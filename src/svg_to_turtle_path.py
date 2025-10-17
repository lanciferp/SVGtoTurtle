import turtle

import pip
import math

import subprocess
import sys
import os
import numpy as np
# subprocess.check_call([sys.executable, "-m", "pip", "install", "svgpathtools"])

import svgpathtools

def draw_from_paths(t, paths, scaling_factor=1, move_center=False, offset_x=0, offset_y=0, scale=False):

    def goto_wrapper(t, x, y):
        if move_center:
            x = x + offset_x
            y = y - offset_y
        if scale:
            x = x * scaling_factor
            y = y * scaling_factor
        t.goto(x, y)

    # Set up the turtle
    turtle_colors = ["red", "green", "blue", "orange", "purple", "brown", "pink", "cyan"]

    for i in range(len(paths)):
        t_color = turtle_colors[i % len(turtle_colors)]
        t.color(t_color)
        path = paths[i]
        print(path[0].start.real, t_color)
        for segment in path:
            if isinstance(segment, svgpathtools.path.Line):
                t.penup()
                goto_wrapper(t, segment.start.real, segment.start.imag * -1)  # Invert y-axis
                t.pendown()
                goto_wrapper(t, segment.end.real, segment.end.imag * -1)  # Invert y-axis
                t.penup()

            elif isinstance(segment, svgpathtools.path.CubicBezier):
                t.penup()
                t_values = np.linspace(0, 1, num=20).tolist()

                i_numbers = segment.points(t_values)
                x_values = []
                y_values = []

                for number in i_numbers:
                    x_values.append(number.real)
                    y_values.append(number.imag)

                t.penup()
                for x, y in zip(x_values, y_values):
                    y = y.real
                    goto_wrapper(t, x, y * -1)
                    t.pendown()
                t.penup()

if __name__ == '__main__':
    print(os.getcwd())
    svg_path = "./example_images/cat-svgrepo-com.svg"

    if os.path.isfile(svg_path):
        paths, attributes = svgpathtools.svg2paths(svg_path)
    else:
        raise Exception("File not found")
    print(len(paths), "paths found in", svg_path)
    #calculate bounding box
    xmin =math.inf
    xmax =-math.inf
    ymin =math.inf
    ymax =-math.inf

    for path in paths:
        pxmin, pxmax, pymin, pymax = path.bbox()
        if pxmin < xmin:
            xmin = pxmin
        if pxmax > xmax:
            xmax = pxmax
        if pymin < ymin:
            ymin = pymin
        if pymax > ymax:
            ymax = pymax

    #scale svg to fit a specific bounding box
    scale = True
    svg_width = xmax - xmin
    svg_height = ymax - ymin

    svg_center_x = (xmax + xmin) / 2
    svg_center_y = (ymax + ymin) / 2

    print("SVG dimensions:", svg_width, svg_height)
    print("SVG center:", svg_center_x, svg_center_y)
    print("SVG BoundingBox:", xmin, xmax, ymin, ymax)

    desired_width = 400  # in turtle units
    scaling_factor = desired_width / svg_width

    move_center = True
    desired_center_x = 0
    desired_center_y = 0
    offset_x = desired_center_x - svg_center_x
    offset_y = desired_center_y - svg_center_y

    t = turtle.Turtle()
    t.speed(0)  
    turtle.bgcolor("white")
    t.width(2)
    screen = turtle.Screen()
    screen.tracer(0)

    # # draw bounding box
    # t.color("blue")
    # t.penup()
    # goto_wrapper(t, xmin, -ymin)
    # t.pendown()
    # goto_wrapper(t, xmax, -ymin)
    # goto_wrapper(t, xmax, -ymax)
    # goto_wrapper(t, xmin, -ymax)
    # goto_wrapper(t, xmin, -ymin)
    # t.penup()

    draw_from_paths(t, paths, scaling_factor=scaling_factor, move_center=move_center, offset_x=offset_x, offset_y=offset_y, scale=scale)
    turtle.done()