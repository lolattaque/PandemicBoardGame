import pygame
import random
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
        bg_rect = name_rect.inflate(4, 2)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)
        screen.blit(name_surface, name_rect)

        virus_count_surface = cityfont.render(str(city.virus), True, (255, 255, 255))
        virus_rect = virus_count_surface.get_rect(center=(x, y))
        screen.blit(virus_count_surface, virus_rect)

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
    for i in range(num_players):
        p = players[i]
        city = city_objects[p.city]
        x, y = city.location
        offset_x = x + (i * 10) - 22.5
        offset_y = y + 30
        pygame.draw.rect(screen, p.colour, (offset_x, offset_y, 15, 15))
        pygame.draw.rect(screen, (0, 0, 0), (offset_x, offset_y, 15, 15), 1)

turn = 0
target = None
def player_test():
    global turn, target
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()
    keys = pygame.key.get_pressed()
    active_player = players[turn % num_players]
    moved_or_acted = False

    if keys[pygame.K_r]:
        active_player.build_research_station(city_objects, Pandemic_Game)
        pygame.time.delay(200)

    elif keys[pygame.K_c] and city_objects[active_player.city].research_center:
        active_player.discover_cure(city_objects[active_player.city].colour, [c for c in active_player.cards if city_objects[c].colour == city_objects[active_player.city].colour], city_objects, Pandemic_Game)
        for p in players:
            if isinstance(p, Medic):
                p.auto_remove_cured_cubes(city_objects, Pandemic_Game)
        pygame.time.delay(200)

    if keys[pygame.K_s]:
        others = [p for p in players if p != active_player and p.city == active_player.city]
        if others:
            target = others[0]
            if isinstance(active_player, Researcher):
                valid_give = [c for c in active_player.cards]
            else:
                valid_give = [active_player.city] if active_player.city in active_player.cards else []   
            valid_take = [active_player.city] if active_player.city in target.cards else []
            if valid_give:
                active_player.share_knowledge(target, valid_give[0], True, city_objects)
            elif valid_take:
                active_player.share_knowledge(target, valid_take[0], False, city_objects)
        pygame.time.delay(200)

    elif keys[pygame.K_SPACE]:
        if active_player.actions > 0:
            active_player.actions -= 1
            pygame.time.delay(200)

    if mouse_click[0]:
        for city_name, city in city_objects.items():
            dist = ((mouse_pos[0] - city.location[0])**2 + (mouse_pos[1] - city.location[1])**2)**0.5
            
            if dist < 20:
                current_city_obj = city_objects[active_player.city]
                
                if city_name in current_city_obj.connections:
                    active_player.drive_ferry(city_name, city_objects)
                    moved_or_acted = True
                    if isinstance(active_player, Medic):
                        active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                elif city_name == active_player.city:
                    active_player.treat_disease(current_city_obj.colour, city_objects, Pandemic_Game)
                    moved_or_acted = True

                elif city_name in active_player.cards:
                    active_player.direct_flight(city_name, city_objects, Pandemic_Game)
                    moved_or_acted = True
                    if isinstance(active_player, Medic):
                        active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                elif active_player.city in active_player.cards:
                    active_player.charter_flight(city_name, city_objects, Pandemic_Game)
                    moved_or_acted = True
                    if isinstance(active_player, Medic):
                        active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                else:
                    active_player.shuttle_flight(city_name, city_objects)
                    moved_or_acted = True
                    if isinstance(active_player, Medic):
                        active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                
                if moved_or_acted:
                    pygame.time.delay(200)
                    break

    if active_player.actions == 0:
        active_player.actions = 4
        turn += 1
        Pandemic_Game.infect_virus(city_objects)
        for _ in range (2):
            active_player.draw_cards(Pandemic_Game.city_cards, Pandemic_Game)
                
