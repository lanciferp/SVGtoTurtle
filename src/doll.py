import svgpathtools
import svgpath_utils

class Doll():

    #Intersections are basically just a fancy tuple, with the first element being the intersections doll, and the second being a list of intersection points
    class DollIntersection():
        def __init__(self, doll, points):
            self.int_doll = doll
            self.points = points  # List of intersection points

    def __init__(self, path: svgpathtools.Path):
        self.path = path

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
        if not hasattr(self, 'children'):
            self.children = []
        self.children.append(child_doll)
    
    def add_intersecting_doll(self, intersecting_doll: 'Doll', intersection_points: list[complex]):
        if not hasattr(self, 'intersections'):
            self.intersecting_dolls = []
        doll_int = self.DollIntersection(intersecting_doll, intersection_points)
        self.intersecting_dolls.append(doll_int)
        
    def get_regions(self):
        # Returns a list of paths, each defining a region within the doll
        # Should only be called after intersections and children have been added

        regions = []

        if hasattr(self, 'intersections') :
            #determine if the intersections bisect the doll into multiple regions
                int_doll = self.intersecting_dolls[0].int_doll
                points = self.intersecting_dolls[0].points

                if len(points) == 1:
                    #TODO: add logic to add the part of the doll that is inside the region to the region itself
                    simple_region = Region(self.path._segments)
                    return [simple_region]

                else:
                    # more than one intersection point, we need to check if it is a bisection, or not
                    int_path = int_doll.path

                    #get the section of the path between the two intersection points

                    #if it is within the doll, then we have two regions, so we make temp dolls for each
                    #and recursively solve

                        #if the doll has no children, then it's a simple bisection, adding the relevant intersections to the new dolls

                        #if the doll has children and this intersection doesn't intersect any of them, then it's still a simple bisection
                        #adding the relevant intersections and children to the new dolls

                        #if itersection also intersects children, then we need to solve for the intersections with those children, and use
                        #the subpaths to define the new regions.

                        


                        #if not, then we just have 2 intrustions, and we go to the next intersection
        elif hasattr(self, 'children'):
            #if there are no instersections, but there are children, then we have one outer region, and the children are holes

            if len(self.children()) == 1:
                #simple case, just one child, so we can create the outer region directly
                outer_region = OuterRegion(self.path, [self.children[0].path])
                regions.append(outer_region)
                return regions

            else:
                childpaths = []

                for child1 in self.children:
                    if hasattr(child1, 'intersections'):
                        # child_intersections = child1.intersections
                        # conjoined_path = None
                        # for child2 in self.children:
                        #     if child1 == child2:
                        #         continue
                        #     for intersection in child_intersections:
                        #         if intersection.int_doll == child2:
                        #             #these two children intersect, so we need to solve for the intersections between them

                        #             #we need a nice math way to think about this, probably using ray casting, as the two children aren't necessarily
                        #             #a nice venn diagram, basically we need to look along the segments between each intersection point
                        #             #and find the outermost segments
                        pass
                
                    else:
                        childpaths.append(child1.path)
                            
            #create outer region, listing children as inner paths
            outer_region = OuterRegion(self.path, childpaths)
            return regions.append(outer_region)
        
        if not hasattr(self, 'intersections') and not hasattr(self, 'children'):
            return regions.append(Region(self.path))

class Region():
    def __init__(self, segments):
        self.segments = segments # svgpathtools.Path object

class OuterRegion(Region):
    def __init__(self, path, inner_paths):
        super().__init__(path)
        self.inner_paths = inner_paths  # List of svgpathtools.Path objects that are holes in this region

