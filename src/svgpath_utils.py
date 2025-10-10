from svgpathtools import Path, Line, CubicBezier

from sympy import symbols, simplify, Eq, solve, I, expand
t1, t2 = symbols('t1 t2', real=True)

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
    
def bezier_complex(P0, P1, P2, P3, t):
    """Return cubic Bézier expression in complex form at parameter t"""
    return (
        (1 - t)**3 * P0 +
        3 * (1 - t)**2 * t * P1 +
        3 * (1 - t) * t**2 * P2 +
        t**3 * P3
    )

def solve_bezier_self_intersection_complex(P0, P1, P2, P3):
    # Define symbolic Bézier curve points
    B1 = expand(bezier_complex(P0, P1, P2, P3, t1))
    B2 = expand(bezier_complex(P0, P1, P2, P3, t2))

    # Equation: B(t1) == B(t2)
    diff = simplify(B1 - B2)

    # Separate real and imaginary parts (x and y components)
    eq_real = Eq(diff.as_real_imag()[0], 0)
    eq_imag = Eq(diff.as_real_imag()[1], 0)

    # Solve the system
    sol = solve((eq_real, eq_imag), (t1, t2), dict=True)

    # Filter valid solutions: t1 ≠ t2 and both in (0, 1)
    valid = []
    for s in sol:
        if t1 in s and t2 in s:
            try:
                t1f = float(s[t1].evalf())
                t2f = float(s[t2].evalf())
                if 0 < t1f < 1 and 0 < t2f < 1 and abs(t1f - t2f) > 1e-6:
                    valid.append((t1f, t2f))
            except (TypeError, ValueError):
                continue
    
    p=CubicBezier(P0, P1, P2, P3).poly()
    x = p(valid[0][0]).real
    y = p(valid[0][1]).imag * -1
    return x,y
