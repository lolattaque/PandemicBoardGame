# -*- coding: utf-8 -*-
import pygame
import random
from players import Player
from cities import City, city_list

pygame.init()

city_objects = {}
for name, data in city_list.items():
    city_objects[name] = City(
        name=name,
        connections=data["connections"],
        colour=data["colour"],
        location=data["location"]
    )

largefont = pygame.font.SysFont("arial", 60)
smallfont = pygame.font.SysFont("arial", 40)  

width, height = 1400, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pandemic Board Game")

board = pygame.image.load("PandemicGameBoard.jpg")
board = pygame.transform.scale(board, (width-200, height))

player_options = [2, 3, 4]
selected_index = 0
num_players = player_options[selected_index]

def loading_screen():
    global selected_index
    screen.fill((0,0,0))

    title_surface = largefont.render("PANDEMIC", True, (255, 255, 255))
    title_rect = title_surface.get_rect(center=(width/2, height/5))
    screen.blit(title_surface, title_rect)

    radius = 100
    circles = [
        (width//5, int(height/1.5), radius, 2),
        (width//2, int(height/1.5), radius, 3),
        (width - width//5, int(height/1.5), radius, 4)
    ]

    for i, (x, y, r, n) in enumerate(circles):
        if i == selected_index:
            pygame.draw.circle(screen, (155, 155, 0), (x, y), r)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), r, 3)

        number_surface = largefont.render(str(n), True, (255, 255, 255))
        number_rect = number_surface.get_rect(center=(x, y))
        screen.blit(number_surface, number_rect)

    mouse_pressed = pygame.mouse.get_pressed()
    if mouse_pressed[0]:
        mouse_pos = pygame.mouse.get_pos()
        for i, (x, y, r, n) in enumerate(circles):
            dx = mouse_pos[0] - x
            dy = mouse_pos[1] - y
            if dx*dx + dy*dy <= r*r:
                selected_index = i
                break

def handle_mouse_click():
    mouse_pressed = pygame.mouse.get_pressed()
    if mouse_pressed[0]:
        mouse_pos = pygame.mouse.get_pos()
        print("Mouse clicked at:", mouse_pos)

def draw_cities():
    for city in city_objects.values():
        x, y = city.location
        color = (0, 0, 255)
        if city.colour == "Yellow":
            color = (255, 255, 0)
        elif city.colour == "Black":
            color = (0, 0, 0)
        elif city.colour == "Red":
            color = (255, 0, 0)
        pygame.draw.circle(screen, color, (x, y), 10)

running = True
clock = pygame.time.Clock()
game_state = [1,0,0,0]

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Handle arrow keys ---
        elif event.type == pygame.KEYDOWN and game_state[0] == 1:
            if event.key == pygame.K_RETURN:
                game_state[0] = 0 

    if game_state[0] == 1:
        loading_screen()
    else:
        screen.fill((0,0,0))
        screen.blit(board, (0, 0))
        draw_cities()
        handle_mouse_click()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
