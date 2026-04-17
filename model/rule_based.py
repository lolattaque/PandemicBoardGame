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

def nearest_city_with_colour(start, colour, city_objects):
    idx = COLOUR_INDEX[colour]
    if city_objects[start].virus[idx] > 0:
        return start, []
    visited = {start}
    queue = deque([(start, [])])
    while queue:
        city_name, path = queue.popleft()
        for neighbour in city_objects[city_name].connections:
            if neighbour not in visited:
                new_path = path + [neighbour]
                if city_objects[neighbour].virus[idx] > 0:
                    return neighbour, new_path
                visited.add(neighbour)
                queue.append((neighbour, new_path))
    return None, []

def cubes_remaining(colour, city_objects):
    idx = COLOUR_INDEX[colour]
    on_board = sum(city_objects[n].virus[idx] for n in city_objects)
    return 24 - on_board

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._city_objects_ref = None
        self._players_ref = None

    def draw_cards(self, city_cards, board):
        if len(self.cards) >= 7:
            if self._city_objects_ref and self._players_ref:
                self.auto_discard(self._city_objects_ref, board, self._players_ref)
            else:
                self.cards.pop(0)

        if len(self.cards) < 7:
            drawn_card = city_cards.pop()
            if drawn_card == "Infection Card":
                board.epidemic_count += 1
                board.infection_rate = board.infection_rate_track[
                    min(board.epidemic_count, len(board.infection_rate_track) - 1)
                ]
                board.shuffle_infection_deck()
                self.draw_cards(city_cards, board)
            else:
                self.cards.append(drawn_card)

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

    def _colour_assignments(self, city_objects, board, players):
        assignments = {}
        for colour in COLOURS:
            idx = COLOUR_INDEX[colour]
            if board.cures[idx]:
                continue
            best_player = max(
                players,
                key=lambda p, col=colour: sum(
                    1 for c in p.cards if city_objects.get(c) and city_objects[c].colour == col
                ) / (4 if isinstance(p, Scientist) else 5)
            )
            assignments[colour] = best_player
        return assignments

    def _my_assigned_colours(self, city_objects, board, players):
        return {c for c, p in self._colour_assignments(city_objects, board, players).items() if p is self}

    def _find_trade_target(self, city_objects, board, players):
        require = self._require_to_cure()
        colour_cards = self._cure_colour_cards(city_objects, board)
        assignments = self._colour_assignments(city_objects, board, players)
        my_colours = self._my_assigned_colours(city_objects, board, players)

        for colour in my_colours:
            my_count = len(colour_cards[colour])
            if my_count >= require:
                continue
            for partner in players:
                if partner is self:
                    continue
                useful = [
                    c for c in partner.cards
                    if city_objects.get(c) and city_objects[c].colour == colour
                ]
                if not useful:
                    continue
                if isinstance(partner, Researcher):
                    return (partner, partner.city, useful[0], False)
                else:
                    best_card = min(
                        useful,
                        key=lambda c: len(bfs_path(self.city, c, city_objects))
                    )
                    return (partner, best_card, best_card, False)

        for card in self.cards:
            city = city_objects.get(card)
            if not city:
                continue
            colour = city.colour
            idx = COLOUR_INDEX[colour]
            if board.cures[idx]:
                continue
            if colour in my_colours:
                continue
            assignee = assignments.get(colour)
            if assignee is None or assignee is self:
                continue
            assignee_count = sum(
                1 for c in assignee.cards if city_objects.get(c) and city_objects[c].colour == colour
            )
            assignee_require = 4 if isinstance(assignee, Scientist) else 5
            if assignee_count >= assignee_require:
                continue

            if isinstance(self, Researcher):
                return (assignee, assignee.city, card, True)
            else:
                return (assignee, card, card, True)

        return None

    def _use_event_cards(self, city_objects, board, players):
        require = self._require_to_cure()
        colour_cards = self._cure_colour_cards(city_objects, board)

        if "One Quiet Night" in self.cards:
            threat_cities = sum(
                1 for city in city_objects.values()
                if any(city.virus[i] == 3 and not board.eradicated[i] for i in range(4))
            )
            if board.outbreak_counter >= 5 or threat_cities >= 3:
                self.use_event_card("One Quiet Night", board, city_objects, None, None)

        if "Government Grant" in self.cards:
            for p in players:
                p_colour_cards = {}
                for card in p.cards:
                    city = city_objects.get(card)
                    if city:
                        p_colour_cards.setdefault(city.colour, []).append(card)
                p_require = 4 if isinstance(p, Scientist) else 5
                for colour, cards in p_colour_cards.items():
                    idx = COLOUR_INDEX[colour]
                    if not board.cures[idx] and len(cards) >= p_require:
                        _, path = nearest_research_station(p.city, city_objects)
                        if len(path) > 2 and p.city not in p.cards:
                            self.use_event_card("Government Grant", board, city_objects, p.city, None)
                            break

        if "Resilient Population" in self.cards:
            discard = board.infection_card_discard_pile
            if discard:
                best = max(
                    discard,
                    key=lambda c: sum(city_objects[c].virus) if c in city_objects else 0
                )
                if city_objects.get(best) and sum(city_objects[best].virus) >= 2:
                    self.use_event_card("Resilient Population", board, city_objects, best, None)

        if "Forecast" in self.cards:
            top_n = min(6, len(board.infection_cards))
            top = board.infection_cards[-top_n:]
            if any(city_objects.get(c) and sum(city_objects[c].virus) >= 2 for c in top):
                reordered = sorted(
                    top,
                    key=lambda c: sum(city_objects[c].virus) if city_objects.get(c) else 0
                )
                self.use_event_card("Forecast", board, city_objects, None, reordered)

        if "Airlift" in self.cards:
            for colour, cards in colour_cards.items():
                if len(cards) >= require:
                    station, path = nearest_research_station(self.city, city_objects)
                    if len(path) > 3 and station:
                        self.use_event_card("Airlift", board, city_objects, station, None)
                        break

    def auto_discard(self, city_objects, board, players=None):
        assignments = self._colour_assignments(city_objects, board, players) if players else {}
        my_colours = {c for c, p in assignments.items() if p is self} if players else set()

        if players:
            for card in list(self.cards):
                city = city_objects.get(card)
                if not city:
                    continue
                colour = city.colour
                idx = COLOUR_INDEX[colour]
                if board.cures[idx] or colour in my_colours:
                    continue
                assignee = assignments.get(colour)
                if assignee is None or assignee is self or assignee.city != self.city:
                    continue
                can_give = isinstance(self, Researcher) or card == self.city
                if can_give:
                    self.cards.remove(card)
                    assignee.cards.append(card)
                    return

        require = self._require_to_cure()
        colour_cards = self._cure_colour_cards(city_objects, board)

        def card_value(card):
            city = city_objects.get(card)
            if not city:
                return -1
            colour = city.colour
            idx = COLOUR_INDEX[colour]
            if board.cures[idx] or board.eradicated[idx]:
                return 0
            if colour in my_colours:
                my_count = len(colour_cards[colour])

                return 10 + my_count
            if players:
                assignee = assignments.get(colour)
                if assignee is not None and assignee is not self:
                    their_count = sum(
                        1 for c in assignee.cards
                        if city_objects.get(c) and city_objects[c].colour == colour
                    )
                    assignee_require = 4 if isinstance(assignee, Scientist) else 5
                    if their_count < assignee_require:
                        return 4 + their_count
            return 1

        worst_card = min(self.cards, key=card_value)
        self.cards.remove(worst_card)
        board.player_discard_pile.append(worst_card)

    def take_turn(self, city_objects, board, players):
        self._city_objects_ref = city_objects
        self._players_ref = players
        while self.actions > 0:
            taken = self._decide_action(city_objects, board, players)
            if not taken:
                break

    def _decide_action(self, city_objects, board, players):
        self._use_event_cards(city_objects, board, players)
        require = self._require_to_cure()
        colour_cards = self._cure_colour_cards(city_objects, board)
        current = city_objects[self.city]
        my_colours = self._my_assigned_colours(city_objects, board, players)

        for colour in COLOURS:
            idx = COLOUR_INDEX[colour]
            if board.eradicated[idx] or board.cures[idx]:
                continue
            if cubes_remaining(colour, city_objects) < 5:
                if current.virus[idx] > 0:
                    self.treat_disease(colour, city_objects, board)
                    return True
                city_name, path = nearest_city_with_colour(self.city, colour, city_objects)
                if city_name and path:
                    self.drive_ferry(path[0], city_objects)
                    return True

        for colour in my_colours:
            cards = colour_cards[colour]
            if len(cards) >= require:
                if current.research_center:
                    self.discover_cure(colour, cards[:require], city_objects, board)
                    return True
                _, station_path = nearest_research_station(self.city, city_objects)
                if self.city in self.cards and city_objects[self.city].colour != colour and not current.research_center:
                    self.build_research_station(city_objects, board)
                    return True
                if station_path:
                    self.drive_ferry(station_path[0], city_objects)
                    return True

        trade = self._find_trade_target(city_objects, board, players)
        if trade:
            partner, meeting_city, card, is_give = trade
            if self.city == meeting_city and partner.city == meeting_city:
                if is_give:
                    self.share_knowledge(partner, card, give=True, city_objects=city_objects)
                else:
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
                _, meeting_city, _, _ = trade
                if self.city != meeting_city:
                    path = bfs_path(self.city, meeting_city, city_objects)
                    if path:
                        self.drive_ferry(path[0], city_objects)
                        return True
                break

        for colour in my_colours:
            if len(colour_cards[colour]) >= require - 1:
                _, station_path = nearest_research_station(self.city, city_objects)
                if station_path:
                    self.drive_ferry(station_path[0], city_objects)
                    return True

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