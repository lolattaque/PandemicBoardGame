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
        player_cards_display(screen, players, city_objects, width, height, smallGunfont, cityfont, get_colour)

    else:
        screen.fill((0,30,70))
        screen.blit(board, (0, 0))

        draw_connections(screen, city_objects, width, get_colour)
        draw_cities(screen, city_objects, virus_angle, cityfont, get_colour)
        draw_outbreak_animations(screen, Pandemic_Game, city_objects)
        draw_movement_highlights(screen, players, city_objects, turn, num_players, dispatcher_occupied_mode, dispatcher_occupied_pawn, dispatcher_move_other)
        draw_board(screen, Pandemic_Game, city_objects, width, height, largeGunfont, smallGunfont, tinyGunfont, cityfont, get_colour)
        draw_players(screen, players, city_objects, turn, num_players)
        action_buttons = draw_current_player_panel(screen, players, city_objects, Pandemic_Game, turn, num_players, width, height, tinyGunfont, cityfont, get_colour, dispatcher_occupied_mode, dispatcher_occupied_pawn)

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