from svgpathtools import Path, Line, CubicBezier

import numpy as np

def path1_is_contained_in_path2(path1, path2):
    #assert path2.isclosed()  # This question isn't well-defined otherwise
    if path2.intersect(path1):
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