def player_cards_display():
    screen.fill((0,0,0))

    card_width = 120
    card_height = 70
    card_spacing = 12
    cards_per_row = 4

    mouse_pos = pygame.mouse.get_pos()

    for i, player in enumerate(players):
        x, y, w, h = (i%2)*(width/2), (i//2)*(height/2), width/2, height/2

        pygame.draw.rect(screen, player.colour, (x, y, w, h))
        pygame.draw.circle(screen, (100,100,100), (int(x+80), int(y+80)), 60)

        role_txt = smallGunfont.render(type(player).__name__, True, (0,0,0))
        screen.blit(role_txt, (x+150, y+60))

        total_cards = len(player.cards)
        if total_cards > 0:
            total_width = min(total_cards, cards_per_row)*(card_width+card_spacing)-card_spacing
            start_x = x + (w-total_width)//2

            for j, card in enumerate(player.cards):
                row = j // cards_per_row
                col = j % cards_per_row

                card_x = start_x + col*(card_width+card_spacing)
                card_y = y + 160 + row*(card_height+card_spacing)

                rect = pygame.Rect(card_x, card_y, card_width, card_height)

                if rect.collidepoint(mouse_pos):
                    rect.y -= 8

                if card in city_objects:
                    top_colour = get_colour(city_objects[card].colour)
                else:
                    top_colour = (200,200,200)

                pygame.draw.rect(screen, (235,235,235), rect, border_radius=10)
                pygame.draw.rect(screen, top_colour, (rect.x, rect.y, card_width, 14), border_radius=10)
                pygame.draw.rect(screen, (0,0,0), rect, 2, border_radius=10)

                txt = cityfont.render(str(card), True, (0,0,0))
                screen.blit(txt, (rect.x+8, rect.y+28))

def draw_current_player_panel():
    panel_x = width - 200
    panel_width = 200
    panel_height = height
    pygame.draw.rect(screen, (20, 20, 40), (panel_x, 0, panel_width, panel_height))

    active_player = players[turn % num_players]

    name_surface = tinyGunfont.render(active_player.name, True, active_player.colour)
    role_surface = tinyGunfont.render(type(active_player).__name__, True, (255, 255, 255))
    screen.blit(name_surface, (panel_x + 10, 20))
    screen.blit(role_surface, (panel_x + 10, 60))

    actions_surface = tinyGunfont.render(f"Actions: {active_player.actions}", True, (255, 255, 255))
    screen.blit(actions_surface, (panel_x + 10, 100))

    card_width = 160
    card_height = 60
    spacing = 10
    start_y = 150
    for i, card in enumerate(active_player.cards):
        rect = pygame.Rect(panel_x + 20, start_y + i*(card_height + spacing), card_width, card_height)
        pygame.draw.rect(screen, (235,235,235), rect, border_radius=8)
        if card in city_objects:
            top_colour = get_colour(city_objects[card].colour)
        else:
            top_colour = (200,200,200)
        pygame.draw.rect(screen, top_colour, (rect.x, rect.y, card_width, 14), border_radius=8)
        pygame.draw.rect(screen, (0,0,0), rect, 2, border_radius=8)
        card_text = cityfont.render(str(card), True, (0,0,0))
        screen.blit(card_text, (rect.x + 8, rect.y + 20))

def draw_movement_highlights():
    global turn, players, num_players, city_objects
    if not players: return
    
    active_player = players[turn % num_players]
    current_city_obj = city_objects[active_player.city]
    
    for name, city in city_objects.items():
        h_color = None

        if name == active_player.city and city.virus > 0:
            h_color = (255, 255, 255)
        elif name in current_city_obj.connections: 
            h_color = (0, 255, 0)
        elif current_city_obj.research_center and city.research_center and name != active_player.city: 
            h_color = (200, 0, 255)
        elif name in active_player.cards: 
            h_color = (0, 200, 255)
        elif active_player.city in active_player.cards and name != active_player.city: 
            h_color = (255, 255, 0)
        if h_color:
            pygame.draw.circle(screen, h_color, city.location, 18, 3)

running = True
clock = pygame.time.Clock()
game_state = [1,0,0,0]

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
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
            if event.key == pygame.K_p:
                if game_state [3] == 0:
                    game_state[3] = 1
                else:
                    game_state[3] = 0

    if game_state[0] == 1:
        loading_screen()
    
    elif game_state[3] == 1:
        player_cards_display()

    
    else:
        screen.fill((0,30,70))
        screen.blit(board, (0, 0))
        
        draw_connections()
        draw_cities()
        draw_movement_highlights()
        draw_board()
        draw_players()
        player_test()
        draw_current_player_panel()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()