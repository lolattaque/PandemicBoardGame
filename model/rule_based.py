from collections import deque
from players import Player, Scientist, Researcher, COLOUR_INDEX

COLOURS = ["Blue", "Yellow", "Black", "Red"]

def bfs_path(start, goal, city_objects):
    if start == goal:
        return []
    visited = {start}
    queue = deque([(start, [])])
    while queue:
        current, path = queue.popleft()
        for neighbour in city_objects[current].connections:
            if neighbour not in visited:
                new_path = path + [neighbour]
                if neighbour == goal:
                    return new_path
                visited.add(neighbour)
                queue.append((neighbour, new_path))
    return []

def nearest_research_station(start, city_objects):
    if city_objects[start].research_center:
        return start, []
    visited = {start}
    queue = deque([(start, [])])
    while queue:
        current, path = queue.popleft()
        for neighbour in city_objects[current].connections:
            if neighbour not in visited:
                new_path = path + [neighbour]
                if city_objects[neighbour].research_center:
                    return neighbour, new_path
                visited.add(neighbour)
                queue.append((neighbour, new_path))
    return None, []

def nearest_city_with_cubes(start, city_objects, board):
    current = city_objects[start]
    if any(current.virus[i] > 0 and not board.eradicated[i] for i in range(4)):
        return start, []
    visited = {start}
    queue = deque([(start, [])])
    while queue:
        city_name, path = queue.popleft()
        for neighbour in city_objects[city_name].connections:
            if neighbour not in visited:
                new_path = path + [neighbour]
                city = city_objects[neighbour]
                if any(city.virus[i] > 0 and not board.eradicated[i] for i in range(4)):
                    return neighbour, new_path
                visited.add(neighbour)
                queue.append((neighbour, new_path))
    return None, []

class AIPlayer(Player):

    def _require_to_cure(self):
        return 4 if isinstance(self, Scientist) else 5

    def _cure_colour_cards(self, city_objects, board):
        result = {c: [] for c in COLOURS}
        for card in self.cards:
            city = city_objects.get(card)
            if city:
                colour = city.colour
                idx = COLOUR_INDEX[colour]
                if not board.cures[idx]:
                    result[colour].append(card)
        return result

    def _find_trade_target(self, city_objects, board, players):
        colour_cards = self._cure_colour_cards(city_objects, board)
        best_colour = max(colour_cards, key=lambda c: len(colour_cards[c]))
        require = self._require_to_cure()
        my_count = len(colour_cards[best_colour])

        if my_count != require - 1:
            return None

        for partner in players:
            if partner is self:
                continue

            partner_useful = [
                c for c in partner.cards
                if city_objects.get(c) and city_objects[c].colour == best_colour
                and c not in self.cards
            ]

            if len(partner_useful) < 3:
                continue

            if isinstance(partner, Researcher):
                return (partner, partner.city, partner_useful[0])
            else:
                best_card = min(
                    partner_useful,
                    key=lambda card: len(bfs_path(self.city, card, city_objects))
                )
                return (partner, best_card, best_card)

        return None

    def auto_discard(self, city_objects, board):
        colour_cards = self._cure_colour_cards(city_objects, board)
        best_colour = max(colour_cards, key=lambda c: len(colour_cards[c]))
        for card in list(self.cards):
            city = city_objects.get(card)
            if not city:
                self.cards.remove(card)
                board.player_discard_pile.append(card)
                return
            if city.colour != best_colour:
                self.cards.remove(card)
                board.player_discard_pile.append(card)
                return
        card = self.cards[0]
        self.cards.remove(card)
        board.player_discard_pile.append(card)

    def take_turn(self, city_objects, board, players):
        while self.actions > 0:
            taken = self._decide_action(city_objects, board, players)
            if not taken:
                break

    def _decide_action(self, city_objects, board, players):
        require = self._require_to_cure()
        colour_cards = self._cure_colour_cards(city_objects, board)
        current = city_objects[self.city]

        claimed_colours = set()
        for other in players:
            if other is self:
                continue
            for colour in COLOURS:
                idx = COLOUR_INDEX[colour]
                if board.cures[idx]:
                    continue
                other_count = sum(
                    1 for c in other.cards
                    if city_objects.get(c) and city_objects[c].colour == colour
                )
                my_count = len(colour_cards[colour])
                if other_count >= 3 and other_count > my_count:
                    claimed_colours.add(colour)

        unclaimed = {c: cards for c, cards in colour_cards.items() if c not in claimed_colours}
        working_set = unclaimed if unclaimed else colour_cards

        best_colour = max(working_set, key=lambda c: len(working_set[c]))
        best_count = len(working_set[best_colour])

        for colour, cards in working_set.items():
            if len(cards) >= require:
                if current.research_center:
                    self.discover_cure(colour, cards[:require], city_objects, board)
                    return True

                _, station_path = nearest_research_station(self.city, city_objects)

                if len(station_path) > 3 and self.city in self.cards:
                    current_card_colour = city_objects[self.city].colour
                    if current_card_colour != colour:
                        self.build_research_station(city_objects, board)
                        return True

                if station_path:
                    self.drive_ferry(station_path[0], city_objects)
                    return True

        if best_count >= 2:
            if len(self.cards) >= 7:
                for card in list(self.cards):
                    city = city_objects.get(card)
                    if city and city.colour != best_colour:
                        self.cards.remove(card)
                        board.player_discard_pile.append(card)
                        return True
                    if not city:
                        self.cards.remove(card)
                        board.player_discard_pile.append(card)
                        return True

            trade = self._find_trade_target(city_objects, board, players)
            if trade:
                partner, meeting_city, card = trade
                if self.city == meeting_city and partner.city == meeting_city:
                    partner.share_knowledge(self, card, give=True, city_objects=city_objects)
                    return True
                else:
                    path = bfs_path(self.city, meeting_city, city_objects)
                    if path:
                        self.drive_ferry(path[0], city_objects)
                        return True

        for other in players:
            if other is self or not isinstance(other, AIPlayer):
                continue
            trade = other._find_trade_target(city_objects, board, players)
            if trade and trade[0] is self:
                _, meeting_city, _ = trade
                if self.city != meeting_city:
                    path = bfs_path(self.city, meeting_city, city_objects)
                    if path:
                        self.drive_ferry(path[0], city_objects)
                        return True
                break

        for colour in COLOURS:
            idx = COLOUR_INDEX[colour]
            if not board.eradicated[idx] and current.virus[idx] == 3:
                self.treat_disease(colour, city_objects, board)
                return True

        for neighbour_name in current.connections:
            neighbour = city_objects[neighbour_name]
            for colour in COLOURS:
                idx = COLOUR_INDEX[colour]
                if not board.eradicated[idx] and neighbour.virus[idx] == 3:
                    self.drive_ferry(neighbour_name, city_objects)
                    return True

        for colour in COLOURS:
            idx = COLOUR_INDEX[colour]
            if not board.eradicated[idx] and current.virus[idx] > 0:
                self.treat_disease(colour, city_objects, board)
                return True

        _, path = nearest_city_with_cubes(self.city, city_objects, board)
        if path:
            self.drive_ferry(path[0], city_objects)
            return True

        return False