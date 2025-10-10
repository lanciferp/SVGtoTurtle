from svgpathtools import Path, Line

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


if __name__ == '__main__':
    # Test examples
    closed_path = Path(Line(0,5), Line(5,5+5j), Line(5+5j, 0))
    path_that_is_contained = Path(Line(1+1j, 2+2j))
    print(path1_is_contained_in_path2(path_that_is_contained, closed_path))

    path_thats_not_contained = Path(Line(10+10j, 20+20j))
    print(path1_is_contained_in_path2(path_thats_not_contained, closed_path))

    path_that_intersects = Path(Line(2+1j, 10+10j))
    print(path1_is_contained_in_path2(path_that_intersects, closed_path))