from __future__ import annotations

import svgpathtools
import svgpath_utils


class SegmentIntersection():
    def __init__(self, self_segment, self_ts, int_segment, int_ts):
        self.self_segment = self_segment
        self.self_ts = self_ts
        self.int_segment = int_segment
        self.int_ts = int_ts


class DollIntersection():
    def __init__(self, int_doll, intersections: list[SegmentIntersection]):
        self.int_doll = int_doll
        self.intersections = intersections


class Doll():

    def __init__(self, path: svgpathtools.Path):
        self.path = path
        self.children: list[Doll] = []
        self.doll_intersections: list[DollIntersection] = []

    def add_segment(self, segment: svgpathtools.Line | svgpathtools.CubicBezier):
        self.path.append(segment)

    def get_bounding_box(self):
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for segment in self.path:
            bbox = segment.bbox()
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])
        return (min_x, min_y, max_x, max_y)

    def add_child(self, child_doll: 'Doll'):
        self.children.append(child_doll)

    def add_doll_intersection(self, intersection: DollIntersection):
        self.doll_intersections.append(intersection)

    def get_regions(self):
        regions = []

        if not self.doll_intersections and not self.children:
            regions.append(Region(self.path))
            return regions

        if not self.doll_intersections:
            childpaths = [child.path for child in self.children]
            regions.append(OuterRegion(self.path, childpaths))
            return regions

        total_intersections = sum(len(di.intersections) for di in self.doll_intersections)

        if total_intersections == 1:
            if self.children:
                childpaths = [child.path for child in self.children]
                regions.append(OuterRegion(self.path, childpaths))
            else:
                regions.append(Region(self.path))
            return regions

        for doll_intersection in self.doll_intersections:
            if len(doll_intersection.intersections) <= 1:
                regions.append(Region(self.path))
                continue

            ints = doll_intersection.intersections
            for i in range(0, len(ints) - 1, 2):
                int_a = ints[i]
                int_b = ints[i + 1]

                sub_path_a, sub_path_b = svgpath_utils.split_path_at_intersections(
                    self.path,
                    int_a.self_segment, int_a.self_ts[0],
                    int_b.self_segment, int_b.self_ts[0],
                )

                if sub_path_a is None or sub_path_b is None:
                    regions.append(Region(self.path))
                    continue

                sub_doll_a = Doll(sub_path_a)
                sub_doll_b = Doll(sub_path_b)

                for child in self.children:
                    if child.doll_intersections and any(
                        ci.int_doll == doll_intersection.int_doll
                        for ci in child.doll_intersections
                    ):
                        # Child also intersects the bisecting doll — complex case,
                        # fall back to containment check for now.
                        pass

                    if svgpath_utils.path1_is_contained_in_path2(child.path, sub_path_a):
                        sub_doll_a.add_child(child)
                    else:
                        sub_doll_b.add_child(child)

                regions.extend(sub_doll_a.get_regions())
                regions.extend(sub_doll_b.get_regions())

        return regions


class Region():
    def __init__(self, segments):
        self.segments = segments


class OuterRegion(Region):
    def __init__(self, path, inner_paths):
        super().__init__(path)
        self.inner_paths = inner_paths
