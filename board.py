import random
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
                city_objects[city_name].virus = cubes
                
    def infect_virus(self, city_objects):
        for i in range(self.infection_rate):
            city_name = self.draw_infection_card()
            city = city_objects[city_name]
            city.virus += 1
            if city.virus >= 4:
                city.outbreak(city_objects, self)
                

