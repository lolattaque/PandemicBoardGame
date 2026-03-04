import pygame
import random
import math
from players import Player, Medic, Scientist, Researcher, Operations_Expert, Dispatcher, Quarantine_Specialist, Contingency_Planner
from cities import City, city_list
from board import Board

pygame.init()

largefont = pygame.font.SysFont("arial", 60)
smallfont = pygame.font.SysFont("arial", 40)
cityfont = pygame.font.SysFont("arial", 12, bold=True)

largeGunfont = pygame.font.Font("Gunplay.ttf", 100)
smallGunfont = pygame.font.Font("Gunplay.ttf", 50)
tinyGunfont = pygame.font.Font("Gunplay.ttf", 20)

width, height = 1400, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pandemic Board Game")

board = pygame.image.load("image.png")
board = pygame.transform.scale(board, (width-200, height))

city_objects = {}
for name, data in city_list.items():
    city_objects[name] = City(
        name=name,
        connections=data["connections"],
        colour=data["colour"],
        location=data["location"]
    )
city_objects["Atlanta"].research_center = True

players = []
player_options = [2, 3, 4]
selected_index = 0
selected_difficulty = 0
player_colors = [(255, 255, 255), (0, 255, 0), (255, 165, 0), (255, 0, 255)]
difficulties = ["Easy", "Normal", "Hard"]

role_classes = [
    Medic, 
    Scientist, 
    Researcher, 
    Dispatcher, 
    Contingency_Planner, 
    Operations_Expert, 
    Quarantine_Specialist
]

random.shuffle(role_classes)

def get_colour(colour_str):
    if colour_str == "Blue":
        return (0, 0, 255)
    elif colour_str == "Yellow":
        return (150, 150, 0)
    elif colour_str == "Black":
        return (80, 80, 80)
    elif colour_str == "Red":
        return (255, 0, 0)
    return (255, 255, 255)

ROLE_ACCENT = {
    "Contingency_Planner": (100, 195, 250),
    "Operations_Expert": (170, 225, 105),
    "Dispatcher": (205, 125, 235),
    "Quarantine_Specialist": (50, 130, 58),
    "Medic": (255, 152, 0),
    "Researcher": (230, 185, 125),
    "Scientist": (200, 55, 55),
}
DARK_BG = (26, 32, 44) 
CARD_BG = (40, 52, 70)
TEXT_WHITE = (240, 244, 248)
TEXT_MUTED = (160, 174, 192)

