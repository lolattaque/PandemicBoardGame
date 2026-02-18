from players import quarantine_protects

class City:
    def __init__(self, name, connections, colour, location):
        self.connections = connections
        self.location = location
        self.name = name
        self.colour = colour
        self.virus = 0
        self.research_center = False

    def outbreak(self, city_objects, board, players=None, visited=None):
        if visited is None:
            visited = set()

        if self.name in visited:
            return

        if self.virus < 4:
            return

        visited.add(self.name)
        board.outbreak_counter += 1
        self.virus = 3

        for connection in self.connections:
            neighbour = city_objects[connection]
            if players and quarantine_protects(neighbour.name, players, city_objects):
                continue
            neighbour.virus += 1
            if neighbour.virus >= 4:
                neighbour.outbreak(city_objects, board, players, visited)

city_list = {
    # BLUE (Done)
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