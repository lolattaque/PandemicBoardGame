class Player:
    def __init__(self, role, starting_location):
        self.cards = []
        self.role = role
        self.location = starting_location
        self.actions = 4


class City:
    def __init__(self, name, connections, colour):
        self.connections = connections
        self.name = name
        self.colour = colour
        self.virus = 0
        self.research_center = False

class Game:
    def __init__(self):
        self.infection_cards = []
        self.city_cards = []
        self.discard_pile = []
        self.outbreak_counter = 0
        self.infection_rate = 2


        

        
