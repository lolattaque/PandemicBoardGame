import pygame
import random
import sys

pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("In-Place Card Shuffle")
clock = pygame.time.Clock()

GREEN = (20, 120, 60)
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)

CARD_W, CARD_H = 70, 100
STACK_X = WIDTH//2 - CARD_W//2
STACK_Y = HEIGHT//2 - CARD_H//2
t = 5
class Card:
    def __init__(self, depth):
        self.x = STACK_X
        self.y = STACK_Y
        self.depth = depth
        self.offset_x = 0
        self.offset_y = 0
        self.target_offset_x = 0
        self.target_offset_y = 0

    def update(self):
        self.offset_x += (self.target_offset_x - self.offset_x) * 0.2
        self.offset_y += (self.target_offset_y - self.offset_y) * 0.2

    def draw(self):
        x = self.x + self.offset_x
        y = self.y + self.offset_y - self.depth * 0.4
        pygame.draw.rect(screen, WHITE, (x, y, CARD_W, CARD_H), border_radius=6)
        pygame.draw.rect(screen, BLACK, (x, y, CARD_W, CARD_H), 2, border_radius=6)

# Create deck
deck = [Card(i) for i in range(40)]

shuffle_timer = 0
shuffle_phase = 0


running = True
while running:
    screen.fill(GREEN)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    shuffle_timer += 1

    # Every 2 seconds start a new shuffle
    if shuffle_timer > 120:
        shuffle_timer = 0
        shuffle_phase = 1

    # Phase 1: Cards separate slightly
    if shuffle_phase == 1:
        for c in deck:
            c.target_offset_x = random.randint(-40, 40)
            c.target_offset_y = random.randint(-20, 20)
        shuffle_phase = 2

    # Phase 2: Randomize order
    if shuffle_phase == 2 and shuffle_timer > 50:
        random.shuffle(deck)
        for i, c in enumerate(deck):
            c.depth = i
        if t == 0:
            shuffle_phase = 3
        t -= 1

    # Phase 3: Snap back to stack
    if shuffle_phase == 3 and shuffle_timer > 80:
        for c in deck:
            c.target_offset_x = 0
            c.target_offset_y = 0
        shuffle_phase = 0
        t = 5

    for card in deck:
        card.update()

    for card in deck:
        card.draw()

    pygame.display.flip()
    clock.tick(60)
