"""created the learning environment"""

#imports
import sys, os
import gymnasium as gym
import numpy as np
import random
from gymnasium import spaces
from unittest.mock import MagicMock
sys.modules["pygame"] = MagicMock()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cities import city_list, City
from board import Board
from players import Medic, Scientist, Researcher, Operations_Expert, Dispatcher, Quarantine_Specialist, Contingency_Planner

#static values from our pandemic game
CITY_NAMES = sorted(city_list.keys())
CITY_INDEX = {n: i for i, n in enumerate(CITY_NAMES)}
NUM_CITIES = len(CITY_NAMES)
NUM_COLOURS = 4
NUM_ACTIONS = NUM_CITIES + NUM_COLOURS + 1 + NUM_COLOURS + 1
COLOUR_ORDER = ["Blue", "Yellow", "Black", "Red"]

ROLE_CLASSES = [
    Medic,
    Scientist,
    Researcher,
    Dispatcher,
    Contingency_Planner,
    Operations_Expert,
    Quarantine_Specialist,
]
ROLE_ORDER = [cls.__name__ for cls in ROLE_CLASSES]
NUM_ROLES = len(ROLE_ORDER)

class PandemicEnv(gym.Env):

    #initialize the game environment
    def __init__(self, difficulty=0, num_players=2, max_episode_steps=None):
        super().__init__()
        self.difficulty = difficulty
        self.num_players = num_players
        self.max_episode_steps = max_episode_steps
        self._elapsed_steps = 0
        self.board = None
        self.turn = None
        self.players = None
        self.city_objects = None

        # Upper bound for player deck size at game setup (all city cards + epidemic inserts).
        self._max_player_deck = float(NUM_CITIES + int(self.difficulty) + 4)

        observation_size = (
            NUM_COLOURS * NUM_CITIES
            + NUM_CITIES
            + self.num_players * NUM_CITIES
            + NUM_CITIES
            + NUM_COLOURS
            + 3
            + NUM_ROLES
            + 1
        )
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(observation_size,), dtype=np.float32)
        self.action_space = spaces.Discrete(NUM_ACTIONS)

    def _get_obs(self):
        obs = []
        active_player = self.players[self.turn % len(self.players)]

        #the virus count of each colour per city
        for colour_idx in range(NUM_COLOURS):
            for city_name in CITY_NAMES:
                obs.append(self.city_objects[city_name].virus[colour_idx] / 3.0)

        #where are the research centers 
        for city_name in CITY_NAMES:
            obs.append(1.0 if self.city_objects[city_name].research_center else 0.0)

        # pawn positions for every player (seat order matches self.players)
        for p in self.players:
            for city_name in CITY_NAMES:
                obs.append(1.0 if p.city == city_name else 0.0)

        # city cards in active player's hand (counts, max hand size 7 in rules)
        for city_name in CITY_NAMES:
            count = sum(1 for c in active_player.cards if c == city_name)
            obs.append(min(count, 7) / 7.0)

        #cures, outbreak counter, infection rates, actions left
        for cure in self.board.cures:
            obs.append(1.0 if cure else 0.0)

        obs.append(self.board.outbreak_counter / 8.0)
        obs.append(self.board.infection_rate / 4.0)
        obs.append(active_player.actions / 4.0)

        role_name = type(active_player).__name__
        for name in ROLE_ORDER:
            obs.append(1.0 if role_name == name else 0.0)

        obs.append(len(self.board.city_cards) / self._max_player_deck)

        return np.array(obs, dtype=np.float32)

    def terminal_outcome(self):
        """If the game is in a terminal state, return outcome label; else None."""
        if self.board is None or self.city_objects is None:
            return None
        if all(self.board.cures):
            return "win"
        if self.board.outbreak_counter >= 8:
            return "lose_outbreaks"
        if not self.board.city_cards:
            return "lose_cards"
        for idx in range(NUM_COLOURS):
            if sum(self.city_objects[n].virus[idx] for n in self.city_objects) > 24:
                return "lose_cubes"
        return None

    def _get_info(self):
        return {
        "outbreaks": self.board.outbreak_counter,
        "cures_found": sum(self.board.cures),
        "cards_left": len(self.board.city_cards),
        "player_city": self.players[self.turn % len(self.players)].city,
        }
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        #create a new game
        self.city_objects = {}
        for name, data in city_list.items():
            self.city_objects[name] = City(
                name=name,
                connections=data["connections"],
                colour=data["colour"],
                location=data["location"]
            )
        self.city_objects["Atlanta"].research_center = True

        role_classes = list(ROLE_CLASSES)
        random.shuffle(role_classes)

        self.board = Board(self.city_objects, self.difficulty)
        self.board.set_board(self.city_objects)

        self.players = []
        for i in range(self.num_players):
            new_player = role_classes[i](
                name=f"Player {i+1}",
                colour=(0,0,0),
                total=self.num_players,
                city_cards = self.board.city_cards,
                board=self.board
            )
            self.players.append(new_player)
        self.board.add_epidemic_card()
        self.turn = 0
        self._elapsed_steps = 0

        return self._get_obs(), self._get_info()


    def step(self, action):
        active_player = self.players[self.turn % len(self.players)]
        reward = -0.01

        #board summary
        prev_cures = sum(self.board.cures)
        prev_outbreaks = self.board.outbreak_counter

        valid = False
        current = self.city_objects[active_player.city]

        #player movements
        if action < NUM_CITIES:
            target = CITY_NAMES[action]
            if target in current.connections:
                active_player.drive_ferry(target, self.city_objects)
                valid = True
            elif target in active_player.cards:
                active_player.direct_flight(target, self.city_objects, self.board)
                valid = True
            elif active_player.city in active_player.cards:
                active_player.charter_flight(target, self.city_objects, self.board)
                valid = True
            elif current.research_center and self.city_objects[target].research_center:
                active_player.shuttle_flight(target, self.city_objects)
                valid = True

        #player curing
        elif action < NUM_CITIES + NUM_COLOURS:
            colour_idx = action - NUM_CITIES
            colour = COLOUR_ORDER[colour_idx]
            if not self.board.cures[colour_idx]:
                matching = [c for c in active_player.cards if c in self.city_objects and self.city_objects[c].colour == colour]
                if len(matching) >= active_player.require_to_cure and current.research_center:
                    active_player.discover_cure(colour, matching[:active_player.require_to_cure], self.city_objects, self.board)
                    reward += 1.0
                    valid = True

        #player bulding research station
        elif action == NUM_CITIES + NUM_COLOURS:
            before = sum(1 for c in self.city_objects.values() if c.research_center)
            active_player.build_research_station(self.city_objects, self.board)
            valid = sum(1 for c in self.city_objects.values() if c.research_center) > before

        #player treating
        elif action < NUM_CITIES + NUM_COLOURS + 1 + NUM_COLOURS:
            colour_idx = action - (NUM_CITIES + NUM_COLOURS + 1)
            colour = COLOUR_ORDER[colour_idx]
            if current.virus[colour_idx] > 0:
                active_player.treat_disease(colour, self.city_objects, self.board)
                valid = True

        #skipping turn
        else:
            if active_player.actions > 0:
                active_player.actions -= 1
                valid = True

        #punishing bad moves or impossible moves
        if not valid:
            reward -= 0.05

        if sum(self.board.cures) > prev_cures:
            reward += 100.0
        if self.board.outbreak_counter > prev_outbreaks:
            reward -= 0.5

        #infect cities after each turn like the regular game
        if active_player.actions <= 0:
            for i in range (2):
                if not self.board.city_cards:
                    break
                drawn = self.board.city_cards.pop()
                if drawn == "Infection Card":
                    self.board.epidemic_count += 1
                    self.board.infection_rate = self.board.infection_rate_track[
                        min(self.board.epidemic_count, len(self.board.infection_rate_track) - 1)
                    ]
                    self.board.shuffle_infection_deck()
                else:
                    active_player.cards.append(drawn)
                    while len(active_player.cards) > 7:
                        active_player.cards.pop(0)
            self.board.infect_virus(self.city_objects, self.players)
            active_player.actions = 4
            self.turn += 1
        
        outcome = self.terminal_outcome()
        terminated = outcome is not None

        if terminated:
            reward += 50.0 if outcome == "win" else -25.0

        self._elapsed_steps += 1
        truncated = False
        if (
            self.max_episode_steps is not None
            and self._elapsed_steps >= self.max_episode_steps
            and not terminated
        ):
            truncated = True

        return self._get_obs(), reward, terminated, truncated, self._get_info()


