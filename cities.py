class City:
    def __init__(self, name, connections, colour, location):
        self.connections = connections
        self.location = location
        self.name = name
        self.colour = colour
        self.virus = 0
        self.research_center = False

city_list = {
    # BLUE - AI list of cities all wrong
    "San Francisco": {"connections": ["Chicago", "Tokyo", "Los Angeles"], "colour": "Blue", "location": (100, 280)},
    "Chicago": {"connections": ["San Francisco", "Los Angeles", "Mexico City", "Atlanta", "Montreal"], "colour": "Blue", "location": (210, 250)},
    "Atlanta": {"connections": ["Chicago", "Miami", "Washington"], "colour": "Blue", "location": (240, 310)},
    "Montreal": {"connections": ["Chicago", "Washington", "New York"], "colour": "Blue", "location": (290, 250)},
    "New York": {"connections": ["Montreal", "Washington", "London", "Madrid"], "colour": "Blue", "location": (350, 260)},#
    "Washington": {"connections": ["Atlanta", "New York", "Montreal", "Miami"], "colour": "Blue", "location": (325, 305)},
    "Miami": {"connections": ["Atlanta", "Mexico City", "Washington"], "colour": "Blue", "location": (600, 400)},
    "Los Angeles": {"connections": ["San Francisco", "Chicago", "Mexico City", "Sydney"], "colour": "Blue", "location": (200, 400)},
    "Mexico City": {"connections": ["Los Angeles", "Chicago", "Miami", "Bogota", "Lima"], "colour": "Blue", "location": (350, 500)},

    # YELLOW
    "Bogota": {"connections": ["Mexico City", "Lima", "Miami", "Sao Paulo", "Buenos Aires"], "colour": "Yellow", "location": (500, 550)},
    "Lima": {"connections": ["Mexico City", "Bogota", "Santiago"], "colour": "Yellow", "location": (300, 650)},
    "Santiago": {"connections": ["Lima"], "colour": "Yellow", "location": (300, 750)},
    "Sao Paulo": {"connections": ["Bogota", "Buenos Aires", "Lagos"], "colour": "Yellow", "location": (600, 650)},
    "Buenos Aires": {"connections": ["Bogota", "Sao Paulo"], "colour": "Yellow", "location": (600, 750)},
    "Lagos": {"connections": ["Sao Paulo", "Khartoum", "Kinshasa"], "colour": "Yellow", "location": (900, 500)},
    "Khartoum": {"connections": ["Lagos", "Johannesburg", "Cairo"], "colour": "Yellow", "location": (950, 400)},
    "Johannesburg": {"connections": ["Khartoum", "Kinshasa"], "colour": "Yellow", "location": (1000, 700)},
    "Kinshasa": {"connections": ["Lagos", "Johannesburg", "Khartoum"], "colour": "Yellow", "location": (900, 600)},

    # BLACK
    "Cairo": {"connections": ["Algiers", "Istanbul", "Khartoum", "Riyadh"], "colour": "Black", "location": (950, 300)},
    "Algiers": {"connections": ["Madrid", "Paris", "Istanbul", "Cairo"], "colour": "Black", "location": (850, 200)},
    "Istanbul": {"connections": ["Milan", "Algiers", "St. Petersburg", "Cairo", "Moscow"], "colour": "Black", "location": (1050, 250)},
    "Moscow": {"connections": ["St. Petersburg", "Istanbul", "Tehran"], "colour": "Black", "location": (1200, 150)},
    "Tehran": {"connections": ["Moscow", "Delhi", "Karachi", "Baghdad"], "colour": "Black", "location": (1150, 300)},
    "Baghdad": {"connections": ["Tehran", "Istanbul", "Riyadh", "Cairo", "Karachi"], "colour": "Black", "location": (1100, 350)},
    "Riyadh": {"connections": ["Baghdad", "Cairo", "Karachi"], "colour": "Black", "location": (1100, 450)},
    "Karachi": {"connections": ["Tehran", "Baghdad", "Riyadh", "Mumbai", "Delhi"], "colour": "Black", "location": (1250, 400)},
    "Delhi": {"connections": ["Tehran", "Karachi", "Mumbai", "Chennai"], "colour": "Black", "location": (1300, 300)},
    "Mumbai": {"connections": ["Karachi", "Delhi", "Chennai"], "colour": "Black", "location": (1250, 500)},
    "Chennai": {"connections": ["Mumbai", "Delhi", "Bangkok", "Kolkata"], "colour": "Black", "location": (1350, 550)},
    "Kolkata": {"connections": ["Chennai", "Bangkok", "Hong Kong"], "colour": "Black", "location": (1400, 400)},

    # RED
    "Beijing": {"connections": ["Shanghai", "Seoul"], "colour": "Red", "location": (1400, 150)},
    "Shanghai": {"connections": ["Beijing", "Hong Kong", "Taipei", "Tokyo", "Seoul"], "colour": "Red", "location": (1350, 250)},
    "Seoul": {"connections": ["Beijing", "Shanghai", "Tokyo"], "colour": "Red", "location": (1450, 100)},
    "Tokyo": {"connections": ["Seoul", "Shanghai", "San Francisco", "Osaka"], "colour": "Red", "location": (1500, 200)},
    "Osaka": {"connections": ["Tokyo", "Taipei"], "colour": "Red", "location": (1520, 250)},
    "Taipei": {"connections": ["Shanghai", "Osaka", "Hong Kong"], "colour": "Red", "location": (1450, 300)},
    "Hong Kong": {"connections": ["Bangkok", "Kolkata", "Shanghai", "Manila", "Ho Chi Minh City"], "colour": "Red", "location": (1400, 350)},
    "Bangkok": {"connections": ["Kolkata", "Chennai", "Jakarta", "Hong Kong", "Ho Chi Minh City"], "colour": "Red", "location": (1350, 400)},
    "Ho Chi Minh City": {"connections": ["Bangkok", "Hong Kong", "Jakarta", "Manila"], "colour": "Red", "location": (1350, 500)},
    "Jakarta": {"connections": ["Bangkok", "Ho Chi Minh City", "Sydney"], "colour": "Red", "location": (1300, 600)},
    "Manila": {"connections": ["Taipei", "Hong Kong", "Ho Chi Minh City", "San Francisco", "Sydney"], "colour": "Red", "location": (1400, 500)},
    "Sydney": {"connections": ["Jakarta", "Manila", "Los Angeles"], "colour": "Red", "location": (1450, 700)}
}
