import turtle
import os
import xml.etree.ElementTree as ET
import svgpathtools
import svgpath_utils

from region import create_nesting_dolls, sort_paths_outer_first, draw_path

SVG_DIR = os.path.join(os.path.dirname(__file__), "..", "example_images")
SVG_FILES = [
    #"cat-svgrepo-com.svg",
    "rooster-svgrepo-com.svg",
    "osa.svg",
    "rails.svg",
    #"python.svg",
]

pen_colors  = ["#8B0000", "#00008B", "#006400", "#8B4500", "#4B0082",
               "#8B6914", "#005F5F", "#6B006B", "#3B3B00", "#00456B"]
fill_colors = ["#FFB3B3", "#B3B3FF", "#B3FFB3", "#FFD9B3", "#D9B3FF",
               "#FFF0B3", "#B3FFFF", "#FFB3FF", "#FFFFB3", "#B3DFFF"]

# Presentation attributes that can be inherited from parent elements
_INHERITED_ATTRS = ('fill', 'stroke', 'stroke-width', 'opacity',
                    'fill-opacity', 'stroke-opacity')
_SHAPE_TAGS = {'path', 'circle', 'ellipse', 'rect',
               'line', 'polyline', 'polygon'}


def _parse_inherited_attrs(svg_file):
    """
    Walk the SVG XML tree in document order and return one attribute dict per
    shape element, with group-level presentation attributes propagated to
    children (same cascade rules as a browser).
    Order matches svgpathtools.svg2paths output.
    """
    tree = ET.parse(svg_file)
    root = tree.getroot()
    strip_ns = lambda tag: tag.split('}')[-1]

    results = []

    def walk(el, inherited):
        combined = dict(inherited)
        # Inherit presentation attributes from element
        for attr in _INHERITED_ATTRS:
            v = el.get(attr)
            if v is not None:
                combined[attr] = v
        # Also parse inline style="..." overrides
        for item in el.get('style', '').split(';'):
            if ':' in item:
                k, v = item.split(':', 1)
                combined[k.strip()] = v.strip()

        if strip_ns(el.tag) in _SHAPE_TAGS:
            results.append(dict(combined))

        for child in el:
            walk(child, combined)

    walk(root, {})
    return results


def process_svg(svg_path):
    """
    Load an SVG, detect nesting, find segment intersections.
    Returns (ordered_paths, attrs_by_path, intersection_points, svg_bbox).
    svg_bbox is (xmin, xmax, ymin, ymax) in SVG coordinates.
    """
    if not os.path.isfile(svg_path):
        raise FileNotFoundError(f"SVG not found: {svg_path}")

    paths, svgpt_attrs = svgpathtools.svg2paths(svg_path)
    inherited     = _parse_inherited_attrs(svg_path)
    print(f"\n--- {os.path.basename(svg_path)} ---")

    # Merge inherited group styles with per-element attrs.
    # Per-element attributes win; inherited fill in the gaps.
    merged_attrs = []
    for path_attr, inh in zip(svgpt_attrs, inherited):
        merged = dict(inh)
        for k, v in path_attr.items():
            if v:          # svgpathtools sometimes returns empty strings
                merged[k] = v
        merged_attrs.append(merged)

    # Split compound paths (multiple M commands) into continuous subpaths,
    # each inheriting its parent's merged attributes.
    expanded_paths = []
    attrs_by_path  = {}
    for path, attr in zip(paths, merged_attrs):
        for subpath in path.continuous_subpaths():
            expanded_paths.append(subpath)
            attrs_by_path[id(subpath)] = attr
    paths = expanded_paths
    print(f"{len(paths)} subpaths after expansion")

    nested_paths, nested_path_rel = create_nesting_dolls(paths)

    # Re-add any subpaths dropped by create_nesting_dolls (standalone, non-nested)
    nested_ids = {id(p) for p in nested_paths}
    paths = nested_paths + [p for p in paths if id(p) not in nested_ids]

    # Only check segments across DIFFERENT paths; skip endpoint touches (t near 0/1)
    EPS = 1e-4
    intersection_points = set()
    # Track which path pairs geometrically overlap (boundary crosses OR endpoint inside)
    overlapping_pairs = set()   # set of (id(open_path), id(closed_path))
    print(sum(len(p) for p in paths), "segments found")

    for i, path_a in enumerate(paths):
        for j, path_b in enumerate(paths):
            if j <= i:
                continue
            has_intersection = False
            for seg_a in path_a:
                for seg_b in path_b:
                    try:
                        pts = seg_a.intersect(seg_b)
                    except Exception:
                        continue
                    for t_a, t_b in pts:
                        if (t_a < EPS or t_a > 1 - EPS or
                                t_b < EPS or t_b > 1 - EPS):
                            continue
                        intersection_points.add(seg_a.point(t_a))
                        has_intersection = True

            if has_intersection:
                overlapping_pairs.add((id(path_a), id(path_b)))

    # Also catch open paths whose endpoints land inside a closed path
    # (line terminates inside a circle — boundaries don't cross, but they visually overlap)
    closed_paths = [p for p in paths if abs(p.start - p.end) < 1e-4]
    open_paths   = [p for p in paths if abs(p.start - p.end) >= 1e-4]
    for op in open_paths:
        for cp in closed_paths:
            if (id(op), id(cp)) in overlapping_pairs or (id(cp), id(op)) in overlapping_pairs:
                continue
            if (svgpath_utils.path1_is_contained_in_path2(
                    svgpathtools.Path(svgpathtools.Line(op.start, op.start + 1e-6)), cp) or
                    svgpath_utils.path1_is_contained_in_path2(
                    svgpathtools.Path(svgpathtools.Line(op.end, op.end + 1e-6)), cp)):
                overlapping_pairs.add((id(op), id(cp)))

    for path in paths:
        for segment in path:
            if isinstance(segment, svgpathtools.CubicBezier):
                solutions = svgpath_utils.optimized_bezier_self_intersect(segment)
                if solutions:
                    intersection_points.add(solutions[0])

    print(len(intersection_points), "intersection points found")

    ordered_paths = sort_paths_outer_first(paths, nested_path_rel, overlapping_pairs)

    bboxes = [p.bbox() for p in paths if len(p) > 0]
    xmin = min(b[0] for b in bboxes)
    xmax = max(b[1] for b in bboxes)
    ymin = min(b[2] for b in bboxes)
    ymax = max(b[3] for b in bboxes)

    return ordered_paths, attrs_by_path, intersection_points, (xmin, xmax, ymin, ymax)


