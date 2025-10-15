import turtle

import pip
import math
import time

import subprocess
import sys
import os
import numpy as np
from svg_to_turtle_path import draw_from_paths
import  svgpath_utils


import svgpathtools

from sympy import symbols, simplify, Eq, solve, I, expand
t1, t2 = symbols('t1 t2', real=True)

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



def nest_dolls_rec(child, doll_relations):
    g_child_list = []
    for rel in doll_relations:
        if rel[0] == child:
            g_child_list.append(rel[1])
    if len(g_child_list) == 0:
        return child
    else:
        gchildren = []
        for gchild in g_child_list:
            gchildren.append(nest_dolls_rec(gchild, doll_relations))
            return gchildren


def fill_with_diagonal_lines(t, path, spacing=5, scaling_factor=10):
    #calculate bounding box
    xmin, xmax, ymin, ymax = path.bbox()

    #draw diagonal lines from top-left to bottom-right
    x_list = np.linspace(xmin, xmax, num=int((xmax - xmin) / spacing) + 1)

    for x in x_list:
        #find the points that contain this X

        for segment in path:
            seg_xmin, seg_xmax, seg_ymin, seg_ymax = segment.bbox()

            if seg_xmin <= x <= seg_xmax: 
                print(x, svgpath_utils.get_y_from_x_bezier(segment, x))


if __name__ == '__main__':
    svg_path = "./example_images/cat-svgrepo-com.svg"

    if os.path.isfile(svg_path):
        paths, attributes = svgpathtools.svg2paths(svg_path)
    else:
        raise Exception("File not found")
    
    paths, nested_path_rel = create_nesting_dolls(paths)

    #convert paths to list of segments
    segments = []
 
    def paths_to_segments(paths):
        segments = []
        for path in paths:
            for segment in path:
                if isinstance(segment, svgpathtools.Path):
                    segments.append(paths_to_segments(segment))
                    return
                else:
                    segments.append(segment)
        return segments

    segments = paths_to_segments(paths)

    #add some self intersecting segments for testing
    segments.append(svgpathtools.CubicBezier(-1.78+5.76j, 16.04+8.2j, -2.58+0.24j, 4.14+8.67j))
    paths.append(svgpathtools.Path(segments[-1]))
    intersections = []
    
    #seperate paths that intersect from those that don't
    print(len(segments), "segments found in", svg_path)
    # look for intersections in segments
    for segment in segments:
        for segment2 in segments:
            if segment == segment2:
                continue
            intersection = segment.intersect(segment2)
            if intersection:
                intersections.append((segment, segment2, intersection))

    intersection_points_i = set()
    for intersection in intersections:
        seg1, seg2, points = intersection
        #convert to xy
        for point in points:
            seg1_int = seg1.poly()(point[0])
            intersection_points_i.add(seg1_int)

    for segment in segments:
        if isinstance(segment, svgpathtools.CubicBezier):
            solutions = svgpath_utils.optimized_bezier_self_intersect(segment)
            if len(solutions) > 0:
                intersection_points_i.add(solutions[0])

    t = turtle.Turtle()
    t.speed(0)  
    turtle.bgcolor("white")
    t.width(2)
    screen = turtle.Screen()
    screen.tracer(0)
    sf = 10
    draw_from_paths(t, paths, scaling_factor=sf, scale=True)

    #on each intersection point draw a red dot
    print(len(intersection_points_i), "intersection points found")
    t.color("red")
    for point in intersection_points_i:
        x = point.real * sf
        y = point.imag * -sf
        t.penup()
        t.goto(x, y)
        t.pendown()
        t.dot(5, "red")
    

    for path in paths:

        # if the path has no children, and no intersections, fill with diagonal lines
        is_last = True
        for rel in nested_path_rel:
            if rel[1] == path:
                is_last = False
        if is_last:
            is_alone = True
            for path2 in paths:
                if path == path2:
                    continue
                intersections = path.intersect(path2)
                if intersections:
                    is_alone = False

            if is_alone:
                fill_with_diagonal_lines(t, path, spacing=10, scaling_factor=sf)


    turtle.done()
