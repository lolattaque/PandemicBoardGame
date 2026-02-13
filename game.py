import pygame
import random
from players import Player, Medic, Scientist, Researcher, Operations_Expert, Dispatcher, Quarantine_Specialist, Contingency_Planner
from cities import City, city_list
from board import Board

pygame.init()

largefont = pygame.font.SysFont("arial", 60)
smallfont = pygame.font.SysFont("arial", 40)  
cityfont = pygame.font.SysFont("arial", 12, bold=True)

width, height = 1200, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pandemic Board Game")

board = pygame.image.load("PandemicGameBoard.jpg")
board = pygame.transform.scale(board, (width, height))



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
player_colors = [(255, 255, 255), (0, 255, 0), (255, 165, 0), (255, 0, 255)]

Pandemic_Game = Board(city_objects)
Pandemic_Game.shuffle_infection_deck()
Pandemic_Game.set_board(city_objects)

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

def draw_connections():
    drawn_connections = set()
    for city_name, city in city_objects.items():
        start_pos = city.location
        start_colour = get_colour(city.colour)
        
        for connection_name in city.connections:
            if connection_name in city_objects:
                target_city = city_objects[connection_name]
                end_pos = target_city.location
                end_colour = get_colour(target_city.colour)
                
                dist = ((start_pos[0] - end_pos[0])**2 + (start_pos[1] - end_pos[1])**2)**0.5
                
                if dist < 750:
                    connection_pair = tuple(sorted((city_name, connection_name)))
                    if connection_pair not in drawn_connections:
                        mid_x = (start_pos[0] + end_pos[0]) / 2
                        mid_y = (start_pos[1] + end_pos[1]) / 2
                        mid_pos = (mid_x, mid_y)
                        
                        pygame.draw.line(screen, start_colour, start_pos, mid_pos, 3)
                        pygame.draw.line(screen, end_colour, mid_pos, end_pos, 3)
                        
                        drawn_connections.add(connection_pair)

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
    header_surface = largefont.render("PANDEMIC", True, (255, 255, 255))
    header_rect = header_surface.get_rect(center=(230, 80))
    screen.blit(header_surface, header_rect)

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

def player_test():
    global turn
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()
    keys = pygame.key.get_pressed()
    active_player = players[turn % num_players]

    if keys[pygame.K_r]:
        print("GGS")
        active_player.build_research_station(city_objects, Pandemic_Game)
        pygame.time.delay(200)

    elif keys[pygame.K_c] and city_objects[active_player.city].research_center:
        active_player.discover_cure(city_objects[active_player.city].colour, [c for c in active_player.cards if city_objects[c].colour == city_objects[active_player.city].colour], city_objects, Pandemic_Game)
        for p in players:
            if isinstance(p, Medic):
                p.auto_remove_cured_cubes(city_objects, Pandemic_Game)
        pygame.time.delay(200)
        print(Pandemic_Game)

    if keys[pygame.K_s]:
        print("swap")
        others = []
        for p in players:
            if p != active_player:
                if p.city == active_player.city:
                    others.append(p)
        target = others[0]
        if active_player.city in active_player.cards:
            active_player.share_knowledge(target, active_player.city, True, city_objects)
        elif active_player.city in target.cards:
            active_player.share_knowledge(target, active_player.city, False, city_objects)
        pygame.time.delay(200)

    elif keys[pygame.K_SPACE]:
        if active_player.actions > 0:
            active_player.actions -= 1
            print(active_player.actions)
            pygame.time.delay(200)

    if mouse_click[0]:
        
        for city_name, city in city_objects.items():
            dist = ((mouse_pos[0] - city.location[0])**2 + (mouse_pos[1] - city.location[1])**2)**0.5
            
            if dist < 20:
                current_city_obj = city_objects[active_player.city]
                
                if city_name in current_city_obj.connections:
                    active_player.drive_ferry(city_name, city_objects)
                    if isinstance(active_player, Medic):
                        active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                elif city_name == active_player.city:
                    active_player.treat_disease(current_city_obj.colour, city_objects, Pandemic_Game)

                elif city_name in active_player.cards:
                    active_player.direct_flight(city_name, city_objects, Pandemic_Game)
                    if isinstance(active_player, Medic):
                        active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                elif active_player.city in active_player.cards:
                    active_player.charter_flight(city_name, city_objects, Pandemic_Game)
                    if isinstance(active_player, Medic):
                        active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                else:
                    active_player.shuttle_flight(city_name, city_objects)
                    if isinstance(active_player, Medic):
                        active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                pygame.time.delay(200)

    if active_player.actions == 0:
        active_player.actions = 4
        print(active_player.actions)
        turn += 1
        Pandemic_Game.infect_virus(city_objects)
        for _ in range (2):
            active_player.draw_cards(Pandemic_Game.city_cards)
    
    action_text = largefont.render(f"Actions: {active_player.actions}", True, active_player.colour)
    screen.blit(action_text, (20, height - 80))
            
def player_display():
    screen.fill((0,0,0))
    for i, player in enumerate(players):
        x, y, w, h = (i%2)*(width/2), (i//2)*(height/2), width/2, height/2
        pygame.draw.rect(screen, player.colour, (x, y, w, h))
        pygame.draw.circle(screen, (100,100,100), (int(x+80), int(y+80)), 60)
        screen.blit(smallfont.render(type(player).__name__, True, (0,0,0)), (x+150, y+60))
        for j, card in enumerate(player.cards):
            card_color = get_colour(city_objects[card].colour) if card in city_objects else (0,0,0)
            screen.blit(smallfont.render(f" - {card}", True, card_color), (x+30, y+160+(j*40)))

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
                num_players = player_options[selected_index]
                for i in range(num_players):
                    new_player = role_classes[i](
                        name=f"Player {i+1}",
                        colour=player_colors[i],
                        total=num_players,
                        city_cards = Pandemic_Game.city_cards
                    )
                    players.append(new_player)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                if game_state [3] == 0:
                    game_state[3] = 1
                else:
                    game_state[3] = 0

    if game_state[0] == 1:
        loading_screen()
    
    elif game_state[3] == 1:
        player_display()

    
    else:
        screen.fill((0,30,70))
        #screen.blit(board, (0, 0))
        
        draw_connections()
        draw_cities()
        draw_board()
        draw_players()
        player_test()

        for city_name in city_objects:
            city = city_objects[city_name]
            city.outbreak(city_objects)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()