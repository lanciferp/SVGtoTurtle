"""
Test script: loads the cat SVG, detects regions using the Doll system,
and draws each region as a filled shape with turtle.
"""

import os
import sys
import math
import turtle
import numpy as np
import svgpathtools

sys.path.insert(0, os.path.dirname(__file__))
import svgpath_utils
from doll import Doll, DollIntersection, SegmentIntersection, Region, OuterRegion

SVG_PATH = os.path.join(os.path.dirname(__file__), "..", "example_images", "cat-svgrepo-com.svg")

FILL_COLORS = [
    "#e8c99f", "#d4a574", "#c4956a", "#8b6355", "#f0d9b5",
    "#a0522d", "#cd853f", "#daa520", "#b8860b", "#8b4513",
    "#ffe4b5", "#ffdead", "#f4a460", "#d2691e", "#a52a2a",
]


# ---------------------------------------------------------------------------
# Step 1 — build Doll objects and nesting hierarchy
# ---------------------------------------------------------------------------

def _bbox_area(path):
    xmin, xmax, ymin, ymax = path.bbox()
    return (xmax - xmin) * (ymax - ymin)


def build_doll_hierarchy(paths):
    """
    Create Doll objects for every path and wire up direct parent→child
    relationships (each child is assigned to its smallest enclosing parent).

    Returns:
        top_dolls  – list of Doll objects that are not children of anything
        all_dolls  – list of all Doll objects (in the same order as `paths`)
    """
    dolls = [Doll(p) for p in paths]
    path_to_doll = {id(p): d for p, d in zip(paths, dolls)}

    # For each path find every path that contains it, then pick the smallest.
    for i, child_path in enumerate(paths):
        containers = []
        for j, parent_path in enumerate(paths):
            if i == j:
                continue
            try:
                if svgpath_utils.path1_is_contained_in_path2(child_path, parent_path):
                    containers.append(parent_path)
            except Exception:
                pass  # malformed / open paths — skip

        if containers:
            # Direct parent = smallest enclosing path
            direct_parent = min(containers, key=_bbox_area)
            path_to_doll[id(direct_parent)].add_child(dolls[i])

    child_ids = set()
    for doll in dolls:
        if hasattr(doll, 'children'):
            for child in doll.children:
                child_ids.add(id(child))

    top_dolls = [d for d in dolls if id(d) not in child_ids]
    return top_dolls, dolls


# ---------------------------------------------------------------------------
# Step 2 — find intersections between dolls
# ---------------------------------------------------------------------------

def register_intersections(all_dolls):
    """
    For every pair of dolls that share no parent/child relationship, find
    segment-level intersections and register them on both dolls.
    """
    # Build a set of (parent_id, child_id) pairs so we can skip nested pairs.
    nested_pairs = set()
    for doll in all_dolls:
        if hasattr(doll, 'children'):
            for child in doll.children:
                nested_pairs.add((id(doll), id(child)))
                nested_pairs.add((id(child), id(doll)))

    for i, doll_a in enumerate(all_dolls):
        for j, doll_b in enumerate(all_dolls):
            if j <= i:
                continue
            if (id(doll_a), id(doll_b)) in nested_pairs:
                continue

            seg_intersections = []
            for seg_a in doll_a.path:
                for seg_b in doll_b.path:
                    try:
                        pts = seg_a.intersect(seg_b)
                    except Exception:
                        continue
                    for t_a, t_b in pts:
                        seg_intersections.append(
                            SegmentIntersection(seg_a, [t_a], seg_b, [t_b])
                        )

            if seg_intersections:
                doll_a.add_doll_intersection(DollIntersection(doll_b, seg_intersections))
                doll_b.add_doll_intersection(DollIntersection(doll_a, seg_intersections))


# ---------------------------------------------------------------------------
# Step 3 — drawing helpers
# ---------------------------------------------------------------------------

def _draw_path_outline(t, path, sf):
    """Trace the outline of a svgpathtools.Path with the turtle."""
    first = True
    for segment in path:
        if isinstance(segment, svgpathtools.Line):
            if first:
                t.penup()
                t.goto(segment.start.real * sf, segment.start.imag * -sf)
                t.pendown()
                first = False
            t.goto(segment.end.real * sf, segment.end.imag * -sf)

        elif isinstance(segment, svgpathtools.CubicBezier):
            t_vals = np.linspace(0, 1, num=20)
            if first:
                pt0 = segment.point(0)
                t.penup()
                t.goto(pt0.real * sf, pt0.imag * -sf)
                t.pendown()
                first = False
            for tv in t_vals[1:]:
                pt = segment.point(tv)
                t.goto(pt.real * sf, pt.imag * -sf)


def draw_region(t, region, sf, fill_color, border_color="black"):
    """Draw a Region or OuterRegion as a filled polygon."""
    path = region.segments  # Region stores the Path in .segments

    t.pencolor(border_color)
    t.fillcolor(fill_color)
    t.penup()
    t.begin_fill()
    _draw_path_outline(t, path, sf)
    t.end_fill()
    t.penup()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    svg_path = os.path.normpath(SVG_PATH)
    if not os.path.isfile(svg_path):
        raise FileNotFoundError(f"SVG not found: {svg_path}")

    paths, _ = svgpathtools.svg2paths(svg_path)
    print(f"Loaded {len(paths)} paths from {os.path.basename(svg_path)}")

    # Compute scaling factor to fit the image into ~400 turtle units wide
    all_bbox = [p.bbox() for p in paths if len(p) > 0]
    if all_bbox:
        xmin = min(b[0] for b in all_bbox)
        xmax = max(b[1] for b in all_bbox)
        svg_width = xmax - xmin
        sf = 400 / svg_width if svg_width > 0 else 1.0
    else:
        sf = 1.0

    print(f"Scaling factor: {sf:.4f}")

    # Build hierarchy
    top_dolls, all_dolls = build_doll_hierarchy(paths)
    print(f"{len(top_dolls)} top-level dolls, {len(all_dolls)} total")

    # Register intersections
    register_intersections(all_dolls)

    # Collect regions
    all_regions = []
    for doll in top_dolls:
        try:
            regions = doll.get_regions()
            all_regions.extend(regions)
        except Exception as e:
            print(f"  Warning: get_regions() failed for a doll: {e}")

    print(f"{len(all_regions)} regions detected")

    # Set up turtle
    screen = turtle.Screen()
    screen.title("SVG Region Detector — cat")
    screen.bgcolor("white")
    screen.tracer(0)

    t = turtle.Turtle()
    t.speed(0)
    t.width(1)
    t.hideturtle()

    # Draw each region with a distinct fill color
    for i, region in enumerate(all_regions):
        color = FILL_COLORS[i % len(FILL_COLORS)]
        try:
            draw_region(t, region, sf, fill_color=color)
        except Exception as e:
            print(f"  Warning: failed to draw region {i}: {e}")

    screen.update()
    print("Done — close the turtle window to exit.")
    turtle.done()


if __name__ == "__main__":
    main()