def _resolve_color(attrs, key, fallback):
    """
    Return the colour value for `key`:
      - explicit 'none'  → None  (caller should skip fill/stroke)
      - value present    → that value
      - not set          → fallback palette colour
    """
    if key not in attrs:
        return fallback
    val = attrs[key].strip()
    if val.lower() == 'none':
        return None   # explicitly disabled
    return val if val else fallback


def draw_svg(t, ordered_paths, attrs_by_path, intersection_points, sf, x_offset=0):
    """Draw one SVG's paths and intersection dots, shifted by x_offset turtle units."""
    for i, path in enumerate(ordered_paths):
        a = attrs_by_path.get(id(path), {})
        pen_color  = _resolve_color(a, 'stroke', pen_colors[i % len(pen_colors)])
        fill_color = _resolve_color(a, 'fill',   fill_colors[i % len(fill_colors)])
        try:
            stroke_width = float(a.get('stroke-width', 1))
        except (TypeError, ValueError):
            stroke_width = 1

        draw_path(t, path, sf,
                  pen_color=pen_color,
                  fill_color=fill_color,
                  stroke_width=stroke_width,
                  x_offset=x_offset)

    t.pencolor("red")
    t.pensize(1)
    for point in intersection_points:
        x = point.real * sf + x_offset
        y = point.imag * -sf
        t.penup()
        t.goto(x, y)
        t.pendown()
        t.dot(5, "red")


if __name__ == '__main__':
    TARGET_WIDTH = 400  # turtle units each image is scaled to fit
    padding = 50        # turtle units of gap between images

    results = []
    for filename in SVG_FILES:
        svg_path = os.path.join(SVG_DIR, filename)
        ordered_paths, attrs_by_path, intersection_points, bbox = process_svg(svg_path)
        results.append((ordered_paths, attrs_by_path, intersection_points, bbox))

    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()
    turtle.bgcolor("white")
    screen = turtle.Screen()
    screen.tracer(0)

    x_cursor = 0
    for ordered_paths, attrs_by_path, intersection_points, bbox in results:
        xmin, xmax, ymin, ymax = bbox
        svg_width = xmax - xmin
        sf = TARGET_WIDTH / svg_width if svg_width > 0 else 1.0
        x_offset = x_cursor - xmin * sf

        draw_svg(t, ordered_paths, attrs_by_path, intersection_points, sf, x_offset=x_offset)
        x_cursor += TARGET_WIDTH + padding

    screen.update()
    turtle.done()
