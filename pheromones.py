import numpy as np
from components import Position
import typing

class PheromoneMap:
    def __init__(self, screen_width, screen_height):
        self.map = np.zeros((screen_width, screen_height), dtype=float)
        self.width = screen_width
        self.height = screen_height
    def fade(self):
        self.map *= .9995

    def splat(self, ant_position: Position, intensity: float):
        cell_x = round(ant_position.x)
        cell_y = round(ant_position.y)

        offset_x = ant_position.x - cell_x
        offset_y = ant_position.y - cell_y

        weights_x = [
            .5 * (.5 - offset_x)**2,
            .75 - offset_x**2,
            .5 * (.5 + offset_x) **2
        ]

        weights_y = [
                .5 * (.5 - offset_y)**2,
                .75 - offset_y**2,
                .5 * (.5 + offset_y) **2
            ]

        interpolation_matrix =[]

        for column in range(3):
            for row in range(3):
                neighbor_x = cell_x + (column - 1)
                neighbor_y = cell_y + (row - 1)

                cell_weight = weights_x[column] * weights_y[row]

                interpolation_matrix.append([neighbor_x, neighbor_y, cell_weight])
       
        for x, y, weight in interpolation_matrix:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.map[x, y] = min(self.map[x, y] + intensity * weight, 1)


        



        







