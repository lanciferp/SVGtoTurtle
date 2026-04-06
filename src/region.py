import numpy as np
import svgpathtools
import svgpath_utils


def _sample_path_points(path, samples_per_segment=30):
    pts = []
    for seg in path:
        start = 0 if not pts else 1
        for tv in np.linspace(0, 1, samples_per_segment)[start:]:
            pts.append(seg.point(float(tv)))
    return pts


def _perp_offset(pts, i, half_w):
    n = len(pts)
    if i == 0:
        tangent = pts[1] - pts[0]
    elif i == n - 1:
        tangent = pts[-1] - pts[-2]
    else:
        tangent = pts[i + 1] - pts[i - 1]
    length = abs(tangent)
    if length < 1e-10:
        return 0j
    return complex(-tangent.imag, tangent.real) / length * half_w


def _draw_stroke_polygon(t, path, sf, color, stroke_width, x_offset=0):
    """Render a path as a filled polygon with flat (butt) line caps."""
    pts = _sample_path_points(path, samples_per_segment=30)
    if len(pts) < 2:
        return
    half_w = stroke_width / 2
    left  = [pts[i] + _perp_offset(pts, i,  half_w) for i in range(len(pts))]
    right = [pts[i] + _perp_offset(pts, i, -half_w) for i in range(len(pts))]
    polygon = left + right[::-1]

    t.pencolor(color)
    t.fillcolor(color)
    t.pensize(1)
    t.penup()
    t.goto(polygon[0].real * sf + x_offset, polygon[0].imag * -sf)
    t.pendown()
    t.begin_fill()
    for pt in polygon[1:]:
        t.goto(pt.real * sf + x_offset, pt.imag * -sf)
    t.goto(polygon[0].real * sf + x_offset, polygon[0].imag * -sf)
    t.end_fill()
    t.penup()


def create_nesting_dolls(paths):
    russian_doll_rel = set()
    #check if paths are in other paths
    for path in paths:
        for path2 in paths:
            if path == path2:
                continue
            if svgpath_utils.path1_is_contained_in_path2(path, path2):
                russian_doll_rel.add((path, path2))

    print(len(russian_doll_rel), "paths are contained in other paths")


    if len(russian_doll_rel) == 0:
            # if there are none, try with continous subpaths
        cont_subpaths = []
        for path in paths:
            path_subpaths = path.continuous_subpaths()
            cont_subpaths.extend(path_subpaths)

        for cont_path1 in cont_subpaths:
            for cont_path2 in cont_subpaths:
                if cont_path1 == cont_path2:
                    continue
                if svgpath_utils.path1_is_contained_in_path2(cont_path1, cont_path2):
                    russian_doll_rel.add((cont_path1, cont_path2))

    print(len(russian_doll_rel), "continuous subpaths are contained in other paths")

    dolls = set()
    for rel in russian_doll_rel:
        dolls.add(rel[0])
        dolls.add(rel[1])

    print(len(dolls), "unique paths found that are part of nesting dolls")

    return list(dolls), russian_doll_rel


def sort_paths_outer_first(paths, nested_path_rel, overlapping_pairs=None):
    """
    Sort paths so that outer (containing) paths come before inner (contained)
    paths. Within the same nesting depth, open stroke paths are drawn before
    closed paths they overlap with (so closed shapes like circles render on top).
    """
    overlapping_pairs = overlapping_pairs or set()
    depth = {id(p): 0 for p in paths}
    for child, _ in nested_path_rel:
        if id(child) in depth:
            depth[id(child)] += 1

    # A closed path that overlaps an open path must be drawn after it.
    # Assign a secondary "on_top" flag: 1 = draw after overlapping open paths.
    on_top = set()
    for pid_open, pid_closed in overlapping_pairs:
        on_top.add(pid_closed)

    def sort_key(p):
        d = depth.get(id(p), 0)
        # 0 = draw earlier (open stroke paths), 1 = draw later (circles on top)
        top = 1 if id(p) in on_top else 0
        return (d, top)

    return sorted(paths, key=sort_key)


def draw_path(t, path, sf, pen_color, fill_color, stroke_width=1, x_offset=0):
    """
    Draw a single svgpathtools.Path.
    Closed paths are drawn with a filled interior.
    Open paths with stroke_width > 1 are expanded into a filled polygon with
    flat (butt) line caps to match browser SVG rendering.
    Open paths with stroke_width <= 1 fall back to turtle pensize.
    """
    closed = abs(path.start - path.end) < 1e-4

    effective_pen = pen_color if pen_color is not None else (fill_color or "white")

    # Open path with thick stroke → expand to filled polygon (flat caps)
    if not closed and stroke_width > 1 and effective_pen is not None:
        _draw_stroke_polygon(t, path, sf, effective_pen, stroke_width, x_offset)
        return

    t.pensize(max(1, round(stroke_width * sf)))
    t.pencolor(effective_pen)

    do_fill = closed and fill_color is not None
    first = True
    if do_fill:
        t.fillcolor(fill_color)
        t.begin_fill()

    for segment in path:
        if isinstance(segment, svgpathtools.Line):
            if first:
                t.penup()
                t.goto(segment.start.real * sf + x_offset, segment.start.imag * -sf)
                t.pendown()
                first = False
            t.goto(segment.end.real * sf + x_offset, segment.end.imag * -sf)
        elif isinstance(segment, (svgpathtools.CubicBezier, svgpathtools.QuadraticBezier, svgpathtools.Arc)):
            t_vals = np.linspace(0, 1, num=20)
            if first:
                pt = segment.point(0)
                t.penup()
                t.goto(pt.real * sf + x_offset, pt.imag * -sf)
                t.pendown()
                first = False
            for tv in t_vals[1:]:
                pt = segment.point(tv)
                t.goto(pt.real * sf + x_offset, pt.imag * -sf)

    if do_fill:
        t.end_fill()
    t.penup()
