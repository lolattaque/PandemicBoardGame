import pygame
import random
from players import (
    Player, Medic, Scientist, Researcher, Operations_Expert, Dispatcher, Quarantine_Specialist, Contingency_Planner,
    ROLE_ACCENT, DARK_BG, CARD_BG, TEXT_WHITE, TEXT_MUTED,
    draw_players, draw_current_player_panel, player_cards_display, draw_share_popup, draw_occupy_popup, draw_discard_popup
)
from cities import City, city_list, draw_connections, draw_cities, draw_movement_highlights
from board import Board, draw_board, draw_outbreak_animations, draw_result_screen

pygame.init()

largefont = pygame.font.SysFont("arial", 60)
smallfont = pygame.font.SysFont("arial", 40)
cityfont = pygame.font.SysFont("arial", 12, bold=True)

largeGunfont = pygame.font.Font("Gunplay.ttf", 100)
smallGunfont = pygame.font.Font("Gunplay.ttf", 50)
tinyGunfont = pygame.font.Font("Gunplay.ttf", 20)
avatar_footer_font = pygame.font.SysFont("arial", 32)

width, height = 1400, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pandemic Board Game")

board = pygame.image.load("image.png")
board = pygame.transform.scale(board, (width-200, height))

def _load_avatar_surfaces(sheet_path, cols=3, rows=3, target_px=92):
    sheet = pygame.image.load(sheet_path).convert_alpha()
    sw, sh = sheet.get_width(), sheet.get_height()
    tile_w, tile_h = sw // cols, sh // rows
    tiles = []
    for ry in range(rows):
        for cx in range(cols):
            rect = pygame.Rect(cx * tile_w, ry * tile_h, tile_w, tile_h)
            tile = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
            tile.blit(sheet, (0, 0), rect)
            tile = pygame.transform.smoothscale(tile, (target_px, target_px))
            tiles.append(tile)
    return tiles


AVATAR_SHEET_PATH = "assets/avatars.png"

avatar_surfaces = _load_avatar_surfaces(AVATAR_SHEET_PATH, cols=3, rows=3, target_px=92)


avatar_surfaces_small = [pygame.transform.smoothscale(s, (64, 64)) for s in avatar_surfaces] if avatar_surfaces else []
avatar_surfaces_grid = [pygame.transform.smoothscale(s, (116, 116)) for s in avatar_surfaces] if avatar_surfaces else []

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

avatar_select_player_idx = 0
avatar_grid_rects = []

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


