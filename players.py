import pygame
COLOUR_INDEX = {"Blue": 0, "Yellow": 1, "Black": 2, "Red": 3}
MAX_RESEARCH_STATIONS = 6

ROLE_ACCENT = {
    "Contingency_Planner": (100, 195, 250),
    "Operations_Expert": (170, 225, 105),
    "Dispatcher": (205, 125, 235),
    "Quarantine_Specialist": (50, 130, 58),
    "Medic": (255, 152, 0),
    "Researcher": (230, 185, 125),
    "Scientist": (200, 55, 55),
}
DARK_BG = (26, 32, 44)
CARD_BG = (40, 52, 70)
TEXT_WHITE = (240, 244, 248)
TEXT_MUTED = (160, 174, 192)


class Player:
    def __init__(self, name, colour, total, city_cards, board):
        self.cards = []
        self.name = name
        self.city = "Atlanta"
        self.colour = colour
        self.actions = 4
        self.require_to_cure = 5
        self.operations = False
        self.avatar_idx = None

        for _ in range (6-total):
            self.draw_cards(city_cards, board)

        
    def draw_cards(self, city_cards, board):
        if len(self.cards) == 7:
            self.cards.pop(0)
        
        if len(self.cards) < 7:
            drawn_card = city_cards.pop()
            if drawn_card == "Infection Card":
                board.epidemic_count += 1
                board.infection_rate = board.infection_rate_track[min(board.epidemic_count, len(board.infection_rate_track) - 1)]
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
            if current and idx is not None and current.virus[idx] > 0:
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
            if current and idx is not None and current.virus[idx] > 0:
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


