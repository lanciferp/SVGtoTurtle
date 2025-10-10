class ChipLine():
    
    def __init__(self, start, direction, angle, tool):
        self.start = start
        self.direction = direction
        self.angle = angle
        self.tool = tool


class VGrooveLine():
    def __init__(self, start, end, depth):
        self.start = start
        self.end = end
        self.depth = depth

