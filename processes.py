import pygame
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
        self.palette = np.array([screen.map_rgb(c.tolist()) & 0xFFFFFFFF for c in colors], dtype=np.uint32)

    def process(self):

        index = (self.pheromone_map.map * 255).astype(np.uint8)
        pygame.surfarray.blit_array(self.screen, self.palette[index])

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
            position.x = max(0, min(position.x + np.cos(transform.angle)*1, self.screen_width))
            
            position.y = max(0, min(position.y + np.sin(transform.angle)*1, self.screen_height))

            transform.magnitude -= 1

            if transform.magnitude <= 0:
                esper.remove_component(ant, Transform)
        

class PathfindingSystem:
    def __init__(self, pheromone_map: PheromoneMap):
        self.max_angle = 5
        self.pheromone_map = pheromone_map

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

        for ant, (ant_tag, ant_position) in esper.get_components(Ant, Position):

            if esper.has_component(ant, Transform):
                continue

            for food, (food_tag, food_position) in esper.get_components(Food, Position):


                food_direction_vector = np.asarray((food_position.x, food_position.y)) - np.asarray((ant_position.x, ant_position.y))
                food_direction_vector = food_direction_vector / np.linalg.norm(food_direction_vector)
                
                distance_from_ant_to_food = np.sqrt(((food_position.x - ant_position.x) ** 2) + ((food_position.y - ant_position.y) ** 2))


                if distance_from_ant_to_food <= 10 and not esper.has_component(ant, HasFood):
                    esper.add_component(ant, HasFood())
                    esper.component_for_entity(ant, Renderable).color = (181, 204, 65)
                    ant_position.angle += 180
                    food_tag.counter += 1
                    
                        

            for home, (home_tag, home_position) in esper.get_components(Home, Position):
                home_direction_vector = np.asarray((home_position.x, home_position.y)) - np.asarray((ant_position.x, ant_position.y))

                home_direction_vector = home_direction_vector / np.linalg.norm(home_direction_vector)

                distance_from_ant_to_home = np.sqrt(((home_position.x - ant_position.x) ** 2) + ((home_position.y - ant_position.y) ** 2))

                if distance_from_ant_to_home <= 3 and esper.has_component(ant, HasFood):
                    esper.remove_component(ant, HasFood)
                    esper.component_for_entity(ant, Renderable).color = (222, 58, 13)
                    ant_position.angle -= 180


            if esper.has_component(ant, HasFood) == True:
                home_angle = np.arctan2(home_direction_vector[1], home_direction_vector[0])
                go_home_angle = (home_angle - ant_position.angle + np.pi) % (2 * np.pi) - np.pi

                ant_position.angle += max(np.radians(-max_angle), min(go_home_angle, np.radians(max_angle)))

                esper.add_component(ant, Transform(home_direction_vector[0], home_direction_vector[1], angle=ant_position.angle, magnitude = 1))

            else:
                food_angle = np.arctan2(food_direction_vector[1], food_direction_vector[0])

                go_food_angle = self.steer(ant_position)

                ant_position.angle += max(np.radians(-max_angle), min(np.radians(max_angle), go_food_angle))

                think = random.randint(1,5)

                esper.add_component(ant, Transform(food_direction_vector[0],food_direction_vector[1], angle = ant_position.angle, magnitude = think))

            
            
            

