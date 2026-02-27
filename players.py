COLOUR_INDEX = {"Blue": 0, "Yellow": 1, "Black": 2, "Red": 3}
MAX_RESEARCH_STATIONS = 6

class Player:
    def __init__(self, name, colour, total, city_cards, board):
        self.cards = []
        self.name = name
        self.city = "Atlanta"
        self.colour = colour
        self.actions = 4
        self.require_to_cure = 5
        self.operations = False

        for _ in range (6-total):
            self.draw_cards(city_cards, board)

        
    def draw_cards(self, city_cards, board):
        if len(self.cards) == 7:
            self.cards.pop(0)
        
        if len(self.cards) < 7:
            drawn_card = city_cards.pop()
            if drawn_card == "Infection Card":
                board.infection_rate += 1
                board.shuffle_infection_deck()
                self.draw_cards(city_cards,board)

            else:
                self.cards.append(drawn_card)        

    def drive_ferry(self, target_city_name, city_objects, move_pawn=None):
        mover = move_pawn if move_pawn is not None else self
        if self.actions > 0:
            current = city_objects.get(mover.city)
            if current and target_city_name in current.connections:
                mover.city = target_city_name
                self.actions -= 1

    def direct_flight(self, city_card_name, city_objects, board, move_pawn=None):
        mover = move_pawn if move_pawn is not None else self
        if self.actions > 0:
            if city_card_name in self.cards:
                self.cards.remove(city_card_name)
                board.player_discard_pile.append(city_card_name)
                mover.city = city_card_name
                self.actions -= 1

    def charter_flight(self, target_city_name, city_objects, board, move_pawn=None):
        mover = move_pawn if move_pawn is not None else self
        if self.actions > 0:
            if mover.city in self.cards:
                self.cards.remove(mover.city)
                board.player_discard_pile.append(mover.city)
                mover.city = target_city_name
                self.actions -= 1

    def shuttle_flight(self, target_city_name, city_objects, move_pawn=None):
        mover = move_pawn if move_pawn is not None else self
        if self.actions > 0:
            current = city_objects.get(mover.city)
            target = city_objects.get(target_city_name)
            if current.research_center and target.research_center:
                mover.city = target_city_name
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
            idx = COLOUR_INDEX.get(colour)
            if current and current.colour == colour and idx is not None and current.virus[idx] > 0:
                if board.cures[idx]:
                    current.virus[idx] = 0
                    total = sum(c.virus[idx] for c in city_objects.values() if c.colour == colour)
                    if total == 0:
                        board.eradicated[idx] = True
                else:
                    current.virus[idx] -= 1
                self.actions -= 1

    def share_knowledge(self, other_player, card, give, city_objects):
        if self.actions > 0 and other_player.city == self.city:
            if give and card in self.cards and card == self.city:
                self.cards.remove(card)
                other_player.cards.append(card)
                self.actions -= 1
            elif not give and card in other_player.cards:
                can_take = card == self.city or (isinstance(other_player, Researcher))
                if can_take:
                    other_player.cards.remove(card)
                    self.cards.append(card)
                    self.actions -= 1

    def discover_cure(self, colour, cards_to_discard, city_objects, board):
        if self.actions > 0:
            current = city_objects.get(self.city)
            idx = COLOUR_INDEX.get(colour)
            required = 5
            if current and current.research_center and not board.cures[idx]:
                if len(cards_to_discard) == required and all(c in self.cards for c in cards_to_discard):
                    if all(city_objects.get(c).colour == colour for c in cards_to_discard):
                        for c in cards_to_discard:
                            self.cards.remove(c)
                            board.player_discard_pile.append(c)
                        board.cures[idx] = True
                        total_cubes = sum(city.virus[idx] for city in city_objects.values() if city.colour == colour)
                        if total_cubes == 0:
                            board.eradicated[idx] = True
                        self.actions -= 1

    def use_event_card(self, card_name, board, city_objects, target_city, reordered_list):
        if card_name in self.cards:
            if card_name == "Government Grant":
                if target_city:
                    city = city_objects.get(target_city)
                    city.research_center = True
                    self.cards.remove(card_name)
                    board.player_discard_pile.append(card_name)
                    print(f"Government Grant used: Research Station built in {target_city}")
            
            elif card_name == "Airlift":
                if target_city:
                    self.city = target_city 
                    self.cards.remove(card_name)
                    board.player_discard_pile.append(card_name)
            
            elif card_name == "One Quiet Night":
                # Skip the next 'Infect Cities' step
                board.quiet_night_active = True
                self._discard_event(card_name, board)
    
            elif card_name == "Forecast":
                num_to_draw = min(6, len(board.infection_cards))
                top_6 = board.infection_cards[-num_to_draw:]
                        
                        # 2. Remove them from the deck temporarily
                board.infection_cards = board.infection_cards[:-num_to_draw]
                        
                print(f"Forecasting: {top_6}")
            
                        # 3. Put them back in the new order
                        # If reordered_list is provided (e.g., ['Paris', 'Tokyo', ...]), use it.
                        # Otherwise, just put them back as they were (safe default).
                if reordered_list and len(reordered_list) == num_to_draw:
                    board.infection_cards.extend(reordered_list)
                else:
                    board.infection_cards.extend(top_6)
                        
                    print("Infection deck rearranged.")
            
                    # Cleanup: Discard the event card
                self.cards.remove(card_name)
                board.player_discard_pile.append(card_name)
    
            elif card_name == "Resilient Population":
                if target_city in board.infection_discard_pile:
                    board.infection_discard_pile.remove(target_city)
                    self.cards.remove(card_name)
                    board.player_discard_pile.append(card_name)
            pass


