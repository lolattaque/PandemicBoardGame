import math
from players import quarantine_protects, COLOUR_INDEX, Dispatcher

class City:
    def __init__(self, name, connections, colour, location):
        self.connections = connections
        self.location = location
        self.name = name
        self.colour = colour
        self.virus = [0, 0, 0, 0]
        self.research_center = False

    def outbreak(self, city_objects, board, players=None, visited=None, source_idx=None):
        if visited is None:
            visited = set()

        if source_idx is None:
            source_idx = COLOUR_INDEX.get(self.colour, 0)

        if self.name in visited:
            return

        if self.virus[source_idx] < 4:
            return

        visited.add(self.name)
        board.outbreak_counter += 1
        if hasattr(board, "snd_swoosh"):
            board.snd_swoosh.play()
        self.virus[source_idx] = 3
        if hasattr(board, "outbreak_animations"):
            board.outbreak_animations.append({
                "source": self.name,
                "targets": [c for c in self.connections if c in city_objects],
                "colour_idx": source_idx,
                "progress": 0.0,
                "alpha": 255,
            })

        for connection in self.connections:
            neighbour = city_objects[connection]
            if players and quarantine_protects(neighbour.name, players, city_objects):
                continue
            current = neighbour.virus[source_idx]
            if current < 3:
                neighbour.virus[source_idx] = current + 1
            elif current == 3:
                neighbour.outbreak(city_objects, board, players, visited, source_idx)

def draw_connections(screen, city_objects, width, get_colour_fn):
    import pygame
    drawn_connections = set()
    wrap_pairs = {
        ("Los Angeles", "Sydney"),
        ("Manila", "San Francisco"),
        ("San Francisco", "Manila"),
        ("San Francisco", "Tokyo"),
    }

    for city_name, city in city_objects.items():
        start_pos = city.location
        start_colour = get_colour_fn(city.colour)

        for connection_name in city.connections:
            if connection_name not in city_objects:
                continue
            pair = tuple(sorted((city_name, connection_name)))
            if pair in drawn_connections:
                continue

            target_city = city_objects[connection_name]
            end_pos = target_city.location
            end_colour = get_colour_fn(target_city.colour)

            if pair in wrap_pairs:
                mid_y = (start_pos[1] + end_pos[1]) // 2
                left_exit = (0, mid_y)
                right_exit = (width - 200, mid_y)
                if start_pos[0] < end_pos[0]:
                    pygame.draw.line(screen, start_colour, start_pos, left_exit, 3)
                    pygame.draw.line(screen, end_colour, right_exit, end_pos, 3)
                else:
                    pygame.draw.line(screen, start_colour, start_pos, right_exit, 3)
                    pygame.draw.line(screen, end_colour, left_exit, end_pos, 3)
            else:
                mid_pos = ((start_pos[0] + end_pos[0]) / 2, (start_pos[1] + end_pos[1]) / 2)
                pygame.draw.line(screen, start_colour, start_pos, mid_pos, 3)
                pygame.draw.line(screen, end_colour, mid_pos, end_pos, 3)

            drawn_connections.add(pair)


def draw_cities(screen, city_objects, virus_angle, cityfont, get_colour_fn):
    import pygame
    for city in city_objects.values():
        x, y = city.location
        color = get_colour_fn(city.colour)

        pygame.draw.circle(screen, (255, 255, 255), (x, y), 12)
        pygame.draw.circle(screen, color, (x, y), 10)

        city_txt = city.name + (" (R)" if city.research_center else "")
        name_surface = cityfont.render(city_txt, True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(x, y + 25))
        bg_rect = name_rect.inflate(6, 3)
        pygame.draw.rect(screen, (38, 48, 62), bg_rect, border_radius=4)
        pygame.draw.rect(screen, (55, 70, 90), bg_rect, 1, border_radius=4)
        screen.blit(name_surface, name_rect)

        virus_colours = [(80, 130, 255), (230, 210, 40), (180, 180, 180), (240, 60, 60)]
        cube_size, orbit_radius = 9, 22
        cubes = [colour_idx for colour_idx, count in enumerate(city.virus) for _ in range(count)]
        total = len(cubes)
        if total > 0:
            angle_step = (2 * math.pi) / total
            for k, colour_idx in enumerate(cubes):
                angle = virus_angle + k * angle_step
                cx_off = int(x + orbit_radius * math.cos(angle))
                cy_off = int(y + orbit_radius * math.sin(angle))
                rect = pygame.Rect(cx_off - cube_size//2, cy_off - cube_size//2, cube_size, cube_size)
                pygame.draw.rect(screen, virus_colours[colour_idx], rect, border_radius=3)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1, border_radius=3)


