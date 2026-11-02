from dataclasses import dataclass



@dataclass
class Position:
    x: float
    y: float
    angle: float = 0

@dataclass
class Renderable:
    color: tuple = (0,0,0)



@dataclass
class Transform:
    dx: float = 0
    dy: float = 0
    angle: float = 0
    magnitude: float = 0
    wait: int = 0

@dataclass
class Home:
    pass

@dataclass
class Ant:
    pass

@dataclass
class Food:
    counter: int = 0

@dataclass
class HasFood:
    pass


