# -*- coding: utf-8 -*-
import pygame
import random
import gameclasses

pygame.init()

width, height = 1200, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pandemic Board Game")

board = pygame.image.load("PandemicGameBoard.jpg")
board = pygame.transform.scale(board, (width, height))

running = True
clock = pygame.time.Clock()


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.blit(board, (0, 0))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()