def draw_movement_highlights(screen, players, city_objects, turn, num_players, dispatcher_occupied_mode=False, dispatcher_occupied_pawn=None, dispatcher_move_other=None):
    import pygame
    from players import ROLE_ACCENT
    if not players:
        return
    active_player = players[turn % num_players]
   
    if dispatcher_occupied_mode and isinstance(active_player, Dispatcher) and dispatcher_occupied_pawn is not None:
        mover = dispatcher_occupied_pawn
    else:
        mover = dispatcher_move_other if (isinstance(active_player, Dispatcher) and dispatcher_move_other is not None) else active_player
    current_city_obj = city_objects[mover.city]
    accent = ROLE_ACCENT.get(type(active_player).__name__, (80, 120, 160))

    for name, city in city_objects.items():
        h_color = None

        if dispatcher_occupied_mode and isinstance(active_player, Dispatcher) and dispatcher_occupied_pawn is not None:
            if any(p.city == name for p in players) and name != mover.city:
                h_color = accent

        if h_color is None and name == mover.city and any(v > 0 for v in city.virus):
            h_color = accent
        elif h_color is None and name in current_city_obj.connections:
            h_color = accent
        elif h_color is None and current_city_obj.research_center and city.research_center and name != mover.city:
            h_color = accent
        elif h_color is None and name in active_player.cards:
            h_color = accent
        elif h_color is None and mover.city in active_player.cards and name != mover.city:
            h_color = accent
        if h_color is not None:
            cx, cy = city.location
            pygame.draw.circle(screen, h_color, (cx, cy), 17, 3)