def avatar_select_screen():
    global avatar_select_player_idx, avatar_grid_rects
    screen.fill((10, 20, 30))

    title = largeGunfont.render("CHOOSE AVATARS", True, (235, 235, 235))
    screen.blit(title, (width // 2 - title.get_width() // 2, 48))

    cur_player = players[avatar_select_player_idx]
    accent = ROLE_ACCENT.get(type(cur_player).__name__, (200, 0, 0))

    chosen = {p.avatar_idx for p in players if getattr(p, "avatar_idx", None) is not None}

    left_x = 120
    top_y = 175
    row_h = 104
    thumb = 64
    for i, p in enumerate(players):
        row_y = top_y + i * row_h
        row_accent = ROLE_ACCENT.get(type(p).__name__, (140, 140, 140))
        row_rect = pygame.Rect(left_x - 14, row_y - 10, 420, row_h - 12)
        if i == avatar_select_player_idx:
            pygame.draw.rect(screen, (18, 24, 34), row_rect, border_radius=12)
            pygame.draw.rect(screen, row_accent, row_rect, 2, border_radius=12)
        else:
            pygame.draw.rect(screen, (14, 18, 26), row_rect, border_radius=12)
            pygame.draw.rect(screen, (50, 60, 78), row_rect, 1, border_radius=12)

        name_s = smallfont.render(p.name, True, (255, 255, 255) if i == avatar_select_player_idx else (200, 200, 200))
        role_s = tinyGunfont.render(type(p).__name__.replace("_", " "), True, row_accent)
        screen.blit(name_s, (left_x + 12, row_y))
        screen.blit(role_s, (left_x + 14, row_y + 48))

        if getattr(p, "avatar_idx", None) is not None and avatar_surfaces_small:
            idx = p.avatar_idx
            if isinstance(idx, int) and 0 <= idx < len(avatar_surfaces_small):
                tx = row_rect.right - thumb - 14
                ty = row_rect.centery - thumb // 2
                screen.blit(avatar_surfaces_small[idx], (tx, ty))
                pygame.draw.rect(screen, row_accent, pygame.Rect(tx - 4, ty - 4, thumb + 8, thumb + 8), 2, border_radius=10)

    grid_cols = 3
    cell = 140
    gap = 26
    grid_x = width // 2 + 120
    grid_y = 200
    avatar_grid_rects = []
    cur_idx = getattr(cur_player, "avatar_idx", None)
    for idx, surf in enumerate(avatar_surfaces_grid if avatar_surfaces_grid else avatar_surfaces):
        r = idx // grid_cols
        c = idx % grid_cols
        x = grid_x + c * (cell + gap)
        y = grid_y + r * (cell + gap)
        rect = pygame.Rect(x, y, cell, cell)
        avatar_grid_rects.append((rect, idx))
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        taken_by_other = (idx in chosen) and (cur_idx != idx)

        if taken_by_other:
            bg = (16, 20, 28)
            border = (55, 60, 70)
        else:
            bg = (35, 45, 62) if hovered else (24, 30, 42)
            border = accent if hovered else (70, 85, 105)

        pygame.draw.rect(screen, bg, rect, border_radius=16)
        pygame.draw.rect(screen, border, rect, 3 if hovered and not taken_by_other else 2, border_radius=16)

        if surf:
            screen.blit(surf, surf.get_rect(center=rect.center))

        if taken_by_other:
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (rect.x, rect.y))
            lock = tinyGunfont.render("TAKEN", True, (190, 190, 190))
            screen.blit(lock, lock.get_rect(center=rect.center))

        if cur_idx == idx:
            pygame.draw.rect(screen, (255, 230, 150), rect.inflate(-10, -10), 3, border_radius=14)

    all_set = all(getattr(p, "avatar_idx", None) is not None for p in players)
    instr_text = "All set — press Enter to begin." if all_set else "One avatar per player — no duplicates."
    instr_col = (220, 224, 230) if all_set else (175, 185, 198)
    instr = avatar_footer_font.render(instr_text, True, instr_col)
    footer_margin = 88
    screen.blit(instr, (width // 2 - instr.get_width() // 2, height - footer_margin))

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
    global turn, target, dispatcher_move_other, dispatcher_occupied_mode, dispatcher_occupied_pawn
    global share_popup, discard_popup, occupy_popup, pending_end_turn
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

    if occupy_popup is not None:
        if click_event and occupy_popup.get("rects"):
            for key, val in occupy_popup["rects"].items():
                rect, chosen_player = val
                if rect.collidepoint(mouse_pos):
                    if key == "cancel":
                        occupy_popup = None
                        dispatcher_occupied_mode = False
                        dispatcher_occupied_pawn = None
                    elif chosen_player is not None:
                        dispatcher_occupied_pawn = chosen_player
                        occupy_popup = None
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

                elif btn_key == "dispatcher_occupy":
                    if isinstance(active_player, Dispatcher) and active_player.actions > 0:
                        dispatcher_occupied_mode = True
                        dispatcher_occupied_pawn = None
                        occupy_popup = {"rects": {}}

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
                if dispatcher_occupied_mode and isinstance(active_player, Dispatcher) and dispatcher_occupied_pawn is not None:
                    mover = dispatcher_occupied_pawn
                    if active_player.actions > 0:
                        # Ability 1: move any pawn to any city containing another pawn
                        in_city = [p for p in players if p.city == city_name]
                        if in_city and mover.city != city_name:
                            active_player.dispatcher_move_pawn_to_occupied_city(mover, city_name, city_objects, players)
                            moved_or_acted = True
                        else:
                            # Ability 2: move another player's pawn as if it were your own
                            current_city_obj = city_objects[mover.city]
                            if city_name in current_city_obj.connections:
                                active_player.drive_ferry(city_name, city_objects, move_pawn=mover)
                                moved_or_acted = True
                            elif city_name in active_player.cards:
                                active_player.direct_flight(city_name, city_objects, Pandemic_Game, move_pawn=mover)
                                moved_or_acted = True
                            elif mover.city in active_player.cards:
                                active_player.charter_flight(city_name, city_objects, Pandemic_Game, move_pawn=mover)
                                moved_or_acted = True
                            else:
                                active_player.shuttle_flight(city_name, city_objects, move_pawn=mover)
                                moved_or_acted = True

                        if moved_or_acted and isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                    # After a successful move, exit occupy mode
                    if moved_or_acted:
                        dispatcher_occupied_mode = False
                        dispatcher_occupied_pawn = None
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

turn = 0
target = None
dispatcher_move_other = None
dispatcher_occupied_mode = False
dispatcher_occupied_pawn = None

share_popup = None
occupy_popup = None
discard_popup = None
pending_end_turn = False
action_buttons = {}

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
                if game_state[0] == 2 and players and avatar_surfaces:
                    mx, my = pygame.mouse.get_pos()
                    chosen = {p.avatar_idx for p in players if getattr(p, "avatar_idx", None) is not None}
                    cur = players[avatar_select_player_idx]
                    cur_idx = getattr(cur, "avatar_idx", None)
                    for rect, aidx in avatar_grid_rects:
                        if rect.collidepoint((mx, my)):
                            if (aidx in chosen) and (cur_idx != aidx):
                                break
                            players[avatar_select_player_idx].avatar_idx = aidx
                            next_idx = None
                            for step in range(1, len(players) + 1):
                                j = (avatar_select_player_idx + step) % len(players)
                                if getattr(players[j], "avatar_idx", None) is None:
                                    next_idx = j
                                    break
                            avatar_select_player_idx = avatar_select_player_idx if next_idx is None else next_idx
                            break

        elif event.type == pygame.KEYDOWN and game_state[0] == 1:
            if event.key == pygame.K_RETURN:
                game_state[0] = 2
                Pandemic_Game = Board(city_objects, difficulty=selected_difficulty)
                Pandemic_Game.set_board(city_objects)
                num_players = player_options[selected_index]
                players = []
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
                avatar_select_player_idx = 0

        elif event.type == pygame.KEYDOWN and game_state[0] == 2:
            if event.key == pygame.K_RETURN:
                if players and all(getattr(p, "avatar_idx", None) is not None for p in players):
                    game_state[0] = 0
            elif event.key == pygame.K_ESCAPE:
                players = []
                game_state[0] = 1

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

    elif game_state[0] == 2:
        avatar_select_screen()

    elif game_state[3] == 1 and not game_over:
        player_cards_display(screen, players, city_objects, width, height, smallGunfont, cityfont, get_colour, avatar_surfaces=avatar_surfaces)

    else:
        screen.fill((0,30,70))
        screen.blit(board, (0, 0))

        draw_connections(screen, city_objects, width, get_colour)
        draw_cities(screen, city_objects, virus_angle, cityfont, get_colour)
        draw_outbreak_animations(screen, Pandemic_Game, city_objects)
        draw_movement_highlights(screen, players, city_objects, turn, num_players, dispatcher_occupied_mode, dispatcher_occupied_pawn, dispatcher_move_other)
        draw_board(screen, Pandemic_Game, city_objects, width, height, largeGunfont, smallGunfont, tinyGunfont, cityfont, get_colour)
        draw_players(screen, players, city_objects, turn, num_players)
        action_buttons = draw_current_player_panel(screen, players, city_objects, Pandemic_Game, turn, num_players, width, height, tinyGunfont, cityfont, get_colour, dispatcher_occupied_mode, dispatcher_occupied_pawn, avatar_surfaces=avatar_surfaces)

        if not game_over:
            player_test(click_event)
            share_popup = draw_share_popup(screen, share_popup, players, turn, width, height, smallGunfont, tinyGunfont)
            occupy_popup = draw_occupy_popup(screen, occupy_popup, players, turn, width, height, tinyGunfont)
            discard_popup = draw_discard_popup(screen, discard_popup, city_objects, width, height, smallGunfont, tinyGunfont, cityfont, get_colour)
        else:
            result_alpha = draw_result_screen(screen, Pandemic_Game, game_won, lose_reason, result_alpha, width, height, largeGunfont, smallGunfont, tinyGunfont, cityfont)

    pygame.display.flip()
    clock.tick(60)
    virus_angle += 0.012

pygame.quit()