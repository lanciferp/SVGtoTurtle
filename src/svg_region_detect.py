import turtle

import pip
import math

import subprocess
import sys
import os
import numpy as np
from svg_to_turtle_path import draw_from_paths
from svgpath_utils import path1_is_contained_in_path2, solve_bezier_self_intersection_complex


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
            if path1_is_contained_in_path2(path, path2):
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
                if path1_is_contained_in_path2(cont_path1, cont_path2):
                    russian_doll_rel.add((cont_path1, cont_path2))

    print(len(russian_doll_rel), "continuous subpaths are contained in other paths")

    dolls = set()
    for rel in russian_doll_rel:
        dolls.add(rel[0])
        dolls.add(rel[1])

    
    print(len(dolls), "unique paths found that are part of nesting dolls")
    # # now nest paths properly
    # nested_dolls = list()
    # for doll in dolls:
    #     is_root = True
    #     children = []
    #     for rel in russian_doll_rel:
    #         if rel[0] == doll:
    #             is_root = False
    #             break
    #         if rel[1] == doll:
    #             children.append(rel[1])

    #     if not is_root:
    #         continue

    #     print("root doll found")
    #     if len(children) == 0:
    #         nested_dolls.append(doll)
        
    #     elif len(children) >= 1:
    #         for child in children:
    #             new_child = nest_dolls_rec(child, russian_doll_rel)
    #             nested_dolls.append([doll, new_child])
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

    # look for continous curves
    for segment in segments:
        seg1_start = segment.start
        seg1_end = segment.end
        for segment2 in segments:
            if segment == segment2:
                continue

            seg2_start = segment2.start
            seg2_end = segment2.end



    t = turtle.Turtle()
    t.speed(0)  
    turtle.bgcolor("white")
    t.width(2)
    screen = turtle.Screen()
    screen.tracer(0)

    draw_from_paths(t, paths, scaling_factor=10, scale=True)

    #on each intersection point draw a red dot
    print(len(intersection_points_i), "intersection points found")
    t.color("red")
    for point in intersection_points_i:
        x = point.real * 10
        y = point.imag * -10
        t.penup()
        t.goto(x, y)
        t.pendown()
        t.dot(5, "red")

    x,y = solve_bezier_self_intersection_complex(-1.78+5.76j, 16.04+8.2j, -2.58+0.24j, 4.14+8.67j)
    t.penup()

    t.goto(x*10, y*10)
    t.pendown()
    t.dot(5, "blue")
    t.penup()
    offset = -25
    
    

    turtle.done()

