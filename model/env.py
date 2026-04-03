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
from players import Player, Medic, Scientist, Researcher, Operations_Expert, Dispatcher, Quarantine_Specialist, Contingency_Planner, COLOUR_INDEX

#static values from our pandemic game
CITY_NAMES = sorted(city_list.keys())
CITY_INDEX = {n: i for i, n in enumerate(CITY_NAMES)}
NUM_CITIES = len(CITY_NAMES)
NUM_COLOURS = 4
NUM_ACTIONS = NUM_CITIES + NUM_COLOURS + 1 + NUM_COLOURS + 1
COLOUR_ORDER = ["Blue", "Yellow", "Black", "Red"]

class PandemicEnv(gym.Env):

    #initialize the game environment
    def __init__(self, difficulty=0, num_players=2):
        super().__init__()
        self.difficulty = difficulty
        self.num_players = num_players
        self.board = None
        self.turn = None
        self.players = None
        self.city_objects = None

        observation_size = NUM_CITIES*7+NUM_COLOURS+3 
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

        #where is the active player
        for city_name in CITY_NAMES:
            obs.append(1.0 if active_player.city == city_name else 0.0)

        #what cards the player has
        for city_name in CITY_NAMES:
            obs.append(1.0 if city_name in active_player.cards else 0.0)

        #cures, outbreak counter, infection rates, actions left
        for cure in self.board.cures:
            obs.append(1.0 if cure else 0.0)

        obs.append(self.board.outbreak_counter / 8.0)
        obs.append(self.board.infection_rate / 4.0)
        obs.append(active_player.actions / 4.0)

        return np.array(obs, dtype=np.float32)

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

        role_classes = [
            Medic, 
            Scientist, 
            Researcher, 
            Dispatcher, 
            Contingency_Planner, 
            Operations_Expert, 
            Quarantine_Specialist
            ]

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
        
        #tells the outcome of the training
        terminated = False
        outcome = None
        if all(self.board.cures):
            terminated, outcome = True, "win"
        elif self.board.outbreak_counter >= 8:
            terminated, outcome = True, "lose_outbreaks"
        elif not self.board.city_cards:
            terminated, outcome = True, "lose_cards"
        else:
            for idx in range(NUM_COLOURS):
                if sum(self.city_objects[n].virus[idx] for n in self.city_objects) > 24:
                    terminated, outcome = True, "lose_cubes"
                    break

        if terminated:
            reward += 50.0 if outcome == "win" else -25.0

        return self._get_obs(), reward, terminated, False, self._get_info()