class Medic(Player):
    def treat_disease(self, colour, city_objects, board):
        if self.actions > 0:
            current = city_objects.get(self.city)
            idx = COLOUR_INDEX.get(colour)
            if current and current.colour == colour and idx is not None and current.virus[idx] > 0:
                current.virus[idx] = 0
                total = sum(c.virus[idx] for c in city_objects.values() if c.colour == colour)
                if total == 0:
                    board.eradicated[idx] = True
                self.actions -= 1

    def auto_remove_cured_cubes(self, city_objects, board):
        current = city_objects.get(self.city)
        idx = COLOUR_INDEX.get(current.colour)
        if board.cures[idx] and current.virus[idx] > 0:
            current.virus[idx] = 0
            total = sum(c.virus[idx] for c in city_objects.values() if c.colour == current.colour)
            if total == 0:
                board.eradicated[idx] = True

class Scientist(Player):
    def discover_cure(self, colour, cards_to_discard, city_objects, board):
        if self.actions > 0:
            current = city_objects.get(self.city)
            idx = COLOUR_INDEX.get(colour)
            required = 4
            if current and current.research_center and not board.cures[idx]:
                if len(cards_to_discard) == required and all(c in self.cards for c in cards_to_discard):
                    if all(city_objects.get(c).colour == colour for c in cards_to_discard):
                        for c in cards_to_discard:
                            self.cards.remove(c)
                            board.player_discard_pile.append(c)
                        board.cures[idx] = True
                        total_cubes = sum(city.virus[idx] for city in city_objects.values() if city.colour == colour)
                        if total_cubes == 0:
                            board.eradicated[idx] = True
                        self.actions -= 1

class Researcher(Player):
    def share_knowledge(self, other_player, card, give, city_objects):
        if self.actions > 0 and other_player.city == self.city:
            if give:
                if card in self.cards and card in city_objects:
                    self.cards.remove(card)
                    other_player.cards.append(card)
                    self.actions -= 1
            else:
                if card in other_player.cards and card == self.city:
                    other_player.cards.remove(card)
                    self.cards.append(card)
                    self.actions -= 1

class Dispatcher(Player):
    def dispatcher_move_pawn_to_occupied_city(self, pawn_player, target_city_name, city_objects, players):
        if self.actions > 0 and city_objects.get(target_city_name):
            someone_else_there = any(p.city == target_city_name and p != pawn_player for p in players)
            if someone_else_there:
                pawn_player.city = target_city_name
                self.actions -= 1

class Contingency_Planner(Player):
    def __init__(self, name, colour, total, city_cards, board):
        super().__init__(name, colour, total, city_cards, board)
        self.stored_event_card = None

    def retrieve_event_card(self, card_name, board):
        event_cards = ("Government Grant", "Airlift", "One Quiet Night", "Forecast", "Resilient Population")
        if self.actions > 0 and self.stored_event_card is None:
            if card_name in board.player_discard_pile:
                board.player_discard_pile.remove(card_name)
                self.stored_event_card = card_name
                self.actions -= 1

    def use_event_card(self, card_name, board, city_objects, target_city, reordered_list):
        if card_name == self.stored_event_card:
            self._play_stored_event(card_name, board, city_objects, target_city, reordered_list)
            self.stored_event_card = None
            return
        if card_name in self.cards:
            super().use_event_card(card_name, board, city_objects, target_city, reordered_list)

    def _play_stored_event(self, card_name, board, city_objects, target_city, reordered_list):
        if card_name == "Government Grant":
            if target_city:
                city = city_objects.get(target_city)
                if city:
                    city.research_center = True
        elif card_name == "Airlift":
            if target_city:
                self.city = target_city
        elif card_name == "One Quiet Night":
            board.quiet_night_active = True
        elif card_name == "Forecast":
            num_to_draw = min(6, len(board.infection_cards))
            top_6 = board.infection_cards[-num_to_draw:]
            board.infection_cards = board.infection_cards[:-num_to_draw]
            if reordered_list and len(reordered_list) == num_to_draw:
                board.infection_cards.extend(reordered_list)
            else:
                board.infection_cards.extend(top_6)
        elif card_name == "Resilient Population":
            if target_city and hasattr(board, "infection_discard_pile") and target_city in board.infection_discard_pile:
                board.infection_discard_pile.remove(target_city)
            elif target_city and hasattr(board, "infection_card_discard_pile") and target_city in board.infection_card_discard_pile:
                board.infection_card_discard_pile.remove(target_city)

class Operations_Expert(Player):
    def __init__(self, name, colour, total, city_cards, board):
        super().__init__(name, colour, total, city_cards, board)
        self.ops_expert_special_move_used = False

    def build_research_station(self, city_objects, board, remove_from_city_name=None):
        if self.actions > 0:
            current = city_objects.get(self.city)
            if not current:
                return
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
                current.research_center = True
                self.actions -= 1

    def ops_expert_special_move(self, target_city_name, card_to_discard, city_objects, board):
        if self.actions > 0 and not self.ops_expert_special_move_used:
            current = city_objects.get(self.city)
            if current and current.research_center and target_city_name in city_objects:
                if card_to_discard in self.cards and card_to_discard in city_objects:
                    self.cards.remove(card_to_discard)
                    board.player_discard_pile.append(card_to_discard)
                    self.city = target_city_name
                    self.actions -= 1
                    self.ops_expert_special_move_used = True

class Quarantine_Specialist(Player):
    pass


def quarantine_protects(city_name, players, city_objects):
    for p in players:
        if not isinstance(p, Quarantine_Specialist):
            continue
        if p.city == city_name:
            return True
        cur = city_objects.get(p.city)
        if cur and city_name in cur.connections:
            return True
    return False

