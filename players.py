class Player:
    def __init__(self, role, starting_location):
        self.cards = []
        self.role = role
        self.location = starting_location
        self.actions = 4

    def move(self, city):
        pass

    def ferry(self, city):
        pass

    def shuttle(self, city):
        pass

    def treat_disease(self, city):
        pass

    def share_knowledge(self, other_player, card):
        pass

    def discover_cure(self, color):
        pass

    def build_research_station(self, city):
        pass

    def use_event_card(self, card):
        pass


class Medic(Player):
    pass

class Scientist(Player):
    pass

class Researcher(Player):
    pass

class Dispatcher(Player):
    pass

class Contingency_Planner(Player):
    pass

class Operations_Expert(Player):
    pass

class Quarantine_Specialist(Player):
    pass




        

        
