import pygame
import math
import typing
import esper
from components import Position, Renderable, Transform, Food, Ant, HasFood, Home
import random
import numpy as np
from pheromones import PheromoneMap

class RenderSystem:
    def __init__(self, screen: pygame.display, pheromone_map: PheromoneMap):
        self.screen = screen
        self.pheromone_map = pheromone_map
        self.font = pygame.font.SysFont("Arial", 30)

        low = np.array((128, 111, 62))
        high = np.array((186, 38, 209))
        levels = np.linspace(0, 1, 256)[:, None]
        colors = (high * levels + low * (1 - levels)).astype(np.uint8)
        self.index_buf = np.empty(pheromone_map.map.shape, dtype=np.uint8)
        self.phero_surface = pygame.Surface(pheromone_map.map.shape, depth=8)
        self.phero_surface.set_palette(colors.tolist())
        self.palette = np.array([screen.map_rgb(c.tolist()) & 0xFFFFFFFF for c in colors], dtype=np.uint32)

    def process(self):

        np.multiply(self.pheromone_map.map, 255, out=self.index_buf, casting='unsafe')
        pygame.surfarray.blit_array(self.phero_surface, self.index_buf)
        self.screen.blit(self.phero_surface, (0, 0))

        for entity, (position, renderable) in esper.get_components(Position, Renderable):
            if esper.has_component(entity, Ant):
                pygame.draw.rect(self.screen, renderable.color ,(position.x - 2, position.y - 2, 4, 4))
            else: pygame.draw.rect(self.screen, renderable.color ,(position.x - 5, position.y - 5, 10, 10))

        for food, (food_tag, position) in esper.get_components(Food, Position):
            counter = self.font.render(str(food_tag.counter), True, (52, 235, 94))
            self.screen.blit(counter, (position.x, position.y - 15))
            
            


class MovementSystem:
    def __init__(self, screen_width, screen_height, pheromone_map: PheromoneMap):
        self.pheromone_map = pheromone_map
        self.screen_width = screen_width
        self.screen_height = screen_height
        
    def process(self):

        
        for ant, (position, transform) in esper.get_components(Position, Transform):
            if transform.wait > 0:
                transform.wait -= 1
                continue

            if random.random() <= .80:
                if esper.has_component(ant, Food):
                    self.pheromone_map.splat(position, 3)
                else: self.pheromone_map.splat(position, .3)
            position.x = max(0, min(position.x + math.cos(transform.angle), self.screen_width))
            
            position.y = max(0, min(position.y + math.sin(transform.angle), self.screen_height))

            transform.magnitude -= 1

            if transform.magnitude <= 0:
                esper.remove_component(ant, Transform)
        

class PathfindingSystem:
    def __init__(self, pheromone_map: PheromoneMap):
        self.max_angle = 5
        self.pheromone_map = pheromone_map

    def zone_sum(self, cx, cy, r):
        w, h = self.pheromone_map.width, self.pheromone_map.height
        x0, x1 = max(cx - r, 0), min(cx + r + 1, w)
        y0, y1 = max(cy - r, 0), min(cy + r + 1, h)
        if x0 >= x1 or y0 >= y1:
            return 0.0
        return self.pheromone_map.map[x0:x1, y0:y1].sum()

    def smell(self, position_x, position_y, ant_angle, zone_angle, zone_size, zone_distance) -> tuple:
        left_zone_center_x = round(position_x + np.cos(ant_angle - zone_angle)*zone_distance)
        left_zone_center_y = round(position_y + np.sin(ant_angle - zone_angle)*zone_distance)

        right_zone_center_x = round(position_x + np.cos(ant_angle + zone_angle)*zone_distance)
        right_zone_center_y = round(position_y + np.sin(ant_angle + zone_angle)*zone_distance)

        left_pheromones = 0
        right_pheromones = 0
        for x in range(left_zone_center_x - zone_size, left_zone_center_x + zone_size + 1):
            for y in range(left_zone_center_y - zone_size, left_zone_center_y + zone_size + 1):
                if 0 <= x < self.pheromone_map.width and 0 <= y < self.pheromone_map.height:
                    left_pheromones += self.pheromone_map.map[x, y]

        for x in range(right_zone_center_x - zone_size, right_zone_center_x + zone_size + 1):
            for y in range(right_zone_center_y - zone_size, right_zone_center_y + zone_size + 1):
                if 0 <= x < self.pheromone_map.width and 0 <= y < self.pheromone_map.height:
                    right_pheromones += self.pheromone_map.map[x, y]
        
        if left_pheromones + right_pheromones == 0:
            return (.5, .5)
        return (left_pheromones/(left_pheromones + right_pheromones), right_pheromones/ (left_pheromones + right_pheromones))
    


    def steer(self, position: Position):

        max_turn = 3

        sensor_distance = 10
        sensor_angle = np.radians(30)
        sensor_radius = 5
        left_pheromones, right_pheromones = self.smell(position.x, position.y, position.angle, sensor_angle, sensor_radius, sensor_distance)

        rand = random.random()

        alpha = 3

        if rand < left_pheromones:
            theta = -max_turn *(((left_pheromones**alpha)-(rand)**alpha/(left_pheromones**alpha)))
        else:
            theta = max_turn*((rand**alpha - (left_pheromones**alpha)/(right_pheromones**alpha)))

        return theta


            
            



    def process(self):

        max_angle = 20

        foods = [(food_tag, food_position) for food_entity, (food_tag, food_position) in esper.get_components(Food, Position)]
        home_entity, (home_tag, home_position) = next(iter(esper.get_components(Home, Position)))

        for ant, (ant_tag, ant_position) in esper.get_components(Ant, Position):

            if esper.has_component(ant, Transform):
                continue

            has_food = esper.has_component(ant, HasFood)

            if not has_food:
                for food_tag, food_position in foods:
                    if math.hypot(food_position.x - ant_position.x, food_position.y - ant_position.y) <= 10:
                        esper.add_component(ant, HasFood())
                        esper.component_for_entity(ant, Renderable).color = (181, 204, 65)
                        ant_position.angle += 180
                        food_tag.counter += 1
                        has_food = True
                        break

            
                    
                        
            home_dx = home_position.x - ant_position.x
            home_dy = home_position.y - ant_position.y

            if has_food and math.hypot(home_dx, home_dy) <= 3:
                esper.remove_component(ant, HasFood)
                esper.component_for_entity(ant, Renderable).color = (222, 58, 13)
                ant_position.angle -= 180
                has_food = False
                

            if has_food:
                home_angle = math.atan2(home_dy, home_dx)
                go_home_angle = (home_angle - ant_position.angle + math.pi) % (2 * math.pi) - math.pi
                ant_position.angle += max(math.radians(-max_angle), min(go_home_angle, math.radians(max_angle)))
                esper.add_component(ant, Transform(angle=ant_position.angle, magnitude=1))
            else:
                go_food_angle = self.steer(ant_position)
                ant_position.angle += max(math.radians(-max_angle), min(math.radians(max_angle), go_food_angle))
                think = random.randint(1, 5)
                esper.add_component(ant, Transform(angle=ant_position.angle, magnitude=think))