# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 09:40:12 2026

@author: MosesLee
"""

import pygame
import random
import sys

# Initialize
pygame.init()
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Card Shuffle Animation")
clock = pygame.time.Clock()

WHITE = (245,245,245)
BLACK = (20,20,20)
RED = (200,50,50)
BLUE = (50,100,200)

CARD_W, CARD_H = 60, 90
STACK_X = WIDTH // 2 - CARD_W // 2
STACK_Y = HEIGHT // 2 - CARD_H // 2
font = pygame.font.SysFont(None, 48)
# Card class
class Card:
    def __init__(self, i):
        self.x = STACK_X
        self.y = STACK_Y
        self.target_x = self.x
        self.target_y = self.y
        self.speed = 10
        self.id = i

    def move(self):
        self.x += (self.target_x - self.x) * 0.15
        self.y += (self.target_y - self.y) * 0.15

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, CARD_W, CARD_H), border_radius=6)
        font.render ('jeff', True, BLACK)
        pygame.draw.rect(screen, BLACK, (self.x, self.y, CARD_W, CARD_H), 2, border_radius=6)

# Create deck
deck = [Card(i) for i in range(30)]

state = "stack"
timer = 0

running = True
while running:
    screen.fill((30, 120, 40))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    timer += 1

    # Phase 1: Fan out
    if state == "stack" and timer > 60:
        for i, card in enumerate(deck):
            card.target_x = 200 + i * 15
            card.target_y = HEIGHT//2 - CARD_H//2
        state = "fan"
        timer = 0

    # Phase 2: Split
    if state == "fan" and timer > 90:
        half = len(deck)//2
        for i, card in enumerate(deck):
            if i < half:
                card.target_y = 200
            else:
                card.target_y = 350
        state = "split"
        timer = 0

    # Phase 3: Shuffle (interleave)
    if state == "split" and timer > 90:
        random.shuffle(deck)
        for i, card in enumerate(deck):
            card.target_x = STACK_X
            card.target_y = STACK_Y - i * 0.5
        state = "merge"
        timer = 0

    # Phase 4: Reset
    if state == "merge" and timer > 120:
        state = "stack"
        timer = 0

    # Move & draw cards
    for card in deck:
        card.move()
        card.draw(screen)

    pygame.display.flip()
    clock.tick(60)
