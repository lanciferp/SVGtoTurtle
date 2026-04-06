from svgpathtools import Path, Line, CubicBezier

import numpy as np

def path1_is_contained_in_path2(path1, path2):
    #assert path2.isclosed()  # This question isn't well-defined otherwise
    try:
        if path2.intersect(path1):
            return False
    except AssertionError:
        # svgpathtools raises AssertionError when two paths share identical
        # segment objects — treat as intersecting (not contained).
        return False

    # find a point that's definitely outside path2
    xmin, _, _, ymax = path2.bbox()
    b = (xmin + 1) + 1j*(ymax + 1)

    a = path1.start  # pick an arbitrary point in path1
    ab_line = Path(Line(a, b))
    number_of_intersections = len(ab_line.intersect(path2))
    if number_of_intersections % 2:  # if number of intersections is odd
        return True
    else:
        return False


def split_path_at_intersections(path, seg_a, t_a, seg_b, t_b):
    """
    Split a closed path at two points defined by (segment, t) pairs.
    Returns two sub-paths (Path objects) that together partition the original path boundary,
    or (None, None) if either segment is not found in the path.

    Sub-path 1 travels from the split point on seg_a forward to the split point on seg_b.
    Sub-path 2 travels from the split point on seg_b forward (wrapping around) to the split point on seg_a.
    """
    segments = list(path)

    idx_a, idx_b = None, None
    for i, seg in enumerate(segments):
        if seg == seg_a:
            idx_a = i
        if seg == seg_b:
            idx_b = i

    if idx_a is None or idx_b is None:
        return None, None

    # Handle the case where both intersections fall on the same segment
    if idx_a == idx_b:
        t_lo, t_hi = (t_a, t_b) if t_a <= t_b else (t_b, t_a)
        seg_start, seg_mid_and_end = seg_a.split(t_lo)
        # re-parameterise t_hi onto the second piece
        t_hi_reparam = (t_hi - t_lo) / (1.0 - t_lo) if (1.0 - t_lo) > 1e-12 else 0.0
        seg_mid, seg_end = seg_mid_and_end.split(t_hi_reparam)
        sub1_segs = [seg_mid]
        sub2_segs = [seg_end] + segments[idx_a + 1:] + segments[:idx_a] + [seg_start]
        return Path(*sub1_segs), Path(*sub2_segs)

    # Normalize so idx_a comes before idx_b in the path
    if idx_a > idx_b:
        idx_a, idx_b = idx_b, idx_a
        seg_a, seg_b = seg_b, seg_a
        t_a, t_b = t_b, t_a

    seg_a_before, seg_a_after = seg_a.split(t_a)
    seg_b_before, seg_b_after = seg_b.split(t_b)

    # Sub-path 1: seg_a split-point → seg_b split-point (forward)
    sub1_segs = [seg_a_after] + segments[idx_a + 1:idx_b] + [seg_b_before]

    # Sub-path 2: seg_b split-point → seg_a split-point (forward, wrapping around)
    sub2_segs = [seg_b_after] + segments[idx_b + 1:] + segments[:idx_a] + [seg_a_before]

    return Path(*sub1_segs), Path(*sub2_segs)


def get_y_from_x_path(path, x):
    y_values = []
    for segment in path:
        seg_bbox = segment.bbox()
        if not (seg_bbox[0] <= x <= seg_bbox[2]):
            continue

        seg_y_values = get_y_from_x_segment(segment, x)
        y_values.extend(seg_y_values)
    return y_values


def get_y_from_x_segment(segment, x):
    if isinstance(segment, CubicBezier):
        return get_y_from_x_bezier(segment, x)
    elif isinstance(segment, Line):
        return get_y_from_x_line(segment, x)
    else:
        raise ValueError("Segment must be a CubicBezier or Line")


def get_y_from_x_bezier(bezier, x):
    if not isinstance(bezier, CubicBezier):
        raise ValueError("Input must be a CubicBezier segment")
    
    P0, P1, P2, P3 = bezier.start, bezier.control1, bezier.control2, bezier.end

    # Coefficients for the cubic equation Ax^3 + Bx^2 + Cx + D = 0
    A = -P0.real + 3*P1.real - 3*P2.real + P3.real
    B = 3*P0.real - 6*P1.real + 3*P2.real
    C = -3*P0.real + 3*P1.real
    D = P0.real - x

    # Calculate the discriminant
    discriminant = 18*A*B*C*D - 4*B**3*D + B**2*C**2 - 4*A*C**3 - 27*A**2*D**2

    if discriminant < 0:
        return []  # No real roots

    # Use numpy to find the roots of the cubic equation
    coefficients = [A, B, C, D]
    roots = np.roots(coefficients)

    # Filter out the real roots within the range [0, 1]
    real_roots = [root.real for root in roots if np.isreal(root) and 0 <= root.real <= 1]

    # Calculate corresponding y values
    y_values = [bezier.poly()(t).imag for t in real_roots]

    return y_values


def get_y_from_x_line(line, x):
    if not isinstance(line, Line):
        raise ValueError("Input must be a Line segment")
    
    x0, y0 = line.start.real, line.start.imag
    x1, y1 = line.end.real, line.end.imag

    if x0 == x1:  # vertical line
        if x == x0:
            return [y0, y1]  # return both y values
        else:
            return []  # no intersection

    if (x < min(x0, x1)) or (x > max(x0, x1)):
        return []  # x is out of bounds of the line segment

    # Calculate the corresponding y value using linear interpolation
    t = (x - x0) / (x1 - x0)
    y = y0 + t * (y1 - y0)

    return [y]


def optimized_bezier_self_intersect(segment):
    if not isinstance(segment, CubicBezier):
        return []
    
    P0, P1, P2, P3 = segment.start, segment.control1, segment.control2, segment.end

    vx, vy, vz  = P2 - P1, P1 - P0, P3 - P0

    try:
        x,y = np.linalg.solve([[vx.real, vy.real],
                              [vx.imag, vy.imag, ]], [vz.real, vz.imag])
    except np.linalg.LinAlgError:
        return []
    
    if x > 1 or \
           4 * y > (x + 1) * (3 - x) or \
           x > 0 and 2 * y + x < np.sqrt(3 * x * (4 - x)) or \
           3 * y < x * (3 - x):
            return []
    rs = (x - 3) / (x + y - 3)
    rp = rs * rs + 3 / (x + y - 3)
    x1 = (rs - np.sqrt(rs * rs - 4 * rp)) / 2
    results = sorted([x1, rp / x1])

    if len(results) > 0:
        p=CubicBezier(P0, P1, P2, P3).poly()
        solutions = []
        for res in results:
            x = p(res).real
            y = p(res).imag
            solutions.append(complex(x,y))
        return solutions
    return []
