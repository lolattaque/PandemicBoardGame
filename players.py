COLOUR_INDEX = {"Blue": 0, "Yellow": 1, "Black": 2, "Red": 3}
MAX_RESEARCH_STATIONS = 6


class Player:
    def __init__(self, name, colour, total, city_cards):
        self.cards = []
        self.name = name
        self.city = "Atlanta"
        self.colour = colour
        self.actions = 4
    

    def draw_cards(self, city_cards):
        if len(self.cards) <= 7:
            for i in range(2):
                drawn_card = city_cards.pop()
                self.cards.append(drawn_card)
                print(self.cards)

    def drive_ferry(self, target_city_name, city_objects):
        if self.actions > 0:
            current = city_objects.get(self.city)
            if current and target_city_name in current.connections:
                self.city = target_city_name
                self.actions -= 1

    def direct_flight(self, city_card_name, city_objects, board):
        if self.actions > 0:
            if city_card_name in self.cards:
                self.cards.remove(city_card_name)
                board.player_discard_pile.append(city_card_name)
                self.city = city_card_name
                self.actions -= 1

    def charter_flight(self, target_city_name, city_objects, board):
        if self.actions > 0:
            if self.city in self.cards:
                self.cards.remove(self.city)
                board.player_discard_pile.append(self.city)
                self.city = target_city_name
                self.actions -= 1

    def shuttle_flight(self, target_city_name, city_objects):
        if self.actions > 0:
            current = city_objects.get(self.city)
            target = city_objects.get(target_city_name)
            if current.research_center and target.research_center:
                self.city = target_city_name
                self.actions -= 1

    def build_research_station(self, city_objects, board, remove_from_city_name=None):
        if self.actions > 0:
            if self.city in self.cards:
                current = city_objects.get(self.city)
                count = sum(1 for c in city_objects.values() if c.research_center)
                can_build = False
                if count < MAX_RESEARCH_STATIONS:
                    can_build = True
                elif count >= MAX_RESEARCH_STATIONS and remove_from_city_name:
                    other = city_objects.get(remove_from_city_name)
                    if other and other.research_center:
                        other.research_center = False
                        can_build = True
                if can_build:
                    self.cards.remove(self.city)
                    board.player_discard_pile.append(self.city)
                    current.research_center = True
                    self.actions -= 1

    def treat_disease(self, colour, city_objects, board):
        if self.actions > 0:
            current = city_objects.get(self.city)
            if current and current.colour == colour and current.virus > 0:
                idx = COLOUR_INDEX.get(colour)
                if idx is not None:
                    if board.cures[idx] or self.role == 'medic':
                        current.virus = 0
                        total = sum(c.virus for c in city_objects.values() if c.colour == colour)
                        if total == 0:
                            board.eradicated[idx] = True
                    else:
                        current.virus -= 1
                    self.actions -= 1

    def share_knowledge(self, other_player, card, give, city_objects):
        if self.actions > 0:
            if other_player.city == self.city and card == self.city:
                if give and card in self.cards:
                    self.cards.remove(card)
                    other_player.cards.append(card)
                    self.actions -= 1
                elif not give and card in other_player.cards:
                    other_player.cards.remove(card)
                    self.cards.append(card)
                    self.actions -= 1

    def discover_cure(self, colour, cards_to_discard, city_objects, board):
        if self.actions > 0:
            current = city_objects.get(self.city)
            idx = COLOUR_INDEX.get(colour)
            required = self.require_to_cure
            if current and current.research_center and not board.cures[idx]:
                if len(cards_to_discard) == required and all(c in self.cards for c in cards_to_discard):
                    if all(city_objects.get(c).colour == colour for c in cards_to_discard):
                        for c in cards_to_discard:
                            self.cards.remove(c)
                            board.player_discard_pile.append(c)
                        board.cures[idx] = True
                        total_cubes = sum(city.virus for city in city_objects.values() if city.colour == colour)
                        if total_cubes == 0:
                            board.eradicated[idx] = True
                        self.actions -= 1

    def use_event_card(self, card):
        pass


class Medic(Player):
    def treat_disease(self, colour, city_objects, board):
        if self.actions > 0:
            current = city_objects.get(self.city)
            if current and current.colour == colour and current.virus > 0:
                idx = COLOUR_INDEX.get(colour)
                current.virus = 0
                total = sum(c.virus for c in city_objects.values() if c.colour == colour)
                if total == 0:
                    board.eradicated[idx] = True
                self.actions -= 1

    def auto_remove_cured_cubes(self, city_objects, board):
        current = city_objects.get(self.city)
        idx = COLOUR_INDEX.get(current.colour)
        if board.cures[idx] and current.virus > 0:
            current.virus = 0
            total = sum(c.virus for c in city_objects.values() if c.colour == current.colour)
            if total == 0:
                board.eradicated[idx] = True

class Scientist(Player):
        Player.require_to_cure = 4


class Researcher(Player):
    pass

class Dispatcher(Player):
    pass

class Contingency_Planner(Player):
    pass

class Operations_Expert(Player):
    Player.operations = True


class Quarantine_Specialist(Player):
    pass
        

        



