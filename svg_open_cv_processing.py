import turtle

import pip
import math

import subprocess
import sys
import os
import numpy as np
import cv2

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

def convert_svg_to_png(svg_filepath, png_filepath):
    """
    Converts an SVG file to a PNG file using svglib and ReportLab.

    Args:
        svg_filepath (str): The path to the input SVG file.
        png_filepath (str): The path for the output PNG file.
    """
    drawing = svg2rlg(svg_filepath)
    renderPM.drawToFile(drawing, png_filepath, fmt='PNG')
    print(f"Successfully converted '{svg_filepath}' to '{png_filepath}'")

# Example usage:
if __name__ == '__main__':
    input_svg = "./src/cat-svgrepo-com.svg" # Replace with your SVG file name
    output_png = "output.png" # Replace with your desired PNG file name

    convert_svg_to_png(input_svg, output_png)

    img = cv2.imread('output.png')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, contours, -1, (0, 255, 0), 2)
    cv2.imshow('Contours', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()