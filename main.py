import pygame
import sys
import esper
from components import Position, Renderable, Food, Ant, Home

from processes import RenderSystem, PathfindingSystem, MovementSystem
import random

from pheromones import PheromoneMap

import time



pygame.init()



esper.create_entity(
    Home(),
    Position(500, 375),
    Renderable((209, 133, 27))
)

def random_food(number_of_food, screen_width, screen_height):
    for i in range(number_of_food):
        random_position = (random.randint(200, screen_width-200), random.randint(200, screen_height-200))
        if (400 < random_position[0] < 600 and 275 < random_position[1] < 475) or (random_position[0] < 100 or random_position[0] > 900 or random_position[1] > 650 or random_position[1] < 100):
            continue
        esper.create_entity(
            Food(),

            Position(random_position[0], random_position[1]),

            Renderable(color=((255,255,255)))
            
            )
def random_ant(number_of_ants, screen_width, screen_height):
    for i in range(number_of_ants):
        esper.create_entity(
            Ant(),

            Position(random.randint(400, 600), random.randint(275, 475)),

            Renderable(color=((222, 58, 13)))
            
            )
        


screen_width = 1000
screen_height = 750

screen = pygame.display.set_mode((screen_width, screen_height))
pheromone_map = PheromoneMap(screen_width=screen_width, screen_height=screen_height)

pygame.display.set_caption("Ant Sim")

clock = pygame.time.Clock()

random_ant(number_of_ants=100, screen_width=screen.get_width(), screen_height=screen.get_height())

random_food(number_of_food=30, screen_width=screen_width, screen_height=screen_height)

render_system = RenderSystem(screen=screen, pheromone_map=pheromone_map)
pathfinding_system = PathfindingSystem(pheromone_map=pheromone_map)
movement_system = MovementSystem(screen_width=screen_width, screen_height=screen_height, pheromone_map=pheromone_map)

pygame.event.set_blocked(pygame.MOUSEMOTION)

start_time = time.time()

duration = 0

while time.time() - start_time < duration:
    pathfinding_system.process()
    movement_system.process()
    pheromone_map.fade()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    screen.fill((128, 111, 62))


    pathfinding_system.process()
    movement_system.process()
    render_system.process()
    pheromone_map.fade()
    
    pygame.display.flip()

    clock.tick(60)

pygame.quit()

sys.exit()