def loading_screen():
    global selected_index, selected_difficulty
    screen.fill((10, 20, 30))

    title_shadow = largeGunfont.render("PANDEMIC", True, (50, 0, 0))
    title_surface = largeGunfont.render("PANDEMIC", True, (200, 0, 0))
    screen.blit(title_shadow, (width/2 - 215, height/5 + 5))
    screen.blit(title_surface, (width/2 - 220, height/5))

    players_text = smallfont.render("SELECT NUMBER OF PLAYERS", True, (180, 180, 180))
    screen.blit(players_text, (width/2 - players_text.get_width()/2, height/2.8))

    radius = 60
    circles = [
        (width//2 - 150, int(height/2+20), radius, 2),
        (width//2, int(height/2+20), radius, 3),
        (width//2 + 150, int(height/2+20), radius, 4)
    ]

    for i, (x, y, r, n) in enumerate(circles):
        color = (255, 200, 0) if i == selected_index else (100, 100, 100)
        thickness = 0 if i == selected_index else 2
        
        pygame.draw.circle(screen, color, (x, y), r + 5, 2)
        pygame.draw.circle(screen, (30, 30, 30), (x, y), r)
        if i == selected_index:
            pygame.draw.circle(screen, (255, 200, 0), (x, y), r, 4)

        number_surface = largefont.render(str(n), True, color)
        number_rect = number_surface.get_rect(center=(x, y))
        screen.blit(number_surface, number_rect)

    diff_text = smallfont.render("SELECT DIFFICULTY", True, (180, 180, 180))
    screen.blit(diff_text, (width/2 - diff_text.get_width()/2, height/1.5))

    difficulties = ["EASY", "NORMAL", "HARD"]
    button_w, button_h = 180, 60
    
    for i, diff in enumerate(difficulties):
        diff_x = width//2 - 300 + i*210
        diff_y = int(height/1.3)
        rect = pygame.Rect(diff_x, diff_y, button_w, button_h)
        
        color = (200, 0, 0) if i == selected_difficulty else (60, 60, 60)
        text_color = (255, 255, 255) if i == selected_difficulty else (150, 150, 150)
        
        pygame.draw.rect(screen, (20, 20, 20), rect)
        pygame.draw.rect(screen, color, rect, 3)
        
        if i == selected_difficulty:
            pygame.draw.rect(screen, (60, 0, 0), rect.inflate(-4, -4))

        diff_surface = smallGunfont.render(diff, True, text_color)
        diff_rect = diff_surface.get_rect(center=rect.center)
        screen.blit(diff_surface, diff_rect)

    mouse_pressed = pygame.mouse.get_pressed()
    if mouse_pressed[0]:
        mouse_pos = pygame.mouse.get_pos()
        for i, (x, y, r, n) in enumerate(circles):
            if ((mouse_pos[0]-x)**2 + (mouse_pos[1]-y)**2)**0.5 <= r:
                selected_index = i
        for i, diff in enumerate(difficulties):
            diff_x = width//2 - 300 + i*210
            rect = pygame.Rect(diff_x, int(height/1.3), button_w, button_h)
            if rect.collidepoint(mouse_pos):
                selected_difficulty = i

    instr_surface = cityfont.render("PRESS ENTER TO START MISSION", True, (100, 100, 100))
    screen.blit(instr_surface, (width/2 - instr_surface.get_width()/2, height - 40))

def draw_connections():
    drawn_connections = set()

    wrap_pairs = {
        ("San Francisco","Tokyo"),
        ("San Francisco","Manila"),
        ("Los Angeles","Sydney"),
        ("Manila","San Francisco")
    }

    for city_name, city in city_objects.items():
        start_pos = city.location
        start_colour = get_colour(city.colour)

        for connection_name in city.connections:
            if connection_name not in city_objects:
                continue

            pair = tuple(sorted((city_name, connection_name)))
            if pair in drawn_connections:
                continue

            target_city = city_objects[connection_name]
            end_pos = target_city.location
            end_colour = get_colour(target_city.colour)

            if pair in wrap_pairs:
                mid_y = (start_pos[1] + end_pos[1]) // 2
                left_exit = (0, mid_y)
                right_exit = (width-200, mid_y)

                if start_pos[0] < end_pos[0]:
                    pygame.draw.line(screen, start_colour, start_pos, left_exit, 3)
                    pygame.draw.line(screen, end_colour, right_exit, end_pos, 3)
                else:
                    pygame.draw.line(screen, start_colour, start_pos, right_exit, 3)
                    pygame.draw.line(screen, end_colour, left_exit, end_pos, 3)
            else:
                mid_x = (start_pos[0] + end_pos[0]) / 2
                mid_y = (start_pos[1] + end_pos[1]) / 2
                mid_pos = (mid_x, mid_y)

                pygame.draw.line(screen, start_colour, start_pos, mid_pos, 3)
                pygame.draw.line(screen, end_colour, mid_pos, end_pos, 3)

            drawn_connections.add(pair)

def draw_outbreak_animations():
    if not hasattr(Pandemic_Game, "outbreak_animations"):
        return

    virus_colours = [(80, 130, 255), (230, 210, 40), (180, 180, 180), (240, 60, 60)]
    still_active = []
    for anim in Pandemic_Game.outbreak_animations:
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
            glow_col = (*colour, max(0, alpha // 3))
            pygame.draw.circle(glow_surf, glow_col, (15, 15), 15)
            screen.blit(glow_surf, (tx - 15, ty - 15))
            dot_surf = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*colour, alpha), (7, 7), 7)
            screen.blit(dot_surf, (tx - 7, ty - 7))
        ring_r = int(14 + p * 28)
        ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
        ring_col = (*colour, max(0, alpha // 2))
        pygame.draw.circle(ring_surf, ring_col, (ring_r + 2, ring_r + 2), ring_r, 3)
        screen.blit(ring_surf, (src[0] - ring_r - 2, src[1] - ring_r - 2))

        anim["progress"] += 0.025
        if anim["progress"] < 1.0:
            still_active.append(anim)

    Pandemic_Game.outbreak_animations = still_active

def draw_cities():
    for city in city_objects.values():
        x, y = city.location
        color = get_colour(city.colour)

        pygame.draw.circle(screen, (255, 255, 255), (x, y), 12)
        pygame.draw.circle(screen, color, (x, y), 10)

        city_txt = city.name

        if city.research_center == True:
            city_txt += " (R)"

        name_surface = cityfont.render(city_txt, True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(x, y + 25))
        bg_rect = name_rect.inflate(6, 3)
        pygame.draw.rect(screen, (38, 48, 62), bg_rect, border_radius=4)
        pygame.draw.rect(screen, (55, 70, 90), bg_rect, 1, border_radius=4)
        screen.blit(name_surface, name_rect)

        virus_colours = [(80, 130, 255), (230, 210, 40), (180, 180, 180), (240, 60, 60)]
        
        cube_size = 9
        orbit_radius = 22

        cubes = []
        for colour_idx, count in enumerate(city.virus):
            for _ in range(count):
                cubes.append(colour_idx)

        total = len(cubes)
        if total > 0:
            angle_step = (2 * math.pi) / total
            for k, colour_idx in enumerate(cubes):
                angle = virus_angle + k * angle_step
                cx_off = int(x + orbit_radius * math.cos(angle))
                cy_off = int(y + orbit_radius * math.sin(angle))
                rect = pygame.Rect(cx_off - cube_size // 2, cy_off - cube_size // 2, cube_size, cube_size)
                pygame.draw.rect(screen, virus_colours[colour_idx], rect, border_radius=3)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1, border_radius=3)

def draw_board():
    header_surface = largeGunfont.render("PANDEMIC", True, (255, 255, 255))
    header_rect = header_surface.get_rect(center=(250, 80))
    screen.blit(header_surface, header_rect)

    cure_center = 483
    cures_label = smallGunfont.render("Cures", True, (255,255,255))
    screen.blit(cures_label, cures_label.get_rect(center=(cure_center, height-100)))

    cures = [
        ("Blue", 0, (cure_center-90,height-50)),
        ("Yellow", 1, (cure_center-30,height-50)),
        ("Black", 2, (cure_center+30,height-50)),
        ("Red", 3, (cure_center+90,height-50))
    ]

    for colour_name, idx, pos in cures:
        colour_rgb = get_colour(colour_name)

        if Pandemic_Game.cures[idx]:
            fill = (0,120,0)
            border = (0,200,0)
        else:
            fill = (30,30,30)
            border = (200,0,0)

        pygame.draw.circle(screen, fill, pos, 20)
        pygame.draw.circle(screen, border, pos, 20, 4)
        pygame.draw.circle(screen, colour_rgb, pos, 13)
        on_board = sum(city_objects[n].virus[idx] for n in city_objects)
        remaining = 24 - on_board
        cube_surf = cityfont.render(str(remaining), True, (200, 200, 200))
        screen.blit(cube_surf, cube_surf.get_rect(center=(pos)))

    outbreak_center = (100, height-200)
    size = 22
    diamond_points = [
        (outbreak_center[0], outbreak_center[1]-size),
        (outbreak_center[0]+size, outbreak_center[1]),
        (outbreak_center[0], outbreak_center[1]+size),
        (outbreak_center[0]-size, outbreak_center[1])
    ]

    outbreak_label = tinyGunfont.render("Outbreaks", True, (255,255,255))
    screen.blit(outbreak_label, outbreak_label.get_rect(center=(outbreak_center[0], outbreak_center[1]-40)))
    pygame.draw.polygon(screen, (0,140,0), diamond_points)
    pygame.draw.polygon(screen, (0,255,0), diamond_points, 4)

    outbreak_text = tinyGunfont.render(str(Pandemic_Game.outbreak_counter), True, (255,255,255))
    screen.blit(outbreak_text, outbreak_text.get_rect(center=(outbreak_center[0]+1, outbreak_center[1]+1)))

    infection_center = (100, height-100)
    infection_label = tinyGunfont.render("Infection Rate", True, (255,255,255))
    screen.blit(infection_label, infection_label.get_rect(center=(infection_center[0], infection_center[1]-40)))
    pygame.draw.circle(screen, (0,140,0), infection_center, 22)
    pygame.draw.circle(screen, (0,255,0), infection_center, 22, 4)

    infection_text = tinyGunfont.render(str(Pandemic_Game.infection_rate), True, (255,255,255))
    screen.blit(infection_text, infection_text.get_rect(center=infection_center))

def draw_players():
    global turn, num_players
    current_idx = turn % num_players
    pawn_w = 15
    gap = 6
    total_w = num_players * pawn_w + (num_players - 1) * gap
    start_x = -total_w // 2 + pawn_w // 2
    for i in range(num_players):
        p = players[i]
        city = city_objects[p.city]
        x, y = city.location
        offset_x = x + start_x + i * (pawn_w + gap)
        offset_y = y + 30
        fill = ROLE_ACCENT.get(type(p).__name__, (80, 120, 160))
        r = pygame.Rect(offset_x, offset_y, 15, 15)
        pygame.draw.rect(screen, fill, r, border_radius=3)
        border_w = 2 if i == current_idx else 1
        border_color = (255, 255, 255) if i == current_idx else (55, 70, 90)
        pygame.draw.rect(screen, border_color, r, border_w, border_radius=3)

turn = 0
target = None
dispatcher_move_other = None
dispatcher_occupied_mode = False

share_popup = None
discard_popup = None
pending_end_turn = False

action_buttons = {}

def draw_action_button(rect, label, enabled, accent, hover):
    if not enabled:
        bg = (30, 38, 52)
        border = (55, 65, 80)
        text_col = (80, 90, 105)
    elif hover:
        bg = (min(accent[0]//2+40,255), min(accent[1]//2+40,255), min(accent[2]//2+40,255))
        border = accent
        text_col = (255, 255, 255)
    else:
        bg = (accent[0]//3, accent[1]//3, accent[2]//3)
        border = (accent[0]//2+20, accent[1]//2+20, accent[2]//2+20)
        text_col = (200, 210, 220)

    pygame.draw.rect(screen, bg, rect, border_radius=7)
    pygame.draw.rect(screen, border, rect, 2, border_radius=7)

    shine_surf = pygame.Surface((rect.width - 4, rect.height // 3), pygame.SRCALPHA)
    shine_surf.fill((255, 255, 255, 18 if enabled else 6))
    screen.blit(shine_surf, (rect.x + 2, rect.y + 2))

    txt = tinyGunfont.render(label, True, text_col)
    screen.blit(txt, txt.get_rect(center=rect.center))

def check_win_lose():
    global game_over, game_won, lose_reason

    if all(Pandemic_Game.cures):
        game_over = True
        game_won = True
        return

    if Pandemic_Game.outbreak_counter >= 8:
        game_over = True
        game_won = False
        lose_reason = "TOO MANY OUTBREAKS"
        return

    colour_names = ["Blue", "Yellow", "Black", "Red"]
    for idx, col in enumerate(colour_names):
        total = sum(city_objects[n].virus[idx] for n in city_objects)
        if total > 24:
            game_over = True
            game_won = False
            lose_reason = f"NO {col.upper()} CUBES LEFT"
            return

    if not Pandemic_Game.city_cards:
        game_over = True
        game_won = False
        lose_reason = "PLAYER DECK EXHAUSTED"
        return

def end_turn(player):
    global turn, discard_popup, pending_end_turn
    if isinstance(player, Operations_Expert):
        player.ops_expert_special_move_used = False
    player.actions = 4

    cards_drawn = 0
    for _ in range(2):
        if not Pandemic_Game.city_cards:
            check_win_lose()
            return
        drawn = Pandemic_Game.city_cards.pop()
        if drawn == "Infection Card":
            Pandemic_Game.infection_rate += 1
            Pandemic_Game.shuffle_infection_deck()
        else:
            player.cards.append(drawn)
        cards_drawn += 1

    Pandemic_Game.infect_virus(city_objects, players)
    check_win_lose()
    if game_over:
        return

    turn += 1
    for p in players:
        if len(p.cards) > 7:
            discard_popup = {"player": p, "card_rects": []}
            pending_end_turn = True
            break


def player_test(click_event=None):
    global turn, target, dispatcher_move_other, dispatcher_occupied_mode
    global share_popup, discard_popup, pending_end_turn
    mouse_pos = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()
    active_player = players[turn % num_players]

    if discard_popup is not None:
        if click_event and discard_popup.get("card_rects"):
            for crect, card in discard_popup["card_rects"]:
                if crect.collidepoint(mouse_pos):
                    discard_popup["player"].cards.remove(card)
                    Pandemic_Game.player_discard_pile.append(card)
                    if len(discard_popup["player"].cards) > 7:
                        discard_popup["card_rects"] = []
                    else:
                        discard_popup = None
                        pending_end_turn = False
                    break
        return

    if share_popup is not None:
        if click_event and share_popup.get("rects"):
            for key, val in share_popup["rects"].items():
                rect, other, cards, giving = val
                if rect.collidepoint(mouse_pos):
                    if key == "cancel":
                        share_popup = None
                    elif cards and other is not None:
                        if giving:
                            active_player.share_knowledge(other, cards[0], True, city_objects)
                        else:
                            active_player.share_knowledge(other, cards[0], False, city_objects)
                        share_popup = None
                    break
        return

    moved_or_acted = False

    if click_event and action_buttons:
        for btn_key, btn_rect in action_buttons.items():
            if btn_rect.collidepoint(mouse_pos):
                current_city = city_objects[active_player.city]

                if btn_key == "treat":
                    active_player.treat_disease(current_city.colour, city_objects, Pandemic_Game)

                elif btn_key == "build":
                    active_player.build_research_station(city_objects, Pandemic_Game)

                elif btn_key == "cure":
                    colour_counts = {}
                    for c in active_player.cards:
                        if c in city_objects:
                            col = city_objects[c].colour
                            colour_counts.setdefault(col, []).append(c)
                    cure_colour = next(
                        (col for col, cards in colour_counts.items()
                         if len(cards) >= active_player.require_to_cure and not Pandemic_Game.cures[["Blue","Yellow","Black","Red"].index(col)]),
                        None
                    )
                    if cure_colour:
                        cards_to_discard = colour_counts[cure_colour][:active_player.require_to_cure]
                        active_player.discover_cure(cure_colour, cards_to_discard, city_objects, Pandemic_Game)
                        check_win_lose()

                elif btn_key == "share":
                    others = [p for p in players if p != active_player and p.city == active_player.city]
                    if len(others) >= 1:
                        share_popup = {"rects": {}}

                elif btn_key == "skip":
                    if active_player.actions > 0:
                        active_player.actions -= 1

                break

    if isinstance(active_player, Dispatcher):
        if keys[pygame.K_d]:
            dispatcher_move_other = next((p for p in players if p != active_player), None)
        if keys[pygame.K_o]:
            dispatcher_occupied_mode = True

    if click_event:
        for city_name, city in city_objects.items():
            dist = ((mouse_pos[0] - city.location[0])**2 + (mouse_pos[1] - city.location[1])**2)**0.5
            if dist < 20:
                if dispatcher_occupied_mode and isinstance(active_player, Dispatcher):
                    in_city = [p for p in players if p.city == city_name]
                    not_in_city = [p for p in players if p.city != city_name]
                    if in_city and not_in_city and active_player.actions > 0:
                        active_player.dispatcher_move_pawn_to_occupied_city(not_in_city[0], city_name, city_objects, players)
                    dispatcher_occupied_mode = False
                    moved_or_acted = True
                else:
                    mover = dispatcher_move_other if (isinstance(active_player, Dispatcher) and dispatcher_move_other is not None) else active_player
                    current_city_obj = city_objects[mover.city]
                    if city_name in current_city_obj.connections:
                        active_player.drive_ferry(city_name, city_objects, move_pawn=dispatcher_move_other if isinstance(active_player, Dispatcher) else None)
                        moved_or_acted = True
                        if isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                        if isinstance(active_player, Dispatcher):
                            dispatcher_move_other = None
                    elif city_name in active_player.cards:
                        active_player.direct_flight(city_name, city_objects, Pandemic_Game, move_pawn=dispatcher_move_other if isinstance(active_player, Dispatcher) else None)
                        moved_or_acted = True
                        if isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                        if isinstance(active_player, Dispatcher):
                            dispatcher_move_other = None
                    elif mover.city in active_player.cards:
                        active_player.charter_flight(city_name, city_objects, Pandemic_Game, move_pawn=dispatcher_move_other if isinstance(active_player, Dispatcher) else None)
                        moved_or_acted = True
                        if isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                        if isinstance(active_player, Dispatcher):
                            dispatcher_move_other = None
                    elif (isinstance(active_player, Operations_Expert) and dispatcher_move_other is None and
                          not active_player.ops_expert_special_move_used and
                          city_objects[active_player.city].research_center and
                          city_name != active_player.city):
                        city_cards_in_hand = [c for c in active_player.cards if c in city_objects]
                        if city_cards_in_hand:
                            active_player.ops_expert_special_move(city_name, city_cards_in_hand[0], city_objects, Pandemic_Game)
                            moved_or_acted = True
                            if isinstance(active_player, Medic):
                                active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                    else:
                        active_player.shuttle_flight(city_name, city_objects, move_pawn=dispatcher_move_other if isinstance(active_player, Dispatcher) else None)
                        moved_or_acted = True
                        if isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                        if isinstance(active_player, Dispatcher):
                            dispatcher_move_other = None
                if moved_or_acted:
                    break

    if active_player.actions == 0:
        end_turn(active_player)
                
def player_cards_display():
    screen.fill(DARK_BG)

    card_width = 120
    card_height = 70
    card_spacing = 12
    cards_per_row = 4
    panel_pad = 24
    title_bar_h = 52
    avatar_r = 44
    top_header = 80

    mouse_pos = pygame.mouse.get_pos()

    title_surf = smallGunfont.render("PLAYER CARDS", True, TEXT_MUTED)
    title_top = 24
    screen.blit(title_surf, (width // 2 - title_surf.get_width() // 2, title_top))

    for i, player in enumerate(players):
        px = (i % 2) * (width // 2)
        py = top_header + (i // 2) * ((height - top_header) // 2)
        pw = width // 2
        ph = (height - top_header) // 2

        role_name = type(player).__name__.replace("_", " ")
        accent = ROLE_ACCENT.get(type(player).__name__, (80, 120, 160))

        panel_rect = pygame.Rect(px + panel_pad, py + panel_pad + 36, pw - 2 * panel_pad, ph - 2 * panel_pad - 36)
        pygame.draw.rect(screen, CARD_BG, panel_rect, border_radius=12)
        pygame.draw.rect(screen, (accent[0] // 2, accent[1] // 2, accent[2] // 2), panel_rect, 2, border_radius=12)

        bar_rect = pygame.Rect(px + panel_pad, py + panel_pad + 36, pw - 2 * panel_pad, title_bar_h)
        pygame.draw.rect(screen, accent, bar_rect)
        avatar_cx = px + panel_pad + 12 + avatar_r
        avatar_cy = py + panel_pad + 36 + title_bar_h // 2
        pygame.draw.circle(screen, (30, 40, 55), (int(avatar_cx), int(avatar_cy)), avatar_r)
        pygame.draw.circle(screen, accent, (int(avatar_cx), int(avatar_cy)), avatar_r, 3)

        role_txt = smallGunfont.render(role_name.upper(), True, (255, 255, 255))
        role_rect = role_txt.get_rect(midleft=(int(avatar_cx) + avatar_r + 14, bar_rect.centery))
        screen.blit(role_txt, role_rect)

    
        total_cards = len(player.cards)
        if total_cards > 0:
            start_y = py + panel_pad + 36 + title_bar_h + 20
            row_width = min(total_cards, cards_per_row) * (card_width + card_spacing) - card_spacing
            start_x = px + (pw - row_width) // 2

            for j, card in enumerate(player.cards):
                row = j // cards_per_row
                col = j % cards_per_row
                card_x = start_x + col * (card_width + card_spacing)
                card_y = start_y + row * (card_height + card_spacing)

                rect = pygame.Rect(card_x, card_y, card_width, card_height)
                hover = rect.collidepoint(mouse_pos)
                if hover:
                    rect = rect.inflate(4, 4)
                    card_x, card_y = rect.x, rect.y

                if card in city_objects:
                    top_colour = get_colour(city_objects[card].colour)
                else:
                    top_colour = (100, 120, 140)

                card_r = 10
                pygame.draw.rect(screen, (55, 70, 90), rect, border_radius=card_r)
                top_bar = pygame.Rect(rect.x, rect.y, rect.width, 16)
                pygame.draw.rect(screen, top_colour, top_bar, border_radius=card_r)
                pygame.draw.rect(screen, accent, rect, 2, border_radius=card_r)
                txt = cityfont.render(str(card), True, TEXT_WHITE)
                screen.blit(txt, (rect.x + 10, rect.y + 26))
        else:
            no_cards = cityfont.render("No city cards", True, TEXT_MUTED)
            cx = px + pw // 2 - no_cards.get_width() // 2
            cy = py + panel_pad + 36 + title_bar_h + 80
            screen.blit(no_cards, (cx, cy))

def draw_share_popup():
    global share_popup
    if share_popup is None:
        return

    mx, my = pygame.mouse.get_pos()
    active_player = players[turn % num_players]
    accent = ROLE_ACCENT.get(type(active_player).__name__, (80, 120, 160))

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    others = [p for p in players if p != active_player and p.city == active_player.city]
    row_h = 90
    pop_w = 460
    pop_h = 150 + (len(others) * row_h)
    
    board_cx = (width - 200) // 2
    pop_x = board_cx - pop_w // 2
    pop_y = height // 2 - pop_h // 2
    pop_rect = pygame.Rect(pop_x, pop_y, pop_w, pop_h)

    pygame.draw.rect(screen, DARK_BG, pop_rect, border_radius=12)
    pygame.draw.rect(screen, accent, pop_rect, 2, border_radius=12)

    title = smallGunfont.render("SHARE KNOWLEDGE", True, TEXT_WHITE)
    screen.blit(title, title.get_rect(centerx=pop_rect.centerx, top=pop_y + 18))

    share_popup["rects"] = {}

    btn_w, btn_h = 180, 44
    btn_gap = 16
    total_btn_w = btn_w * 2 + btn_gap
    btn_start_x = pop_x + pop_w // 2 - total_btn_w // 2

    row_start_y = pop_y + 72
    for i, other in enumerate(others):
        other_accent = ROLE_ACCENT.get(type(other).__name__, (80, 120, 160))
        name_surf = tinyGunfont.render(other.name, True, other_accent)
        screen.blit(name_surf, name_surf.get_rect(centerx=pop_rect.centerx, top=row_start_y + i * row_h + 8))

        if isinstance(active_player, Researcher):
            can_give_cards = list(active_player.cards)
        else:
            can_give_cards = [active_player.city] if active_player.city in active_player.cards else []
        can_take_cards = [active_player.city] if active_player.city in other.cards else []

        give_rect = pygame.Rect(btn_start_x, row_start_y + i * row_h + 38, btn_w, btn_h)
        take_rect = pygame.Rect(btn_start_x + btn_w + btn_gap, row_start_y + i * row_h + 38, btn_w, btn_h)

        draw_action_button(give_rect, "GIVE CARD", bool(can_give_cards), accent,
                           give_rect.collidepoint(mx, my) and bool(can_give_cards))
        draw_action_button(take_rect, "TAKE CARD", bool(can_take_cards), accent,
                           take_rect.collidepoint(mx, my) and bool(can_take_cards))

        share_popup["rects"][f"give_{i}"] = (give_rect, other, can_give_cards, True)
        share_popup["rects"][f"take_{i}"] = (take_rect, other, can_take_cards, False)

    cancel_rect = pygame.Rect(pop_rect.centerx - 60, pop_y + pop_h - 54, 120, 36)
    draw_action_button(cancel_rect, "CANCEL", True, (100, 100, 110), cancel_rect.collidepoint(mx, my))
    share_popup["rects"]["cancel"] = (cancel_rect, None, None, None)

def draw_discard_popup():
    global discard_popup
    if discard_popup is None:
        return

    mx, my = pygame.mouse.get_pos()
    player = discard_popup["player"]
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    n_cards = len(player.cards)
    board_cx = (width - 200) / 2
    max_pop_w = 860
    card_gap = 10
    pad = 32

    per_row = min(n_cards, max(1, (max_pop_w - pad * 2 + card_gap) // (100 + card_gap)))
    rows = math.ceil(n_cards / per_row)
    card_w = min(100, (max_pop_w - pad * 2 - card_gap * (per_row - 1)) // per_row)
    card_h = int(card_w * 1.1)
    pop_w = pad * 2 + per_row * card_w + (per_row - 1) * card_gap
    title_h = 66
    row_h = card_h + card_gap
    pop_h = title_h + rows * row_h + pad
    pop_x = board_cx - pop_w // 2
    pop_y = height // 2 - pop_h // 2
    pop_rect = pygame.Rect(pop_x, pop_y, pop_w, pop_h)

    pygame.draw.rect(screen, DARK_BG, pop_rect, border_radius=12)
    pygame.draw.rect(screen, (200, 60, 60), pop_rect, 2, border_radius=12)

    over = n_cards - 7
    msg = f"{player.name}: DISCARD {over} CARD{'S' if over > 1 else ''}"
    title = smallGunfont.render(msg, True, (220, 80, 80))
    screen.blit(title, title.get_rect(centerx=pop_rect.centerx, top=pop_y + 14))
    pygame.draw.rect(screen, (60, 40, 40), pygame.Rect(pop_x + 20, pop_y + title_h - 4, pop_w - 40, 1))

    cards_start_x = pop_x + pad
    cards_start_y = pop_y + title_h + 4

    discard_popup["card_rects"] = []
    for i, card in enumerate(player.cards):
        row = i // per_row
        col = i % per_row
        cx = cards_start_x + col * (card_w + card_gap)
        cy = cards_start_y + row * row_h
        crect = pygame.Rect(cx, cy, card_w, card_h)
        hover = crect.collidepoint(mx, my)
        top_colour = get_colour(city_objects[card].colour) if card in city_objects else (100, 120, 140)

        bg_col = (70, 85, 105) if hover else CARD_BG
        pygame.draw.rect(screen, bg_col, crect, border_radius=7)
        pygame.draw.rect(screen, top_colour, pygame.Rect(cx, cy, card_w, 10), border_radius=7)
        border_col = (220, 80, 80) if hover else (55, 70, 90)
        pygame.draw.rect(screen, border_col, crect, 2, border_radius=7)
        words = card.split()
        lines = []
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if cityfont.size(test)[0] <= card_w - 8:
                line = test
            else:
                if line: lines.append(line)
                line = w
        if line: lines.append(line)
        for li, ltext in enumerate(lines[:3]):
            ls = cityfont.render(ltext, True, TEXT_WHITE)
            screen.blit(ls, ls.get_rect(centerx=crect.centerx, top=crect.y + 14 + li * 14))

        if hover:
            xs = tinyGunfont.render("DISCARD", True, (220, 80, 80))
            screen.blit(xs, xs.get_rect(centerx=crect.centerx, bottom=crect.bottom - 5))

        discard_popup["card_rects"].append((crect, card))


def draw_current_player_panel():
    global action_buttons
    panel_x = width - 200
    panel_width = 200
    panel_height = height
    mouse_pos = pygame.mouse.get_pos()

    pygame.draw.rect(screen, DARK_BG, (panel_x, 0, panel_width, panel_height))
    active_player = players[turn % num_players]
    accent = ROLE_ACCENT.get(type(active_player).__name__, (80, 120, 160))

    pygame.draw.rect(screen, (accent[0]//2, accent[1]//2, accent[2]//2), (panel_x, 0, 2, panel_height))
    header_rect = pygame.Rect(panel_x, 0, panel_width, 70)
    pygame.draw.rect(screen, (accent[0]//4, accent[1]//4, accent[2]//4), header_rect)
    pygame.draw.rect(screen, accent, pygame.Rect(panel_x, 68, panel_width, 2))

    name_surface = tinyGunfont.render(active_player.name, True, TEXT_WHITE)
    role_name = type(active_player).__name__.replace("_", " ")
    role_surface = tinyGunfont.render(role_name, True, accent)
    screen.blit(name_surface, (panel_x + 12, 10))
    screen.blit(role_surface, (panel_x + 12, 36))

    pip_y = 82
    actions_label = cityfont.render("ACTIONS", True, TEXT_MUTED)
    screen.blit(actions_label, (panel_x + 12, pip_y))
    for pip_i in range(4):
        pip_x = panel_x + 12 + pip_i * 26
        pip_rect = pygame.Rect(pip_x, pip_y + 16, 20, 10)
        filled = pip_i < active_player.actions
        pygame.draw.rect(screen, accent if filled else (40, 50, 65), pip_rect, border_radius=3)
        if filled:
            pygame.draw.rect(screen, (255,255,255), pip_rect, 1, border_radius=3)

    card_label = cityfont.render("CARDS", True, TEXT_MUTED)
    screen.blit(card_label, (panel_x + 12, 118))

    card_w = 170
    card_h = 46
    card_gap = 6
    card_start_y = 136
    for i, card in enumerate(active_player.cards):
        crect = pygame.Rect(panel_x + 14, card_start_y + i * (card_h + card_gap), card_w, card_h)
        pygame.draw.rect(screen, CARD_BG, crect, border_radius=6)
        top_colour = get_colour(city_objects[card].colour) if card in city_objects else (100, 120, 140)
        pygame.draw.rect(screen, top_colour, pygame.Rect(crect.x, crect.y, card_w, 8), border_radius=6)
        pygame.draw.rect(screen, (55, 70, 90), crect, 1, border_radius=6)
        card_text = cityfont.render(str(card), True, TEXT_WHITE)
        screen.blit(card_text, (crect.x + 8, crect.y + 16))

    div_y = height - 230
    pygame.draw.rect(screen, (45, 57, 75), pygame.Rect(panel_x + 10, div_y, panel_width - 20, 1))
    btn_w = 170
    btn_h = 36
    btn_x = panel_x + 14
    btn_gap = 8
    btn_start_y = div_y + 10

    current_city = city_objects[active_player.city]

    can_treat = any(v > 0 for v in current_city.virus)
    can_build = (active_player.city in active_player.cards and not current_city.research_center)
    colour_counts = {}
    for c in active_player.cards:
        if c in city_objects:
            col = city_objects[c].colour
            colour_counts[col] = colour_counts.get(col, 0) + 1
    can_cure = current_city.research_center and any(
        count >= active_player.require_to_cure and not Pandemic_Game.cures[["Blue","Yellow","Black","Red"].index(col)]
        for col, count in colour_counts.items()
    )
    others_here = [p for p in players if p != active_player and p.city == active_player.city]
    can_share = bool(others_here)

    can_skip = active_player.actions > 0

    buttons = [
        ("treat", "TREAT", can_treat),
        ("build", "BUILD RC", can_build),
        ("cure", "CURE", can_cure),
        ("share", "SHARE", can_share),
        ("skip", "SKIP", can_skip),
    ]

    action_buttons = {}
    for idx, (key, label, enabled) in enumerate(buttons):
        brect = pygame.Rect(btn_x, btn_start_y + idx * (btn_h + btn_gap), btn_w, btn_h)
        action_buttons[key] = brect
        hover = brect.collidepoint(mouse_pos) and enabled
        btn_accent = (90, 100, 115) if key == "skip" else accent
        draw_action_button(brect, label, enabled, btn_accent, hover)

def draw_movement_highlights():
    global turn, players, num_players, city_objects
    if not players:
        return
    active_player = players[turn % num_players]
    current_city_obj = city_objects[active_player.city]
    accent = ROLE_ACCENT.get(type(active_player).__name__, (80, 120, 160))
    for name, city in city_objects.items():
        h_color = None
        if name == active_player.city and any(v > 0 for v in city.virus):
            h_color = accent
        elif name in current_city_obj.connections:
            h_color = accent
        elif current_city_obj.research_center and city.research_center and name != active_player.city:
            h_color = accent
        elif name in active_player.cards:
            h_color = accent
        elif active_player.city in active_player.cards and name != active_player.city:
            h_color = accent
        if h_color is not None:
            cx, cy = city.location
            main_r, main_w = 17, 3
            pygame.draw.circle(screen, h_color, (cx, cy), main_r, main_w)

def draw_result_screen():
    global result_alpha
    result_alpha = min(255, result_alpha + 3)
    t = result_alpha / 255.0

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    if game_won:
        overlay.fill((0, 20, 0, int(220 * t)))
    else:
        overlay.fill((20, 0, 0, int(220 * t)))
    screen.blit(overlay, (0, 0))

    if result_alpha < 30:
        return

    cx = width // 2
    cy = height // 2

    pulse = abs(math.sin(pygame.time.get_ticks() * 0.002)) * 20
    if game_won:
        glow_col = (0, 200, 80)
        ring_col = (0, 255, 100)
    else:
        glow_col = (200, 30, 30)
        ring_col = (255, 60, 60)

    glow_surf = pygame.Surface((500, 500), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*glow_col, 40), (250, 250), int(180 + pulse))
    pygame.draw.circle(glow_surf, (*glow_col, 20), (250, 250), int(220 + pulse))
    screen.blit(glow_surf, (cx - 250, cy - 250))
    pygame.draw.circle(screen, ring_col, (cx, cy), int(190 + pulse), 3)

    if game_won:
        title_text = "VICTORY"
        title_col = (80, 255, 140)
        sub_text = "ALL DISEASES CURED"
        sub_col = (160, 255, 200)
    else:
        title_text = "DEFEAT"
        title_col = (255, 80, 80)
        sub_text = lose_reason
        sub_col = (255, 160, 160)

    title_surf = largeGunfont.render(title_text, True, title_col)
    screen.blit(title_surf, title_surf.get_rect(center=(cx, cy - 60)))

    sub_surf = smallGunfont.render(sub_text, True, sub_col)
    screen.blit(sub_surf, sub_surf.get_rect(center=(cx, cy + 20)))

    cures_done = sum(Pandemic_Game.cures)
    stat1 = tinyGunfont.render(f"CURES FOUND: {cures_done} / 4", True, (200, 200, 200))
    stat2 = tinyGunfont.render(f"OUTBREAKS:   {Pandemic_Game.outbreak_counter} / 8", True, (200, 200, 200))
    stat3 = tinyGunfont.render(f"CARDS LEFT:  {len(Pandemic_Game.city_cards)}", True, (200, 200, 200))
    screen.blit(stat1, stat1.get_rect(center=(cx, cy + 80)))
    screen.blit(stat2, stat2.get_rect(center=(cx, cy + 110)))
    screen.blit(stat3, stat3.get_rect(center=(cx, cy + 140)))

    prompt = cityfont.render("PRESS R TO PLAY AGAIN  |  ESC TO QUIT", True, (120, 120, 120))
    screen.blit(prompt, prompt.get_rect(center=(cx, cy + 195)))


running = True
clock = pygame.time.Clock()

game_state = [1,0,0,0]
virus_angle = 0.0
game_over = False
game_won = False
lose_reason = ""
result_alpha = 0

while running:
    click_event = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                click_event = True

        elif event.type == pygame.KEYDOWN and game_state[0] == 1:
            if event.key == pygame.K_RETURN:
                game_state[0] = 0 
                Pandemic_Game = Board(city_objects, difficulty=selected_difficulty)
                Pandemic_Game.set_board(city_objects)
                num_players = player_options[selected_index]
                for i in range(num_players):
                    new_player = role_classes[i](
                        name=f"Player {i+1}",
                        colour=player_colors[i],
                        total=num_players,
                        city_cards = Pandemic_Game.city_cards,
                        board=Pandemic_Game
                    )
                    players.append(new_player)
                
                Pandemic_Game.add_epidemic_card()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and not game_over:
                if game_state[3] == 0:
                    game_state[3] = 1
                else:
                    game_state[3] = 0

            elif event.key == pygame.K_ESCAPE and game_over:
                running = False

            elif event.key == pygame.K_r and game_over:
                game_over = False
                game_won = False
                lose_reason = ""
                result_alpha = 0
                turn = 0
                players = []

                for name, data in city_list.items():
                    city_objects[name] = City(
                        name=name,
                        connections=data["connections"],
                        colour=data["colour"],
                        location=data["location"]
                    )
                city_objects["Atlanta"].research_center = True

                game_state[0] = 1

    if game_state[0] == 1:
        loading_screen()

    elif game_state[3] == 1 and not game_over:
        player_cards_display()

    else:
        screen.fill((0,30,70))
        screen.blit(board, (0, 0))

        draw_connections()
        draw_cities()
        draw_outbreak_animations()
        draw_movement_highlights()
        draw_board()
        draw_players()
        draw_current_player_panel()

        if not game_over:
            player_test(click_event)
            draw_share_popup()
            draw_discard_popup()
        else:
            draw_result_screen()

    pygame.display.flip()
    clock.tick(60)
    virus_angle += 0.012

pygame.quit()