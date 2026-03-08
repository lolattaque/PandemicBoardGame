import random
from players import quarantine_protects, COLOUR_INDEX

class Board:
    def __init__(self, city_objects, difficulty):
        self.infection_cards = list(city_objects.keys())
        self.city_cards = list(city_objects.keys())
        self.infection_card_discard_pile = []
        self.outbreak_counter = 0
        self.infection_rate = 2
        self.cures = [False, False, False, False]
        self.eradicated = [False, False, False, False]
        self.player_discard_pile = []
        self.difficulty = int(difficulty) + 4

        self.shuffle_infection_deck()
        random.shuffle(self.city_cards)
        self.outbreak_animations = []

    def add_epidemic_card(self):
        for i in range (self.difficulty):
            self.city_cards.append("Infection Card")
        random.shuffle(self.city_cards)

    def shuffle_infection_deck(self):
        self.infection_cards.extend(self.infection_card_discard_pile)
        self.infection_card_discard_pile = []
        random.shuffle(self.infection_cards)

    def draw_infection_card(self):
        card = self.infection_cards.pop()
        self.infection_card_discard_pile.append(card)
        return card
    
    def draw_city_card(self):
        card = self.infection_cards.pop()
        self.player_discard_pile.append(card)
        return card
        
    def set_board(self, city_objects):
        for i in range (3):
            cubes = 3 - i
            for city in range (3):
                city_name = self.draw_infection_card()
                city_obj = city_objects[city_name]
                idx = COLOUR_INDEX.get(city_obj.colour, 0)
                city_obj.virus[idx] = cubes
                
    def infect_virus(self, city_objects, players=None):
        for i in range(self.infection_rate):
            city_name = self.draw_infection_card()
            city = city_objects[city_name]
            if players and quarantine_protects(city_name, players, city_objects):
                continue
            idx = COLOUR_INDEX.get(city.colour, 0)
            city.virus[idx] += 1
            if city.virus[idx] >= 4:
                city.outbreak(city_objects, self, players, source_idx=idx)

def draw_board(screen, board, city_objects, width, height, largeGunfont, smallGunfont, tinyGunfont, cityfont, get_colour_fn):
    import pygame
    header_surface = largeGunfont.render("PANDEMIC", True, (255, 255, 255))
    screen.blit(header_surface, header_surface.get_rect(center=(250, 80)))

    cure_center = 483
    screen.blit(smallGunfont.render("Cures", True, (255,255,255)), smallGunfont.render("Cures", True, (255,255,255)).get_rect(center=(cure_center, height-100)))

    cures_data = [
        ("Blue", 0, (cure_center-90, height-50)),
        ("Yellow", 1, (cure_center-30, height-50)),
        ("Black", 2, (cure_center+30, height-50)),
        ("Red", 3, (cure_center+90, height-50)),
    ]
    for colour_name, idx, pos in cures_data:
        colour_rgb = get_colour_fn(colour_name)
        if board.cures[idx]:
            fill, border = (0, 120, 0), (0, 200, 0)
        else:
            fill, border = (30, 30, 30), (200, 0, 0)
        pygame.draw.circle(screen, fill, pos, 20)
        pygame.draw.circle(screen, border, pos, 20, 4)
        pygame.draw.circle(screen, colour_rgb, pos, 13)
        on_board = sum(city_objects[n].virus[idx] for n in city_objects)
        cube_surf = cityfont.render(str(24 - on_board), True, (200, 200, 200))
        screen.blit(cube_surf, cube_surf.get_rect(center=pos))

    outbreak_center = (100, height - 200)
    size = 22
    diamond_points = [
        (outbreak_center[0], outbreak_center[1] - size),
        (outbreak_center[0] + size, outbreak_center[1]),
        (outbreak_center[0], outbreak_center[1] + size),
        (outbreak_center[0] - size, outbreak_center[1]),
    ]
    outbreak_label = tinyGunfont.render("Outbreaks", True, (255, 255, 255))
    screen.blit(outbreak_label, outbreak_label.get_rect(center=(outbreak_center[0], outbreak_center[1]-40)))
    pygame.draw.polygon(screen, (0, 140, 0), diamond_points)
    pygame.draw.polygon(screen, (0, 255, 0), diamond_points, 4)
    outbreak_text = tinyGunfont.render(str(board.outbreak_counter), True, (255, 255, 255))
    screen.blit(outbreak_text, outbreak_text.get_rect(center=(outbreak_center[0]+1, outbreak_center[1]+1)))

    infection_center = (100, height - 100)
    infection_label = tinyGunfont.render("Infection Rate", True, (255, 255, 255))
    screen.blit(infection_label, infection_label.get_rect(center=(infection_center[0], infection_center[1]-40)))
    pygame.draw.circle(screen, (0, 140, 0), infection_center, 22)
    pygame.draw.circle(screen, (0, 255, 0), infection_center, 22, 4)
    infection_text = tinyGunfont.render(str(board.infection_rate), True, (255, 255, 255))
    screen.blit(infection_text, infection_text.get_rect(center=infection_center))

