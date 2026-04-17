# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 10:14:30 2026

@author: MosesLee
"""

import pygame
import random
import csv
import os
import numpy as np

from players import (
    Player, Medic, Scientist, Researcher, Operations_Expert, Dispatcher,
    Quarantine_Specialist, Contingency_Planner,
    ROLE_ACCENT, DARK_BG, CARD_BG, TEXT_WHITE, TEXT_MUTED,
    draw_players, draw_current_player_panel, player_cards_display,
    draw_share_popup, draw_occupy_popup, draw_discard_popup,
    draw_event_popup, draw_event_target_popup,
    EVENT_CARDS, EVENT_CARD_DESCS
)
from cities import City, city_list, draw_connections, draw_cities, draw_movement_highlights
from board import Board, draw_board, draw_outbreak_animations, draw_result_screen
from model.rule_based import AIPlayer

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.set_num_channels(16) 
largefont  = pygame.font.SysFont("arial", 60)
smallfont  = pygame.font.SysFont("arial", 40)
cityfont   = pygame.font.SysFont("arial", 12, bold=True)

largeGunfont  = pygame.font.Font("Gunplay.ttf", 100)
smallGunfont  = pygame.font.Font("Gunplay.ttf", 50)
tinyGunfont   = pygame.font.Font("Gunplay.ttf", 20)
avatar_footer_font = pygame.font.SysFont("arial", 32)

width, height = 1400, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pandemic Board Game")

board_img = pygame.image.load("image.png")
board_img = pygame.transform.scale(board_img, (width - 200, height))

SAVE_FILE = "pandemic_save.csv"
event_buttons = None



def make_tone(freq=440, duration=0.15, volume=0.4, wave="sine", sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    if wave == "sine":
        samples = np.sin(2 * np.pi * freq * t)
    elif wave == "square":
        samples = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "noise":
        samples = np.random.uniform(-1, 1, len(t))
  
    fade = np.linspace(1, 0, len(t))
    samples = (samples * fade * volume * 32767).astype(np.int16)
    stereo = np.column_stack([samples, samples])
    sound = pygame.sndarray.make_sound(stereo)
    return sound


SND_CLICK       = make_tone(600,  0.08, 0.3, "sine")        
SND_AVATAR_SEL  = make_tone(880,  0.12, 0.35, "sine")      

ROLE_CLASS_MAP = {
    "Player":                Player,
    "Medic":                 Medic,
    "Scientist":             Scientist,
    "Researcher":            Researcher,
    "Operations_Expert":     Operations_Expert,
    "Dispatcher":            Dispatcher,
    "Quarantine_Specialist": Quarantine_Specialist,
    "Contingency_Planner":   Contingency_Planner,
}


_ai_class_cache = {}

def make_ai_player_class(role_cls):
    if role_cls in _ai_class_cache:
        return _ai_class_cache[role_cls]
    ai_cls = type(f"{role_cls.__name__}", (AIPlayer, role_cls), {})
    _ai_class_cache[role_cls] = ai_cls
    return ai_cls

def convert_to_ai(player):
    ai_cls = make_ai_player_class(type(player))
    new_p = ai_cls.__new__(ai_cls)
    new_p.__dict__.update(player.__dict__)
    new_p._city_objects_ref = None
    new_p._players_ref = None
    return new_p

AVATAR_SHEET_PATH = "assets/avatars.png"

def _load_avatar_surfaces(sheet_path, cols=3, rows=3, target_px=92):
    sheet = pygame.image.load(sheet_path).convert_alpha()
    sw, sh = sheet.get_width(), sheet.get_height()
    tile_w, tile_h = sw // cols, sh // rows
    tiles = []
    for ry in range(rows):
        for cx in range(cols):
            rect = pygame.Rect(cx * tile_w, ry * tile_h, tile_w, tile_h)
            tile = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
            tile.blit(sheet, (0, 0), rect)
            tile = pygame.transform.smoothscale(tile, (target_px, target_px))
            tiles.append(tile)
    return tiles

    
avatar_surfaces       = _load_avatar_surfaces(AVATAR_SHEET_PATH, cols=3, rows=3, target_px=92)
avatar_surfaces_small = [pygame.transform.smoothscale(s, (64,  64))  for s in avatar_surfaces] if avatar_surfaces else []
avatar_surfaces_grid  = [pygame.transform.smoothscale(s, (116, 116)) for s in avatar_surfaces] if avatar_surfaces else []


city_objects = {}
for name, data in city_list.items():
    city_objects[name] = City(
        name=name,
        connections=data["connections"],
        colour=data["colour"],
        location=data["location"]
    )
city_objects["Atlanta"].research_center = True


def get_colour(colour_str):
    return {"Blue": (0,0,255), "Yellow": (150,150,0),
            "Black": (80,80,80), "Red": (255,0,0)}.get(colour_str, (255,255,255))

def _list_to_csv_cell(lst):
    """Encode a Python list as a pipe-separated string for one CSV cell."""
    return "|".join(str(x) for x in lst)

def _csv_cell_to_list(cell):
    """Decode a pipe-separated CSV cell back to a list of strings."""
    if not cell:
        return []
    return cell.split("|")


def save_game():
    """
    CSV layout – each row is  section, key, value
    Sections: META, BOARD, CITY_<name>, PLAYER_<i>
    """
    rows = []


    rows.append(["META", "turn",            str(turn)])
    rows.append(["META", "num_players",     str(num_players)])
    rows.append(["META", "selected_difficulty", str(selected_difficulty)])


    rows.append(["BOARD", "outbreak_counter",  str(Pandemic_Game.outbreak_counter)])
    rows.append(["BOARD", "epidemic_count",    str(Pandemic_Game.epidemic_count)])
    rows.append(["BOARD", "infection_rate",    str(Pandemic_Game.infection_rate)])
    rows.append(["BOARD", "cures",             _list_to_csv_cell(Pandemic_Game.cures)])
    rows.append(["BOARD", "eradicated",        _list_to_csv_cell(Pandemic_Game.eradicated)])
    rows.append(["BOARD", "city_cards",        _list_to_csv_cell(Pandemic_Game.city_cards)])
    rows.append(["BOARD", "infection_cards",   _list_to_csv_cell(Pandemic_Game.infection_cards)])
    rows.append(["BOARD", "infection_discard", _list_to_csv_cell(Pandemic_Game.infection_card_discard_pile)])
    rows.append(["BOARD", "player_discard",    _list_to_csv_cell(Pandemic_Game.player_discard_pile)])
    rows.append(["BOARD", "quiet_night",       str(int(getattr(Pandemic_Game, "quiet_night_active", False)))])


    for cname, city in city_objects.items():
        section = f"CITY_{cname}"
        rows.append([section, "virus",           _list_to_csv_cell(city.virus)])
        rows.append([section, "research_center", str(int(city.research_center))])


    for i, p in enumerate(players):
        section = f"PLAYER_{i}"
        rows.append([section, "name",       p.name])
        rows.append([section, "role",       type(p).__name__])
        rows.append([section, "city",       p.city])
        rows.append([section, "actions",    str(p.actions)])
        rows.append([section, "cards",      _list_to_csv_cell(p.cards)])
        rows.append([section, "avatar_idx", str(getattr(p, "avatar_idx", 0))])
        rows.append([section, "ops_used",
                     str(int(getattr(p, "ops_expert_special_move_used", False)))])
        rows.append([section, "stored_event",
                     str(getattr(p, "stored_event_card", "") or "")])

    with open(SAVE_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"[SAVE] Game saved to {SAVE_FILE}")


def load_game():
    """Return True on success, False if no save file found."""
    global Pandemic_Game, players, turn, num_players, selected_difficulty
    global game_over, game_won, lose_reason, result_alpha

    if not os.path.exists(SAVE_FILE):
        print("[LOAD] No save file found.")
        return False

    # Read all rows into a dict-of-dicts  { section: {key: value} }
    data = {}
    with open(SAVE_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue
            section, key, value = row[0], row[1], row[2]
            data.setdefault(section, {})[key] = value

    meta  = data.get("META",  {})
    board = data.get("BOARD", {})


    turn               = int(meta.get("turn", 0))
    num_players        = int(meta.get("num_players", 2))
    selected_difficulty = int(meta.get("selected_difficulty", 0))


    for cname in city_list:
        cd   = city_list[cname]
        city = City(name=cname, connections=cd["connections"],
                    colour=cd["colour"], location=cd["location"])
        section = f"CITY_{cname}"
        if section in data:
            city.virus          = [int(x) for x in _csv_cell_to_list(data[section].get("virus", "0|0|0|0"))]
            city.research_center = bool(int(data[section].get("research_center", "0")))
        city_objects[cname] = city


    Pandemic_Game = Board.__new__(Board)
    Pandemic_Game.outbreak_counter           = int(board.get("outbreak_counter", 0))
    Pandemic_Game.epidemic_count             = int(board.get("epidemic_count", 0))
    Pandemic_Game.infection_rate             = int(board.get("infection_rate", 2))
    Pandemic_Game.infection_rate_track       = [2, 2, 2, 3, 3, 4, 4]
    Pandemic_Game.cures                      = [x == "True" for x in _csv_cell_to_list(board.get("cures", "False|False|False|False"))]
    Pandemic_Game.eradicated                 = [x == "True" for x in _csv_cell_to_list(board.get("eradicated", "False|False|False|False"))]
    Pandemic_Game.city_cards                 = _csv_cell_to_list(board.get("city_cards", ""))
    Pandemic_Game.infection_cards            = _csv_cell_to_list(board.get("infection_cards", ""))
    Pandemic_Game.infection_card_discard_pile = _csv_cell_to_list(board.get("infection_discard", ""))
    Pandemic_Game.player_discard_pile        = _csv_cell_to_list(board.get("player_discard", ""))
    Pandemic_Game.quiet_night_active         = bool(int(board.get("quiet_night", "0")))
    Pandemic_Game.outbreak_animations        = []
    Pandemic_Game.difficulty                 = selected_difficulty + 4

    players = []
    for i in range(num_players):
        section = f"PLAYER_{i}"
        if section not in data:
            break
        pd   = data[section]
        role = pd.get("role", "Player")
        cls  = ROLE_CLASS_MAP.get(role, Player)

        p = cls.__new__(cls)
        p.name       = pd.get("name", f"Player {i+1}")
        p.city       = pd.get("city", "Atlanta")
        p.actions    = int(pd.get("actions", 4))
        p.cards      = _csv_cell_to_list(pd.get("cards", ""))
        p.colour     = (255, 255, 255)
        p.avatar_idx = int(pd.get("avatar_idx", 0))
        p.require_to_cure = 4 if isinstance(p, Scientist) else 5
        p.operations = False

        if isinstance(p, Operations_Expert):
            p.ops_expert_special_move_used = bool(int(pd.get("ops_used", "0")))
        if isinstance(p, Contingency_Planner):
            stored = pd.get("stored_event", "")
            p.stored_event_card = stored if stored else None

        players.append(p)

    game_over    = False
    game_won     = False
    lose_reason  = ""
    result_alpha = 0

    print(f"[LOAD] Game loaded from {SAVE_FILE}")
    return True


players          = []
player_options   = [2, 3, 4]
selected_index   = 0
selected_difficulty = 0
player_colors    = [(255,255,255), (0,255,0), (255,165,0), (255,0,255)]
difficulties     = ["Easy", "Normal", "Hard"]

avatar_select_player_idx = 0
avatar_grid_rects        = []
ai_toggle_rects = []
player_is_ai  = [False, False, False, False]
ai_last_move_time = 0
AI_MOVE_DELAY = 250

role_classes = [Medic, Scientist, Researcher, Dispatcher,
                Contingency_Planner, Operations_Expert, Quarantine_Specialist]
random.shuffle(role_classes)

turn             = 0
num_players      = 2
target           = None
dispatcher_move_other    = None
dispatcher_occupied_mode = False
dispatcher_occupied_pawn = None

share_popup      = None
occupy_popup     = None
discard_popup    = None
event_popup      = None        
pending_event    = None        
pending_end_turn = False
action_buttons   = {}

running      = True
clock        = pygame.time.Clock()
game_state   = [1, 0, 0, 0]   
virus_angle  = 0.0
game_over    = False
game_won     = False
lose_reason  = ""
result_alpha = 0

Pandemic_Game = None   

def loading_screen():
    global selected_index, selected_difficulty
    screen.fill((10, 20, 30))

    title_shadow = largeGunfont.render("PANDEMIC", True, (50, 0, 0))
    title_surface = largeGunfont.render("PANDEMIC", True, (200, 0, 0))
    screen.blit(title_shadow, (width/2 - 215, height/5 + 5))
    screen.blit(title_surface, (width/2 - 220, height/5))

    players_text = smallfont.render("SELECT NUMBER OF PLAYERS", True, (180, 180, 180))
    screen.blit(players_text, (width/2 - players_text.get_width()/2, height/2.8))

    radius  = 60
    circles = [
        (width//2 - 150, int(height/2+20), radius, 2),
        (width//2,       int(height/2+20), radius, 3),
        (width//2 + 150, int(height/2+20), radius, 4),
    ]
    for i, (x, y, r, n) in enumerate(circles):
        color     = (255, 200, 0) if i == selected_index else (100, 100, 100)
        pygame.draw.circle(screen, color,       (x, y), r + 5, 2)
        pygame.draw.circle(screen, (30, 30, 30),(x, y), r)
        if i == selected_index:
            pygame.draw.circle(screen, (255, 200, 0), (x, y), r, 4)
        number_surface = largefont.render(str(n), True, color)
        screen.blit(number_surface, number_surface.get_rect(center=(x, y)))

    diff_text = smallfont.render("SELECT DIFFICULTY", True, (180, 180, 180))
    screen.blit(diff_text, (width/2 - diff_text.get_width()/2, height/1.5))

    diffs     = ["EASY", "NORMAL", "HARD"]
    btn_w, btn_h = 180, 60
    for i, diff in enumerate(diffs):
        diff_x = width//2 - 300 + i*210
        diff_y = int(height/1.3)
        rect   = pygame.Rect(diff_x, diff_y, btn_w, btn_h)
        color      = (200, 0, 0) if i == selected_difficulty else (60, 60, 60)
        text_color = (255, 255, 255) if i == selected_difficulty else (150, 150, 150)
        pygame.draw.rect(screen, (20, 20, 20), rect)
        pygame.draw.rect(screen, color, rect, 3)
        if i == selected_difficulty:
            pygame.draw.rect(screen, (60, 0, 0), rect.inflate(-4, -4))
        diff_surface = smallGunfont.render(diff, True, text_color)
        screen.blit(diff_surface, diff_surface.get_rect(center=rect.center))

  
    save_exists = os.path.exists(SAVE_FILE)
    load_rect   = pygame.Rect(width//2 - 110, int(height*0.86), 220, 52)
    load_col    = (0, 140, 80) if save_exists else (50, 60, 60)
    load_border = (0, 220, 120) if save_exists else (80, 90, 90)
    load_txt_col = (255,255,255) if save_exists else (100,100,100)
    pygame.draw.rect(screen, load_col, load_rect, border_radius=8)
    pygame.draw.rect(screen, load_border, load_rect, 2, border_radius=8)
    load_label = tinyGunfont.render("LOAD SAVED GAME" if save_exists else "NO SAVE FOUND", True, load_txt_col)
    screen.blit(load_label, load_label.get_rect(center=load_rect.center))

    mouse_pressed = pygame.mouse.get_pressed()
    if mouse_pressed[0]:
        mouse_pos = pygame.mouse.get_pos()
        for i, (x, y, r, n) in enumerate(circles):
            if ((mouse_pos[0]-x)**2 + (mouse_pos[1]-y)**2)**0.5 <= r:
                selected_index = i
        for i, diff in enumerate(diffs):
            diff_x = width//2 - 300 + i*210
            rect   = pygame.Rect(diff_x, int(height/1.3), btn_w, btn_h)
            if rect.collidepoint(mouse_pos):
                selected_difficulty = i

    instr_surface = cityfont.render("PRESS ENTER TO START MISSION", True, (100, 100, 100))
    screen.blit(instr_surface, (width/2 - instr_surface.get_width()/2, height - 40))

    return load_rect   


def avatar_select_screen():
    global avatar_select_player_idx, avatar_grid_rects, ai_toggle_rects
    screen.fill((10, 20, 30))

    title = largeGunfont.render("CHOOSE AVATARS", True, (235, 235, 235))
    screen.blit(title, (width//2 - title.get_width()//2, 48))

    cur_player = players[avatar_select_player_idx]
    accent     = ROLE_ACCENT.get(type(cur_player).__name__, (200, 0, 0))
    chosen     = {p.avatar_idx for p in players if getattr(p, "avatar_idx", None) is not None}

    left_x, top_y, row_h, thumb = 120, 175, 104, 64
    ai_toggle_rects = []
    for i, p in enumerate(players):
        row_y     = top_y + i * row_h
        row_accent = ROLE_ACCENT.get(type(p).__name__, (140, 140, 140))
        row_rect   = pygame.Rect(left_x - 14, row_y - 10, 420, row_h - 12)
        is_active  = (i == avatar_select_player_idx)
        pygame.draw.rect(screen, (18, 24, 34) if is_active else (14, 18, 26), row_rect, border_radius=12)
        pygame.draw.rect(screen, row_accent if is_active else (50, 60, 78), row_rect, 2 if is_active else 1, border_radius=12)
        name_col = (255, 255, 255) if is_active else (200, 200, 200)
        name_s = smallfont.render(p.name, True, name_col)
        role_s = cityfont.render(type(p).__name__.replace("_", " ").upper(), True, row_accent)
        screen.blit(name_s, (left_x + 12, row_y))
        screen.blit(role_s, (left_x + 14, row_y + 50))
        tog_w, tog_h = 82, 32
        tog_x = row_rect.right - thumb - 26 - tog_w
        tog_y = row_rect.centery - tog_h // 2
        tog_rect = pygame.Rect(tog_x, tog_y, tog_w, tog_h)
        ai_toggle_rects.append((tog_rect, i))
        is_ai_flag = player_is_ai[i]
        tog_bg = (30, 80, 50) if is_ai_flag else (60, 30, 30)
        tog_border = (60, 180, 90) if is_ai_flag else (180, 60, 60)
        tog_label = "CPU" if is_ai_flag else "HUM"
        tog_tcol = (120, 255, 140) if is_ai_flag else (255, 120, 120)
        pygame.draw.rect(screen, tog_bg, tog_rect, border_radius=6)
        pygame.draw.rect(screen, tog_border, tog_rect, 2, border_radius=6)
        ts = tinyGunfont.render(tog_label, True, tog_tcol)
        screen.blit(ts, ts.get_rect(center=tog_rect.center))

        if getattr(p, "avatar_idx", None) is not None and avatar_surfaces_small:
            idx = p.avatar_idx
            if isinstance(idx, int) and 0 <= idx < len(avatar_surfaces_small):
                tx = row_rect.right - thumb - 14
                ty = row_rect.centery - thumb // 2
                screen.blit(avatar_surfaces_small[idx], (tx, ty))
                pygame.draw.rect(screen, row_accent,
                                 pygame.Rect(tx-4, ty-4, thumb+8, thumb+8), 2, border_radius=10)

    grid_cols, cell, gap  = 3, 140, 26
    grid_x, grid_y        = width//2 + 120, 200
    avatar_grid_rects     = []
    cur_idx               = getattr(cur_player, "avatar_idx", None)
    cur_is_ai             = player_is_ai[avatar_select_player_idx]
    for idx, surf in enumerate(avatar_surfaces_grid if avatar_surfaces_grid else avatar_surfaces):
        r  = idx // grid_cols
        c  = idx  % grid_cols
        x  = grid_x + c * (cell + gap)
        y  = grid_y + r * (cell + gap)
        rect = pygame.Rect(x, y, cell, cell)
        avatar_grid_rects.append((rect, idx))
        hovered        = rect.collidepoint(pygame.mouse.get_pos()) and not cur_is_ai
        taken_by_other = (idx in chosen) and (cur_idx != idx)
        bg = (16, 20, 28) if (taken_by_other or cur_is_ai) else ((35, 45, 62) if hovered else (24, 30, 42))
        border = (55, 60, 70) if (taken_by_other or cur_is_ai) else (accent if hovered else (70, 85, 105))
        pygame.draw.rect(screen, bg, rect, border_radius=16)
        pygame.draw.rect(screen, border, rect, 3 if hovered else 2, border_radius=16)
        if surf:
            screen.blit(surf, surf.get_rect(center=rect.center))
        if taken_by_other:
            ov = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            ov.fill((0,0,0,140))
            screen.blit(ov, (rect.x, rect.y))
            lock = tinyGunfont.render("TAKEN", True, (190,190,190))
            screen.blit(lock, lock.get_rect(center=rect.center))
        if cur_idx == idx:
            pygame.draw.rect(screen, (255,230,150), rect.inflate(-10,-10), 3, border_radius=14)

    if cur_is_ai:
        ai_msg = tinyGunfont.render("CPU player — avatar auto-assigned", True, (120, 220, 140))
        screen.blit(ai_msg, ai_msg.get_rect(center=(grid_x + (grid_cols * (cell + gap)) // 2, grid_y + 220)))

    all_set   = all(getattr(p, "avatar_idx", None) is not None for p in players)
    instr_txt = "All set — press Enter to begin." if all_set else "One avatar per player — no duplicates."
    instr_col = (220,224,230) if all_set else (175,185,198)
    instr     = avatar_footer_font.render(instr_txt, True, instr_col)
    screen.blit(instr, (width//2 - instr.get_width()//2, height - 88))


def check_win_lose():
    global game_over, game_won, lose_reason
    if all(Pandemic_Game.cures):
        game_over = True; game_won = True; return
    if Pandemic_Game.outbreak_counter >= 8:
        game_over = True; game_won = False; lose_reason = "TOO MANY OUTBREAKS"; return
    colour_names = ["Blue","Yellow","Black","Red"]
    for idx, col in enumerate(colour_names):
        total = sum(city_objects[n].virus[idx] for n in city_objects)
        if total > 24:
            game_over = True; game_won = False
            lose_reason = f"NO {col.upper()} CUBES LEFT"; return
    if not Pandemic_Game.city_cards:
        game_over = True; game_won = False; lose_reason = "PLAYER DECK EXHAUSTED"


def end_turn(player):
    global turn, discard_popup, pending_end_turn
    if isinstance(player, Operations_Expert):
        player.ops_expert_special_move_used = False
    player.actions = 4

    for _ in range(2):
        if not Pandemic_Game.city_cards:
            check_win_lose(); return
        drawn = Pandemic_Game.city_cards.pop()
        if drawn == "Infection Card":
            Pandemic_Game.epidemic_count += 1
            Pandemic_Game.infection_rate = Pandemic_Game.infection_rate_track[
                min(Pandemic_Game.epidemic_count, len(Pandemic_Game.infection_rate_track)-1)]
            Pandemic_Game.shuffle_infection_deck()
        else:
            player.cards.append(drawn)

    if not getattr(Pandemic_Game, "quiet_night_active", False):
        Pandemic_Game.infect_virus(city_objects, players)
    else:
        Pandemic_Game.quiet_night_active = False

    check_win_lose()
    if game_over:
        return

    turn += 1

   
    save_game()

    for p in players:
        if len(p.cards) > 7:
            discard_popup = {"player": p, "card_rects": []}
            pending_end_turn = True
            break


def player_test(click_event=None):
    global turn, target, dispatcher_move_other, dispatcher_occupied_mode, dispatcher_occupied_pawn
    global share_popup, discard_popup, occupy_popup, pending_end_turn
    global event_popup, pending_event

    mouse_pos    = pygame.mouse.get_pos()
    active_player = players[turn % num_players]
    has_event_card = any(card in EVENT_CARDS for card in active_player.cards)
    
  
    if isinstance(active_player, Contingency_Planner):
        if getattr(active_player, "stored_event_card", None):
            has_event_card = True

   
    if discard_popup is not None:
        if click_event and discard_popup.get("card_rects"):
            for crect, card in discard_popup["card_rects"]:
                if crect.collidepoint(mouse_pos):
                    discard_popup["player"].cards.remove(card)
                    Pandemic_Game.player_discard_pile.append(card)
                    if len(discard_popup["player"].cards) > 7:
                        discard_popup["card_rects"] = []
                    else:
                        discard_popup    = None
                        pending_end_turn = False
                    break
        return

    
    if occupy_popup is not None:
        if click_event and occupy_popup.get("rects"):
            for key, val in occupy_popup["rects"].items():
                rect, chosen_player = val
                if rect.collidepoint(mouse_pos):
                    if key == "cancel":
                        occupy_popup             = None
                        dispatcher_occupied_mode = False
                        dispatcher_occupied_pawn = None
                    elif chosen_player is not None:
                        dispatcher_occupied_pawn = chosen_player
                        occupy_popup             = None
                    break
        return

    
    if share_popup is not None:
        if click_event and share_popup.get("rects"):
            for key, val in share_popup["rects"].items():
                rect, other, cards, giving = val
                if rect.collidepoint(mouse_pos):
                    if key == "cancel":
                        share_popup = None
                    elif cards and other is not None:
                        active_player.share_knowledge(other, cards[0], giving, city_objects)
                        share_popup = None
                    break
        return
    
   
    if pending_event is not None:
        if click_event:
            card_name = pending_event["card"]
            step      = pending_event.get("step", 1)
            rects     = pending_event.get("rects", {})

            
            cancel_rect = pending_event.get("cancel_rect")
            if cancel_rect and cancel_rect.collidepoint(mouse_pos):
                pending_event = None
                return

       
            if card_name == "Airlift" and step == 1:
                for key, val in rects.items():
                    if key == "cancel":
                        if val[0].collidepoint(mouse_pos):
                            pending_event = None
                            return
                    else:
                        brect, pidx = val
                        if brect.collidepoint(mouse_pos):
                            pending_event["target_player_idx"] = pidx
                            pending_event["step"] = 2
                            return

            
            elif card_name in ("Airlift", "Government Grant") and step == 2:
                for cname, city in city_objects.items():
                    dist = ((mouse_pos[0]-city.location[0])**2 +
                            (mouse_pos[1]-city.location[1])**2)**0.5
                    if dist < 20:
                        player_idx = pending_event.get("player_idx", turn % num_players)
                        actor      = players[player_idx]
                        if card_name == "Airlift":
                            t_idx  = pending_event.get("target_player_idx", player_idx)
                            target_pawn = players[t_idx]
                            actor.use_event_card("Airlift", Pandemic_Game, city_objects,
                                                 cname, None)
                            # move whichever pawn was selected
                            target_pawn.city = cname
                            if isinstance(target_pawn, Medic):
                                target_pawn.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                        else:
                            actor.use_event_card("Government Grant", Pandemic_Game, city_objects,
                                                 cname, None)
                        pending_event = None
                        return

           
            elif card_name == "Resilient Population":
                for key, val in rects.items():
                    if key == "cancel":
                        if val[0].collidepoint(mouse_pos):
                            pending_event = None
                            return
                    else:
                        brect, city_name = val
                        if brect.collidepoint(mouse_pos):
                            player_idx = pending_event.get("player_idx", turn % num_players)
                            actor      = players[player_idx]
                            actor.use_event_card("Resilient Population", Pandemic_Game,
                                                 city_objects, city_name, None)
                            pending_event = None
                            return

            elif card_name == "Forecast":
                confirm = rects.get("confirm")
                cancel  = rects.get("cancel")
                if confirm and confirm[0].collidepoint(mouse_pos):
                    player_idx = pending_event.get("player_idx", turn % num_players)
                    actor      = players[player_idx]
                    actor.use_event_card("Forecast", Pandemic_Game, city_objects, None, None)
                    pending_event = None
                elif cancel and cancel[0].collidepoint(mouse_pos):
                    pending_event = None
        return

    
    if event_popup is not None:
        if click_event and event_popup.get("rects"):
            for key, val in event_popup["rects"].items():
                rect, card_name, is_stored = val
                if rect.collidepoint(mouse_pos):
                    if key == "cancel":
                        event_popup = None
                        return
                    if card_name is not None:
                        event_popup = None
                        player_idx  = turn % num_players
                        if card_name in ("Government Grant", "Resilient Population"):
                            pending_event = {"card": card_name, "player_idx": player_idx,
                                             "step": 2, "rects": {}}
                        elif card_name == "Airlift":
                            pending_event = {"card": card_name, "player_idx": player_idx,
                                             "step": 1, "rects": {}}
                        elif card_name == "Forecast":
                            pending_event = {"card": card_name, "player_idx": player_idx,
                                             "step": 1, "rects": {}}
                        else:
                            # One Quiet Night – play immediately
                            actor = players[player_idx]
                            if is_stored and isinstance(actor, Contingency_Planner):
                                actor.use_event_card(card_name, Pandemic_Game, city_objects, None, None)
                            else:
                                actor.use_event_card(card_name, Pandemic_Game, city_objects, None, None)
                    return
        return

    
    moved_or_acted = False

    if click_event and action_buttons:
        for btn_key, btn_rect in action_buttons.items():
            if btn_rect.collidepoint(mouse_pos):
                current_city = city_objects[active_player.city]
                if btn_key == "event":
                    SND_CLICK.play()
                    if has_event_card:
                        event_popup = {
                            "player": active_player,
                            "rects": {},
                            "phase": "select" 
                        }
                    else:
                        print("No event cards available!")

                if btn_key == "treat":
                    SND_CLICK.play()
                    colour_order = ["Blue","Yellow","Black","Red"]
                    native       = current_city.colour
                    native_idx   = colour_order.index(native)
                    if current_city.virus[native_idx] > 0:
                        treat_colour = native
                    else:
                        others = [col for col in colour_order
                                  if col != native and current_city.virus[colour_order.index(col)] > 0]
                        treat_colour = random.choice(others) if others else native
                    active_player.treat_disease(treat_colour, city_objects, Pandemic_Game)

                elif btn_key == "build":
                    SND_CLICK.play()
                    active_player.build_research_station(city_objects, Pandemic_Game)

                elif btn_key == "cure":
                    SND_CLICK.play()
                    colour_counts = {}
                    for c in active_player.cards:
                        if c in city_objects:
                            col = city_objects[c].colour
                            colour_counts.setdefault(col, []).append(c)
                    cure_colour = next(
                        (col for col, cards in colour_counts.items()
                         if len(cards) >= active_player.require_to_cure
                         and not Pandemic_Game.cures[["Blue","Yellow","Black","Red"].index(col)]),
                        None
                    )
                    if cure_colour:
                        cards_to_discard = colour_counts[cure_colour][:active_player.require_to_cure]
                        active_player.discover_cure(cure_colour, cards_to_discard, city_objects, Pandemic_Game)
                        check_win_lose()

                elif btn_key == "share":
                    SND_CLICK.play()
                    others = [p for p in players if p != active_player and p.city == active_player.city]
                    if others:
                        share_popup = {"rects": {}}


                elif btn_key == "skip":
                    SND_CLICK.play()
                    if active_player.actions > 0:
                        active_player.actions -= 1

                elif btn_key == "dispatcher_occupy":
                    SND_CLICK.play()
                    if isinstance(active_player, Dispatcher) and active_player.actions > 0:
                        dispatcher_occupied_mode = True
                        dispatcher_occupied_pawn = None
                        occupy_popup = {"rects": {}}
                break

   
    if click_event:
        for city_name, city in city_objects.items():
            dist = ((mouse_pos[0]-city.location[0])**2 +
                    (mouse_pos[1]-city.location[1])**2)**0.5
            if dist < 20:
                if (dispatcher_occupied_mode and isinstance(active_player, Dispatcher)
                        and dispatcher_occupied_pawn is not None):
                    mover = dispatcher_occupied_pawn
                    if active_player.actions > 0:
                        in_city = [p for p in players if p.city == city_name]
                        if in_city and mover.city != city_name:
                            active_player.dispatcher_move_pawn_to_occupied_city(
                                mover, city_name, city_objects, players)
                            moved_or_acted = True
                        else:
                            cur_obj = city_objects[mover.city]
                            if city_name in cur_obj.connections:
                                active_player.drive_ferry(city_name, city_objects, move_pawn=mover)
                                moved_or_acted = True
                            elif city_name in active_player.cards:
                                active_player.direct_flight(city_name, city_objects,
                                                            Pandemic_Game, move_pawn=mover)
                                moved_or_acted = True
                            elif mover.city in active_player.cards:
                                active_player.charter_flight(city_name, city_objects,
                                                             Pandemic_Game, move_pawn=mover)
                                moved_or_acted = True
                            else:
                                active_player.shuttle_flight(city_name, city_objects, move_pawn=mover)
                                moved_or_acted = True

                        if moved_or_acted and isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)

                    if moved_or_acted:
                        dispatcher_occupied_mode = False
                        dispatcher_occupied_pawn = None
                else:
                    mover = (dispatcher_move_other
                             if isinstance(active_player, Dispatcher) and dispatcher_move_other
                             else active_player)
                    cur_obj = city_objects[mover.city]

                    if city_name in cur_obj.connections:
                        active_player.drive_ferry(city_name, city_objects,
                                                  move_pawn=dispatcher_move_other if isinstance(active_player, Dispatcher) else None)
                        moved_or_acted = True
                    elif city_name in active_player.cards:
                        active_player.direct_flight(city_name, city_objects, Pandemic_Game, move_pawn=dispatcher_move_other if isinstance(active_player, Dispatcher) else None)
                        moved_or_acted = True
                        if isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                        if isinstance(active_player, Dispatcher):
                            dispatcher_move_other = None
                    elif mover.city in active_player.cards:
                        active_player.charter_flight(city_name, city_objects, Pandemic_Game, move_pawn=dispatcher_move_other if isinstance(active_player, Dispatcher) else None)
                        moved_or_acted = True
                        if isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                        if isinstance(active_player, Dispatcher):
                            dispatcher_move_other = None
                    elif (isinstance(active_player, Operations_Expert) and dispatcher_move_other is None and
                          not active_player.ops_expert_special_move_used and
                          city_objects[active_player.city].research_center and
                          city_name != active_player.city):
                        city_cards_in_hand = [c for c in active_player.cards if c in city_objects]
                        if city_cards_in_hand:
                            active_player.ops_expert_special_move(city_name, city_cards_in_hand[0], city_objects, Pandemic_Game)
                            moved_or_acted = True
                            if isinstance(active_player, Medic):
                                active_player.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                    else:
                        active_player.shuttle_flight(city_name, city_objects, move_pawn=dispatcher_move_other if isinstance(active_player, Dispatcher) else None)
                        moved_or_acted = True
                        if isinstance(mover, Medic):
                            mover.auto_remove_cured_cubes(city_objects, Pandemic_Game)
                        if isinstance(active_player, Dispatcher):
                            dispatcher_move_other = None

                if moved_or_acted:
                    break

    if active_player.actions == 0:
        end_turn(active_player)
turn = 0
target = None
load_button_rect = None  
dispatcher_move_other = None
dispatcher_occupied_mode = False
dispatcher_occupied_pawn = None
share_popup = None
occupy_popup = None
discard_popup = None
pending_end_turn = False
action_buttons = {}
running = True
clock = pygame.time.Clock()
game_state = [1,0,0,0]
virus_angle = 0.0
game_over = False
game_won = False
lose_reason = ""
result_alpha = 0
ai_last_move_time = 0


load_button_rect = None  

while running:
    click_event = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

       
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click_event = True
            mx, my = pygame.mouse.get_pos()

      
            if game_state[0] == 1 and load_button_rect and load_button_rect.collidepoint((mx, my)):
                if os.path.exists(SAVE_FILE):
                    if load_game():
                        game_state[0] = 0   

          
            elif game_state[0] == 2 and players and avatar_surfaces:
                chosen  = {p.avatar_idx for p in players if getattr(p, "avatar_idx", None) is not None}
                cur     = players[avatar_select_player_idx]
                cur_idx = getattr(cur, "avatar_idx", None)

                tog_clicked = False
                for tog_rect, pidx in ai_toggle_rects:
                    if tog_rect.collidepoint((mx, my)):
                        tog_clicked = True
                        SND_CLICK.play()
                        player_is_ai[pidx] = not player_is_ai[pidx]
                        if player_is_ai[pidx]:
                            used = {p.avatar_idx for p in players if getattr(p, "avatar_idx", None) is not None}
                            for a in range(len(avatar_surfaces)):
                                if a not in used:
                                    players[pidx].avatar_idx = a
                                    break
                            next_human = None
                            for step in range(1, len(players) + 1):
                                j = (pidx + step) % len(players)
                                if not player_is_ai[j] and getattr(players[j], "avatar_idx", None) is None:
                                    next_human = j
                                    break
                            if next_human is not None:
                                avatar_select_player_idx = next_human
                        else:
                            players[pidx].avatar_idx = None
                            avatar_select_player_idx = pidx
                        break

                if not tog_clicked:
                    if player_is_ai[avatar_select_player_idx]:
                        pass
                    else:
                        for rect, aidx in avatar_grid_rects:
                            if rect.collidepoint((mx, my)):
                                if (aidx in chosen) and (cur_idx != aidx):
                                    break
                                players[avatar_select_player_idx].avatar_idx = aidx
                                SND_AVATAR_SEL.play()
                                next_idx = None
                                for step in range(1, len(players) + 1):
                                    j = (avatar_select_player_idx + step) % len(players)
                                    if not player_is_ai[j] and getattr(players[j], "avatar_idx", None) is None:
                                        next_idx = j
                                        break
                                avatar_select_player_idx = (avatar_select_player_idx
                                                            if next_idx is None else next_idx)
                                break

       
        elif event.type == pygame.KEYDOWN:

            if game_state[0] == 1:
                if event.key == pygame.K_RETURN:
                    game_state[0] = 2
                    Pandemic_Game = Board(city_objects, difficulty=selected_difficulty)
                    Pandemic_Game.set_board(city_objects)
  
                    for ec in EVENT_CARDS:
                        Pandemic_Game.city_cards.append(ec)
                    random.shuffle(Pandemic_Game.city_cards)

                    num_players = player_options[selected_index]
                    players     = []
                    random.shuffle(role_classes)
                    for i in range(num_players):
                        new_player = role_classes[i](
                            name=f"Player {i+1}",
                            colour=player_colors[i],
                            total=num_players,
                            city_cards=Pandemic_Game.city_cards,
                            board=Pandemic_Game
                        )
                        players.append(new_player)
                    Pandemic_Game.add_epidemic_card()
                    avatar_select_player_idx = 0

            elif game_state[0] == 2:
                if event.key == pygame.K_RETURN:
                    if players and all(getattr(p, "avatar_idx", None) is not None for p in players):
                        for i in range(len(players)):
                            if player_is_ai[i]:
                                players[i] = convert_to_ai(players[i])
                                players[i].name = f"CPU {i + 1}"
                        game_state[0] = 0
                elif event.key == pygame.K_ESCAPE:
                    players      = []
                    for i in range(4):
                        player_is_ai[i] = False
                    game_state[0] = 1

            else:
                if event.key == pygame.K_p and not game_over:
                    game_state[3] = 1 - game_state[3]
                elif event.key == pygame.K_ESCAPE and game_over:
                    running = False
                elif event.key == pygame.K_r and game_over:
                    # Reset
                    game_over    = False
                    game_won     = False
                    lose_reason  = ""
                    result_alpha = 0
                    turn         = 0
                    players      = []
                    event_popup  = None
                    pending_event = None
                    for i in range(4):
                        player_is_ai[i] = False
                    for name, data in city_list.items():
                        city_objects[name] = City(
                            name=name,
                            connections=data["connections"],
                            colour=data["colour"],
                            location=data["location"]
                        )
                    city_objects["Atlanta"].research_center = True
                    game_state[0] = 1

    
    if game_state[0] == 1:
        load_button_rect = loading_screen()

    elif game_state[0] == 2:
        avatar_select_screen()

    elif game_state[3] == 1 and not game_over:
        player_cards_display(screen, players, city_objects, width, height,
                             smallGunfont, cityfont, get_colour,
                             avatar_surfaces=avatar_surfaces)

    else:
        screen.fill((0, 30, 70))
        screen.blit(board_img, (0, 0))

        draw_connections(screen, city_objects, width, get_colour)
        draw_cities(screen, city_objects, virus_angle, cityfont, get_colour)
        draw_outbreak_animations(screen, Pandemic_Game, city_objects)
        draw_movement_highlights(screen, players, city_objects, turn, num_players,
                                 dispatcher_occupied_mode, dispatcher_occupied_pawn,
                                 dispatcher_move_other)
        draw_board(screen, Pandemic_Game, city_objects, width, height,
                   largeGunfont, smallGunfont, tinyGunfont, cityfont, get_colour)
        draw_players(screen, players, city_objects, turn, num_players)
        action_buttons = draw_current_player_panel(
            screen, players, city_objects, Pandemic_Game, turn, num_players,
            width, height, tinyGunfont, cityfont, get_colour,
            dispatcher_occupied_mode, dispatcher_occupied_pawn,
            avatar_surfaces=avatar_surfaces
        )

        if not game_over:
            active_player = players[turn % num_players]

            while discard_popup and isinstance(discard_popup.get("player"), AIPlayer):
                p = discard_popup["player"]
                p.auto_discard(city_objects, Pandemic_Game, players)
                if len(p.cards) <= 7:
                    discard_popup    = None
                    pending_end_turn = False

            if isinstance(active_player, AIPlayer):
                now = pygame.time.get_ticks()
                if not discard_popup and now - ai_last_move_time >= AI_MOVE_DELAY:
                    active_player._city_objects_ref = city_objects
                    active_player._players_ref = players
                    if active_player.actions > 0:
                        taken = active_player._decide_action(city_objects, Pandemic_Game, players)
                        if not taken:
                            active_player.actions = 0
                    if active_player.actions == 0:
                        end_turn(active_player)
                        while discard_popup and isinstance(discard_popup.get("player"), AIPlayer):
                            p = discard_popup["player"]
                            p.auto_discard(city_objects, Pandemic_Game, players)
                            if len(p.cards) <= 7:
                                discard_popup    = None
                                pending_end_turn = False
                    ai_last_move_time = now
            else:
                player_test(click_event)

            share_popup   = draw_share_popup(screen, share_popup, players, turn,
                                             width, height, smallGunfont, tinyGunfont)
            occupy_popup  = draw_occupy_popup(screen, occupy_popup, players, turn,
                                              width, height, tinyGunfont)
            discard_popup = draw_discard_popup(screen, discard_popup, city_objects,
                                               width, height, smallGunfont, tinyGunfont,
                                               cityfont, get_colour)
            event_popup   = draw_event_popup(screen, event_popup, players, turn,
                                             city_objects, Pandemic_Game,
                                             width, height, tinyGunfont, cityfont)
            pending_event = draw_event_target_popup(screen, pending_event, players,
                                                    Pandemic_Game, city_objects,
                                                    width, height, tinyGunfont, cityfont)
        else:
            result_alpha = draw_result_screen(
                screen, Pandemic_Game, game_won, lose_reason, result_alpha,
                width, height, largeGunfont, smallGunfont, tinyGunfont, cityfont
            )

    pygame.display.flip()
    clock.tick(60)
    virus_angle += 0.012

pygame.quit()