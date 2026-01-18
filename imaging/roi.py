from dataclasses import dataclass

@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    def right(self):
        return self.x + self.w

    def bottom(self):
        return self.y + self.h