city_list = {
    # BLUE
    "San Francisco": {"connections": ["Chicago", "Tokyo", "Los Angeles", "Manila"], "colour": "Blue", "location": (100, 280)},
    "Chicago": {"connections": ["San Francisco", "Los Angeles", "Mexico City", "Atlanta", "Montreal"], "colour": "Blue", "location": (205, 250)},
    "Atlanta": {"connections": ["Chicago", "Miami", "Washington"], "colour": "Blue", "location": (235, 310)},
    "Montreal": {"connections": ["Chicago", "Washington", "New York"], "colour": "Blue", "location": (290, 250)},
    "New York": {"connections": ["Montreal", "Washington", "London", "Madrid"], "colour": "Blue", "location": (355, 260)},
    "Washington": {"connections": ["Atlanta", "New York", "Montreal", "Miami"], "colour": "Blue", "location": (325, 305)},
    "London": {"connections": ["New York", "Madrid", "Paris", "Essen"], "colour": "Blue", "location": (505, 210)},
    "Madrid": {"connections": ["New York", "London", "Paris", "Algiers", "Sao Paulo"], "colour": "Blue", "location": (495, 285)},
    "Essen": {"connections": ["London", "Paris", "Milan", "St. Petersburg"], "colour": "Blue", "location": (590, 195)},
    "Paris": {"connections": ["London", "Madrid", "Essen", "Milan", "Algiers"], "colour": "Blue", "location": (570, 250)},
    "Milan": {"connections": ["Essen", "Paris", "Istanbul"], "colour": "Blue", "location": (625, 235)},
    "St. Petersburg": {"connections": ["Essen", "Istanbul", "Moscow"], "colour": "Blue", "location": (680, 180)},

    # YELLOW
    "Los Angeles": {"connections": ["San Francisco", "Chicago", "Mexico City", "Sydney"], "colour": "Yellow", "location": (115, 355)},
    "Mexico City": {"connections": ["Los Angeles", "Chicago", "Miami", "Bogota", "Lima"], "colour": "Yellow", "location": (190, 380)},
    "Miami": {"connections": ["Atlanta", "Mexico City", "Washington", "Bogota"], "colour": "Yellow", "location": (290, 370)},
    "Bogota": {"connections": ["Mexico City", "Lima", "Miami", "Sao Paulo", "Buenos Aires"], "colour": "Yellow", "location": (280, 450)},
    "Lima": {"connections": ["Mexico City", "Bogota", "Santiago"], "colour": "Yellow", "location": (255, 535)},
    "Santiago": {"connections": ["Lima"], "colour": "Yellow", "location": (265, 620)},
    "Sao Paulo": {"connections": ["Bogota", "Buenos Aires", "Madrid", "Lagos"], "colour": "Yellow", "location": (400, 545)},
    "Buenos Aires": {"connections": ["Bogota", "Sao Paulo"], "colour": "Yellow", "location": (350, 605)},
    "Lagos": {"connections": ["Sao Paulo", "Khartoum", "Kinshasa"], "colour": "Yellow", "location": (560, 435)},
    "Khartoum": {"connections": ["Lagos", "Johannesburg", "Cairo", "Kinshasa"], "colour": "Yellow", "location": (665, 420)},
    "Johannesburg": {"connections": ["Khartoum", "Kinshasa"], "colour": "Yellow", "location": (660, 570)},
    "Kinshasa": {"connections": ["Lagos", "Johannesburg", "Khartoum"], "colour": "Yellow", "location": (615, 490)},

    # BLACK
    "Cairo": {"connections": ["Algiers", "Istanbul", "Khartoum", "Riyadh", "Baghdad"], "colour": "Black", "location": (650, 345)},
    "Algiers": {"connections": ["Madrid", "Paris", "Istanbul", "Cairo"], "colour": "Black", "location": (585, 330)},
    "Istanbul": {"connections": ["Milan", "Algiers", "St. Petersburg", "Cairo", "Moscow", "Baghdad"], "colour": "Black", "location": (660, 280)},
    "Moscow": {"connections": ["St. Petersburg", "Istanbul", "Tehran"], "colour": "Black", "location": (725, 235)},
    "Tehran": {"connections": ["Moscow", "Delhi", "Karachi", "Baghdad"], "colour": "Black", "location": (780, 270)},
    "Baghdad": {"connections": ["Tehran", "Istanbul", "Riyadh", "Cairo", "Karachi"], "colour": "Black", "location": (720, 315)},
    "Riyadh": {"connections": ["Baghdad", "Cairo", "Karachi"], "colour": "Black", "location": (730, 390)},
    "Karachi": {"connections": ["Tehran", "Baghdad", "Riyadh", "Mumbai", "Delhi"], "colour": "Black", "location": (800, 345)},
    "Delhi": {"connections": ["Tehran", "Karachi", "Mumbai", "Chennai", "Kolkata"], "colour": "Black", "location": (860, 325)},
    "Mumbai": {"connections": ["Karachi", "Delhi", "Chennai"], "colour": "Black", "location": (810, 400)},
    "Chennai": {"connections": ["Mumbai", "Delhi", "Bangkok", "Kolkata", "Jakarta"], "colour": "Black", "location": (870, 445)},
    "Kolkata": {"connections": ["Chennai", "Bangkok", "Hong Kong", "Delhi"], "colour": "Black", "location": (915, 340)},

    # RED
    "Beijing": {"connections": ["Shanghai", "Seoul"], "colour": "Red", "location": (965, 250)},
    "Shanghai": {"connections": ["Beijing", "Hong Kong", "Taipei", "Tokyo", "Seoul"], "colour": "Red", "location": (970, 310)},
    "Seoul": {"connections": ["Beijing", "Shanghai", "Tokyo"], "colour": "Red", "location": (1040, 245)},
    "Tokyo": {"connections": ["Seoul", "Shanghai", "San Francisco", "Osaka"], "colour": "Red", "location": (1095, 280)},
    "Osaka": {"connections": ["Tokyo", "Taipei"], "colour": "Red", "location": (1100, 335)},
    "Taipei": {"connections": ["Shanghai", "Osaka", "Hong Kong", "Manila"], "colour": "Red", "location": (1045, 365)},
    "Hong Kong": {"connections": ["Bangkok", "Kolkata", "Shanghai", "Manila", "Ho Chi Minh City", "Taipei"], "colour": "Red", "location": (975, 370)},
    "Bangkok": {"connections": ["Kolkata", "Chennai", "Jakarta", "Hong Kong", "Ho Chi Minh City"], "colour": "Red", "location": (930, 405)},
    "Ho Chi Minh City": {"connections": ["Bangkok", "Hong Kong", "Jakarta", "Manila"], "colour": "Red", "location": (980, 465)},
    "Jakarta": {"connections": ["Bangkok", "Ho Chi Minh City", "Sydney", "Chennai"], "colour": "Red", "location": (930, 510)},
    "Manila": {"connections": ["Taipei", "Hong Kong", "Ho Chi Minh City", "San Francisco", "Sydney"], "colour": "Red", "location": (1060, 460)},
    "Sydney": {"connections": ["Jakarta", "Manila", "Los Angeles"], "colour": "Red", "location": (1110, 620)}
}