def draw_outbreak_animations(screen, board, city_objects):
    import pygame
    virus_colours = [(80, 130, 255), (230, 210, 40), (180, 180, 180), (240, 60, 60)]
    still_active = []

    for anim in board.outbreak_animations:
        p = anim["progress"]
        colour = virus_colours[anim["colour_idx"]]
        src = city_objects[anim["source"]].location
        alpha = max(0, int(255 * (1.0 - p)))

        for target_name in anim["targets"]:
            if target_name not in city_objects:
                continue
            dst = city_objects[target_name].location
            tx = int(src[0] + (dst[0] - src[0]) * p)
            ty = int(src[1] + (dst[1] - src[1]) * p)

            glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*colour, max(0, alpha//3)), (15, 15), 15)
            screen.blit(glow_surf, (tx-15, ty-15))
            dot_surf = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*colour, alpha), (7, 7), 7)
            screen.blit(dot_surf, (tx-7, ty-7))

        ring_r = int(14 + p * 28)
        ring_surf = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*colour, max(0, alpha//2)), (ring_r+2, ring_r+2), ring_r, 3)
        screen.blit(ring_surf, (src[0]-ring_r-2, src[1]-ring_r-2))

        anim["progress"] += 0.025
        if anim["progress"] < 1.0:
            still_active.append(anim)

    board.outbreak_animations = still_active


def draw_result_screen(screen, board, game_won, lose_reason, result_alpha, width, height, largeGunfont, smallGunfont, tinyGunfont, cityfont):
    import math, pygame
    result_alpha = min(255, result_alpha + 3)
    t = result_alpha / 255.0

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 20, 0, int(220*t)) if game_won else (20, 0, 0, int(220*t)))
    screen.blit(overlay, (0, 0))

    if result_alpha < 30:
        return result_alpha

    cx, cy = width // 2, height // 2
    pulse = abs(math.sin(pygame.time.get_ticks() * 0.002)) * 20

    if game_won:
        glow_col, ring_col = (0, 200, 80), (0, 255, 100)
    else:
        glow_col, ring_col = (200, 30, 30), (255, 60, 60)

    glow_surf = pygame.Surface((500, 500), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*glow_col, 40), (250, 250), int(180 + pulse))
    pygame.draw.circle(glow_surf, (*glow_col, 20), (250, 250), int(220 + pulse))
    screen.blit(glow_surf, (cx-250, cy-250))
    pygame.draw.circle(screen, ring_col, (cx, cy), int(190 + pulse), 3)

    if game_won:
        title_text, title_col = "VICTORY", (80, 255, 140)
        sub_text, sub_col = "ALL DISEASES CURED", (160, 255, 200)
    else:
        title_text, title_col = "DEFEAT", (255, 80, 80)
        sub_text, sub_col = lose_reason, (255, 160, 160)

    screen.blit(largeGunfont.render(title_text, True, title_col),
                largeGunfont.render(title_text, True, title_col).get_rect(center=(cx, cy-60)))
    screen.blit(smallGunfont.render(sub_text, True, sub_col),
                smallGunfont.render(sub_text, True, sub_col).get_rect(center=(cx, cy+20)))

    cures_done = sum(board.cures)
    for offset, text in enumerate([
        f"CURES FOUND: {cures_done} / 4",
        f"OUTBREAKS: {board.outbreak_counter} / 8",
        f"CARDS LEFT: {len(board.city_cards)}",
    ]):
        s = tinyGunfont.render(text, True, (200, 200, 200))
        screen.blit(s, s.get_rect(center=(cx, cy + 80 + offset * 30)))

    prompt = cityfont.render("PRESS R TO PLAY AGAIN  |  ESC TO QUIT", True, (120, 120, 120))
    screen.blit(prompt, prompt.get_rect(center=(cx, cy+195)))

    return result_alpha