def draw_action_button(screen, rect, label, enabled, accent, hover, tinyGunfont):
    if not enabled:
        bg = (30, 38, 52)
        border = (55, 65, 80)
        text_col = (80, 90, 105)
    elif hover:
        bg = (min(accent[0]//2+40, 255), min(accent[1]//2+40, 255), min(accent[2]//2+40, 255))
        border = accent
        text_col = (255, 255, 255)
    else:
        bg = (accent[0]//3, accent[1]//3, accent[2]//3)
        border = (accent[0]//2+20, accent[1]//2+20, accent[2]//2+20)
        text_col = (200, 210, 220)

    pygame.draw.rect(screen, bg, rect, border_radius=7)
    pygame.draw.rect(screen, border, rect, 2, border_radius=7)
    shine_surf = pygame.Surface((rect.width - 4, rect.height // 3), pygame.SRCALPHA)
    shine_surf.fill((255, 255, 255, 18 if enabled else 6))
    screen.blit(shine_surf, (rect.x + 2, rect.y + 2))
    txt = tinyGunfont.render(label, True, text_col)
    screen.blit(txt, txt.get_rect(center=rect.center))


def draw_players(screen, players, city_objects, turn, num_players):
    current_idx = turn % num_players
    pawn_w, gap = 15, 6
    total_w = num_players * pawn_w + (num_players - 1) * gap
    start_x = -total_w // 2 + pawn_w // 2
    for i in range(num_players):
        p = players[i]
        x, y = city_objects[p.city].location
        offset_x = x + start_x + i * (pawn_w + gap)
        offset_y = y + 30
        fill = ROLE_ACCENT.get(type(p).__name__, (80, 120, 160))
        r = pygame.Rect(offset_x, offset_y, 15, 15)
        pygame.draw.rect(screen, fill, r, border_radius=3)
        border_w = 2 if i == current_idx else 1
        border_color = (255, 255, 255) if i == current_idx else (55, 70, 90)
        pygame.draw.rect(screen, border_color, r, border_w, border_radius=3)


def _blit_avatar_circle(screen, avatar_surf, center, radius):
    import pygame
    if avatar_surf is None:
        return
    size = int(radius * 2)
    if size <= 0:
        return
    avatar = pygame.transform.smoothscale(avatar_surf, (size, size))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
    avatar.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(avatar, (int(center[0] - radius), int(center[1] - radius)))


def draw_current_player_panel(screen, players, city_objects, board, turn, num_players, width, height, tinyGunfont, cityfont, get_colour_fn, dispatcher_occupied_mode=False, dispatcher_occupied_pawn=None, avatar_surfaces=None):
    panel_x = width - 200
    panel_width = 200
    mouse_pos = pygame.mouse.get_pos()

    pygame.draw.rect(screen, DARK_BG, (panel_x, 0, panel_width, height))
    active_player = players[turn % num_players]
    accent = ROLE_ACCENT.get(type(active_player).__name__, (80, 120, 160))

    pygame.draw.rect(screen, (accent[0]//2, accent[1]//2, accent[2]//2), (panel_x, 0, 2, height))
    header_rect = pygame.Rect(panel_x, 0, panel_width, 70)
    pygame.draw.rect(screen, (accent[0]//4, accent[1]//4, accent[2]//4), header_rect)
    pygame.draw.rect(screen, accent, pygame.Rect(panel_x, 68, panel_width, 2))

    screen.blit(tinyGunfont.render(active_player.name, True, TEXT_WHITE), (panel_x + 12, 10))
    role_name = type(active_player).__name__.replace("_", " ")
    screen.blit(tinyGunfont.render(role_name, True, accent), (panel_x + 12, 36))
    if avatar_surfaces is not None and getattr(active_player, "avatar_idx", None) is not None:
        idx = active_player.avatar_idx
        if isinstance(idx, int) and 0 <= idx < len(avatar_surfaces):
            av_cx, av_cy, av_r = panel_x + panel_width - 34, 35, 20
            pygame.draw.circle(screen, (30, 40, 55), (av_cx, av_cy), av_r)
            pygame.draw.circle(screen, accent, (av_cx, av_cy), av_r, 2)
            _blit_avatar_circle(screen, avatar_surfaces[idx], (av_cx, av_cy), av_r - 3)

    pip_y = 82
    screen.blit(cityfont.render("ACTIONS", True, TEXT_MUTED), (panel_x + 12, pip_y))
    for pip_i in range(4):
        pip_rect = pygame.Rect(panel_x + 12 + pip_i * 26, pip_y + 16, 20, 10)
        filled = pip_i < active_player.actions
        pygame.draw.rect(screen, accent if filled else (40, 50, 65), pip_rect, border_radius=3)
        if filled:
            pygame.draw.rect(screen, (255, 255, 255), pip_rect, 1, border_radius=3)

    screen.blit(cityfont.render("CARDS", True, TEXT_MUTED), (panel_x + 12, 118))
    card_w, card_h, card_gap, card_start_y = 170, 46, 6, 136
    for i, card in enumerate(active_player.cards):
        crect = pygame.Rect(panel_x + 14, card_start_y + i * (card_h + card_gap), card_w, card_h)
        pygame.draw.rect(screen, CARD_BG, crect, border_radius=6)
        top_colour = get_colour_fn(city_objects[card].colour) if card in city_objects else (100, 120, 140)
        pygame.draw.rect(screen, top_colour, pygame.Rect(crect.x, crect.y, card_w, 8), border_radius=6)
        pygame.draw.rect(screen, (55, 70, 90), crect, 1, border_radius=6)
        screen.blit(cityfont.render(str(card), True, TEXT_WHITE), (crect.x + 8, crect.y + 16))

    btn_w, btn_h, btn_gap_y = 170, 36, 8
    btn_x = panel_x + 14
    current_city = city_objects[active_player.city]

    can_treat = any(v > 0 for v in current_city.virus)
    can_build = active_player.city in active_player.cards and not current_city.research_center
    colour_counts = {}
    for c in active_player.cards:
        if c in city_objects:
            col = city_objects[c].colour
            colour_counts[col] = colour_counts.get(col, 0) + 1
    can_cure = current_city.research_center and any(
        count >= active_player.require_to_cure and not board.cures[["Blue","Yellow","Black","Red"].index(col)]
        for col, count in colour_counts.items()
    )
    can_share = bool([p for p in players if p != active_player and p.city == active_player.city])
    can_skip = active_player.actions > 0

    buttons = [
        ("treat", "TREAT", can_treat),
        ("build", "BUILD RC", can_build),
        ("cure", "CURE", can_cure),
        ("share", "SHARE", can_share),
        ("skip", "SKIP", can_skip),
    ]
    if isinstance(active_player, Dispatcher) and active_player.actions > 0:
        has_other = any(p != active_player for p in players)
        buttons.append(("dispatcher_occupy", "OCCUPY", has_other))

    div_y = height - 230 if len(buttons) <= 5 else height - 275
    pygame.draw.rect(screen, (45, 57, 75), pygame.Rect(panel_x + 10, div_y, panel_width - 20, 1))
    btn_start_y = div_y + 10

    action_buttons = {}
    for idx, (key, label, enabled) in enumerate(buttons):
        brect = pygame.Rect(btn_x, btn_start_y + idx * (btn_h + btn_gap_y), btn_w, btn_h)
        action_buttons[key] = brect
        hover = brect.collidepoint(mouse_pos) and enabled
        btn_accent = (90, 100, 115) if key == "skip" else accent
        draw_action_button(screen, brect, label, enabled, btn_accent, hover, tinyGunfont)

    if isinstance(active_player, Dispatcher):
        mode_y = btn_start_y + len(buttons) * (btn_h + btn_gap_y) + 6
        if dispatcher_occupied_mode and dispatcher_occupied_pawn is not None:
            mode_txt = tinyGunfont.render(f"Move {dispatcher_occupied_pawn.name} \u2192 city w/ pawn", True, accent)
            screen.blit(mode_txt, (btn_x, mode_y))
        elif dispatcher_occupied_mode:
            mode_txt = tinyGunfont.render("Select a player to move", True, accent)
            screen.blit(mode_txt, (btn_x, mode_y))

    return action_buttons


def player_cards_display(screen, players, city_objects, width, height, smallGunfont, cityfont, get_colour_fn, avatar_surfaces=None):
    import pygame
    screen.fill(DARK_BG)
    card_width, card_height, card_spacing = 120, 70, 12
    cards_per_row, panel_pad, title_bar_h, avatar_r, top_header = 4, 24, 52, 44, 80
    mouse_pos = pygame.mouse.get_pos()

    title_surf = smallGunfont.render("PLAYER CARDS", True, TEXT_MUTED)
    screen.blit(title_surf, (width // 2 - title_surf.get_width() // 2, 24))

    for i, player in enumerate(players):
        px = (i % 2) * (width // 2)
        py = top_header + (i // 2) * ((height - top_header) // 2)
        pw, ph = width // 2, (height - top_header) // 2
        accent = ROLE_ACCENT.get(type(player).__name__, (80, 120, 160))

        panel_rect = pygame.Rect(px+panel_pad, py+panel_pad+36, pw-2*panel_pad, ph-2*panel_pad-36)
        pygame.draw.rect(screen, CARD_BG, panel_rect, border_radius=12)
        pygame.draw.rect(screen, (accent[0]//2, accent[1]//2, accent[2]//2), panel_rect, 2, border_radius=12)

        bar_rect = pygame.Rect(px+panel_pad, py+panel_pad+36, pw-2*panel_pad, title_bar_h)
        pygame.draw.rect(screen, accent, bar_rect)
        avatar_cx = px + panel_pad + 12 + avatar_r
        avatar_cy = py + panel_pad + 36 + title_bar_h // 2
        pygame.draw.circle(screen, (30, 40, 55), (int(avatar_cx), int(avatar_cy)), avatar_r)
        pygame.draw.circle(screen, accent, (int(avatar_cx), int(avatar_cy)), avatar_r, 3)
        if avatar_surfaces is not None and getattr(player, "avatar_idx", None) is not None:
            idx = player.avatar_idx
            if isinstance(idx, int) and 0 <= idx < len(avatar_surfaces):
                _blit_avatar_circle(screen, avatar_surfaces[idx], (avatar_cx, avatar_cy), avatar_r - 4)

        role_name = type(player).__name__.replace("_", " ")
        role_txt = smallGunfont.render(role_name.upper(), True, (255, 255, 255))
        screen.blit(role_txt, role_txt.get_rect(midleft=(int(avatar_cx)+avatar_r+14, bar_rect.centery)))

        total_cards = len(player.cards)
        if total_cards > 0:
            start_y = py + panel_pad + 36 + title_bar_h + 20
            row_width = min(total_cards, cards_per_row) * (card_width + card_spacing) - card_spacing
            start_x = px + (pw - row_width) // 2
            for j, card in enumerate(player.cards):
                row, col = j // cards_per_row, j % cards_per_row
                rect = pygame.Rect(start_x + col*(card_width+card_spacing), start_y + row*(card_height+card_spacing), card_width, card_height)
                if rect.collidepoint(mouse_pos):
                    rect = rect.inflate(4, 4)
                top_colour = get_colour_fn(city_objects[card].colour) if card in city_objects else (100, 120, 140)
                pygame.draw.rect(screen, (55, 70, 90), rect, border_radius=10)
                pygame.draw.rect(screen, top_colour, pygame.Rect(rect.x, rect.y, rect.width, 16), border_radius=10)
                pygame.draw.rect(screen, accent, rect, 2, border_radius=10)
                screen.blit(cityfont.render(str(card), True, TEXT_WHITE), (rect.x+10, rect.y+26))
        else:
            no_cards = cityfont.render("No city cards", True, TEXT_MUTED)
            screen.blit(no_cards, (px + pw//2 - no_cards.get_width()//2, py + panel_pad + 36 + title_bar_h + 80))


def draw_share_popup(screen, share_popup, players, turn, width, height, smallGunfont, tinyGunfont):
    import pygame
    if share_popup is None:
        return share_popup

    mx, my = pygame.mouse.get_pos()
    active_player = players[turn % len(players)]
    accent = ROLE_ACCENT.get(type(active_player).__name__, (80, 120, 160))

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    others = [p for p in players if p != active_player and p.city == active_player.city]
    row_h, pop_w = 90, 460
    pop_h = 150 + len(others) * row_h
    board_cx = (width - 200) // 2
    pop_x = board_cx - pop_w // 2
    pop_y = height // 2 - pop_h // 2
    pop_rect = pygame.Rect(pop_x, pop_y, pop_w, pop_h)

    pygame.draw.rect(screen, DARK_BG, pop_rect, border_radius=12)
    pygame.draw.rect(screen, accent, pop_rect, 2, border_radius=12)
    title = smallGunfont.render("SHARE KNOWLEDGE", True, TEXT_WHITE)
    screen.blit(title, title.get_rect(centerx=pop_rect.centerx, top=pop_y+18))

    share_popup["rects"] = {}
    btn_w, btn_h, btn_gap = 180, 44, 16
    btn_start_x = pop_x + pop_w//2 - (btn_w*2+btn_gap)//2
    row_start_y = pop_y + 72

    for i, other in enumerate(others):
        other_accent = ROLE_ACCENT.get(type(other).__name__, (80, 120, 160))
        name_surf = tinyGunfont.render(other.name, True, other_accent)
        screen.blit(name_surf, name_surf.get_rect(centerx=pop_rect.centerx, top=row_start_y+i*row_h+8))

        can_give_cards = list(active_player.cards) if isinstance(active_player, Researcher) else \
                         ([active_player.city] if active_player.city in active_player.cards else [])
        can_take_cards = [active_player.city] if active_player.city in other.cards else []

        give_rect = pygame.Rect(btn_start_x, row_start_y+i*row_h+38, btn_w, btn_h)
        take_rect = pygame.Rect(btn_start_x+btn_w+btn_gap, row_start_y+i*row_h+38, btn_w, btn_h)

        draw_action_button(screen, give_rect, "GIVE CARD", bool(can_give_cards), accent, give_rect.collidepoint(mx,my) and bool(can_give_cards), tinyGunfont)
        draw_action_button(screen, take_rect, "TAKE CARD", bool(can_take_cards), accent, take_rect.collidepoint(mx,my) and bool(can_take_cards), tinyGunfont)

        share_popup["rects"][f"give_{i}"] = (give_rect, other, can_give_cards, True)
        share_popup["rects"][f"take_{i}"] = (take_rect, other, can_take_cards, False)

    cancel_rect = pygame.Rect(pop_rect.centerx-60, pop_y+pop_h-54, 120, 36)
    draw_action_button(screen, cancel_rect, "CANCEL", True, (100,100,110), cancel_rect.collidepoint(mx,my), tinyGunfont)
    share_popup["rects"]["cancel"] = (cancel_rect, None, None, None)
    return share_popup


def draw_occupy_popup(screen, occupy_popup, players, turn, width, height, tinyGunfont):
    import pygame
    if occupy_popup is None:
        return occupy_popup

    mx, my = pygame.mouse.get_pos()
    active_player = players[turn % len(players)]
    accent = ROLE_ACCENT.get(type(active_player).__name__, (80, 120, 160))

    others = [p for p in players if p != active_player]
    row_h, pop_w = 72, 380
    pop_h = 140 + len(others) * row_h
    board_cx = (width - 200) // 2
    pop_x = board_cx - pop_w // 2
    pop_y = height // 2 - pop_h // 2
    pop_rect = pygame.Rect(pop_x, pop_y, pop_w, pop_h)

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    pygame.draw.rect(screen, DARK_BG, pop_rect, border_radius=12)
    pygame.draw.rect(screen, accent, pop_rect, 2, border_radius=12)

    title = tinyGunfont.render("SELECT PAWN TO MOVE", True, TEXT_WHITE)
    screen.blit(title, title.get_rect(centerx=pop_rect.centerx, top=pop_y + 22))

    occupy_popup["rects"] = {}
    btn_w, btn_h = 200, 40
    row_start_y = pop_y + 64
    for i, other in enumerate(others):
        other_accent = ROLE_ACCENT.get(type(other).__name__, (80, 120, 160))
        name_surf = tinyGunfont.render(other.name, True, other_accent)
        screen.blit(name_surf, name_surf.get_rect(centerx=pop_rect.centerx, top=row_start_y + i * row_h + 4))
        btn_rect = pygame.Rect(pop_rect.centerx - btn_w // 2, row_start_y + i * row_h + 28, btn_w, btn_h)
        draw_action_button(screen, btn_rect, "MOVE THIS PAWN", True, other_accent, btn_rect.collidepoint(mx, my), tinyGunfont)
        occupy_popup["rects"][f"player_{i}"] = (btn_rect, other)

    cancel_rect = pygame.Rect(pop_rect.centerx - 60, pop_y + pop_h - 50, 120, 36)
    draw_action_button(screen, cancel_rect, "CANCEL", True, (100, 100, 110), cancel_rect.collidepoint(mx, my), tinyGunfont)
    occupy_popup["rects"]["cancel"] = (cancel_rect, None)
    return occupy_popup


def draw_discard_popup(screen, discard_popup, city_objects, width, height, smallGunfont, tinyGunfont, cityfont, get_colour_fn):
    import math, pygame
    if discard_popup is None:
        return discard_popup

    mx, my = pygame.mouse.get_pos()
    player = discard_popup["player"]
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    n_cards = len(player.cards)
    board_cx = (width - 200) / 2
    max_pop_w, card_gap, pad = 860, 10, 32
    per_row = min(n_cards, max(1, (max_pop_w - pad*2 + card_gap) // (100 + card_gap)))
    rows = math.ceil(n_cards / per_row)
    card_w = min(100, (max_pop_w - pad*2 - card_gap*(per_row-1)) // per_row)
    card_h = int(card_w * 1.1)
    pop_w = pad*2 + per_row*card_w + (per_row-1)*card_gap
    title_h, row_h = 66, card_h + card_gap
    pop_h = title_h + rows*row_h + pad
    pop_x = board_cx - pop_w // 2
    pop_y = height // 2 - pop_h // 2
    pop_rect = pygame.Rect(pop_x, pop_y, pop_w, pop_h)

    pygame.draw.rect(screen, DARK_BG, pop_rect, border_radius=12)
    pygame.draw.rect(screen, (200, 60, 60), pop_rect, 2, border_radius=12)
    over = n_cards - 7
    msg = f"{player.name}: DISCARD {over} CARD{'S' if over > 1 else ''}"
    title = smallGunfont.render(msg, True, (220, 80, 80))
    screen.blit(title, title.get_rect(centerx=pop_rect.centerx, top=pop_y+14))
    pygame.draw.rect(screen, (60, 40, 40), pygame.Rect(pop_x+20, pop_y+title_h-4, pop_w-40, 1))

    cards_start_x, cards_start_y = pop_x + pad, pop_y + title_h + 4
    discard_popup["card_rects"] = []

    for i, card in enumerate(player.cards):
        row, col = i // per_row, i % per_row
        cx = cards_start_x + col * (card_w + card_gap)
        cy = cards_start_y + row * row_h
        crect = pygame.Rect(cx, cy, card_w, card_h)
        hover = crect.collidepoint(mx, my)
        top_colour = get_colour_fn(city_objects[card].colour) if card in city_objects else (100, 120, 140)

        pygame.draw.rect(screen, (70,85,105) if hover else CARD_BG, crect, border_radius=7)
        pygame.draw.rect(screen, top_colour, pygame.Rect(cx, cy, card_w, 10), border_radius=7)
        pygame.draw.rect(screen, (220,80,80) if hover else (55,70,90), crect, 2, border_radius=7)

        words, lines, line = card.split(), [], ""
        for w in words:
            test = (line + " " + w).strip()
            if cityfont.size(test)[0] <= card_w - 8:
                line = test
            else:
                if line: lines.append(line)
                line = w
        if line: lines.append(line)
        for li, ltext in enumerate(lines[:3]):
            ls = cityfont.render(ltext, True, TEXT_WHITE)
            screen.blit(ls, ls.get_rect(centerx=crect.centerx, top=crect.y+14+li*14))
        if hover:
            xs = tinyGunfont.render("DISCARD", True, (220, 80, 80))
            screen.blit(xs, xs.get_rect(centerx=crect.centerx, bottom=crect.bottom-5))

        discard_popup["card_rects"].append((crect, card))

    return discard_popup