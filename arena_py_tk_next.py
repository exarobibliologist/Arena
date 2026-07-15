import math
import random
import time
import os
import sys
import json
import re
import threading
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Optional, Dict, Any
from enum import Enum

# --- CORE GAME CLASSES & LOGIC ---

class Colors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    MAGENTA = '\033[35m'
    GRAY = '\033[38;5;239m'
    RESET = '\033[0m'

class Stance(Enum):
    NEUTRAL = "Neutral"
    ATTACK = "Attack"
    DEFEND = "Defend"
    GESTURE = "Gesture"

class Gladiator:
    """Represents a combatant in the arena."""
    def __init__(self, name: str, is_player: bool = False) -> None:
        self.is_player = is_player
        
        if self.is_player:
            self.personality = "Player"
            self.name = name
        else:
            self.personality = random.choice(["Assassin", "Slayer", "Tactician", "Berserker", "Survivor", "GoldDigger"])
            self.name = self.personality

        self.hp: int = 100
        self.base_atk: int = random.randint(15, 20)
        self.base_def_stat: int = random.randint(15, 20)
        
        self.atk: int = self.base_atk
        self.def_stat: int = self.base_def_stat
        
        self.stance: Stance = Stance.NEUTRAL
        self.atk_mult: float = 1.0
        self.def_mult: float = 1.0
        
        self.gold: int = 10 
        self.is_alive: bool = True

    def get_hp_color(self) -> str:
        """Calculates a true-color RGB ANSI string from Green (100) to Red (0)."""
        hp_pct = max(0, min(100, self.hp))
        if hp_pct > 50:
            # Fade from Green to Yellow
            r = int(255 * (100 - hp_pct) / 50.0)
            g = 255
        else:
            # Fade from Yellow to Red
            r = 255
            g = int(255 * hp_pct / 50.0)
        return f"\033[38;2;{r};{g};0m"

    def display_stats(self, index: int) -> str:
        """Returns a formatted string of the gladiator's current combat statistics."""
        marker = ""
        if self.is_alive:
            if self.stance == Stance.ATTACK: marker = f"{Colors.RED} (A){Colors.RESET}"
            elif self.stance == Stance.DEFEND: marker = f"{Colors.GREEN} (D){Colors.RESET}"
            elif self.stance == Stance.GESTURE: marker = f"{Colors.YELLOW} (G){Colors.RESET}"
            
        hp_str = f"{self.get_hp_color()}{self.hp:3}{Colors.RESET}"
            
        return f"[{index:2}] {self.name:12}: HP {hp_str} | Atk {self.atk:2} | Def {self.def_stat:2} | $ {self.gold:3} |{marker}"


class ArenaGame:
    """Main controller for the Arena combat simulation running in a background thread."""
    def __init__(self, ui_queue: queue.Queue, input_event: threading.Event) -> None:
        self.ui_queue = ui_queue
        self.input_event = input_event
        self.user_response = None
        
        self.pot: int = 10
        self.first_blood_victim: Optional[Gladiator] = None
        self.round_num: int = 1
        self.log_file: str = "arena_battle_log.txt"
        
        self.gladiators: List[Gladiator] = [Gladiator("Player", is_player=True)]
        self.player: Gladiator = self.gladiators[0]
        
        for _ in range(19):
            self.gladiators.append(Gladiator("AI")) 
            
        # Retain text-file logging as an artifact backup
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"{Colors.MAGENTA}--- BATTLE LOG INITIALIZED ---{Colors.RESET}\n")

    def gui_input(self, prompt_type: str, context: Any = None) -> Any:
        """Pauses the game thread and requests input from the Tkinter main thread."""
        self.input_event.clear()
        self.ui_queue.put(('PROMPT', prompt_type, context))
        self.input_event.wait() 
        return self.user_response

    def save_game(self, filename: str = "arena_save.json") -> None:
        state = {
            "pot": self.pot,
            "round_num": self.round_num,
            "first_blood_idx": self.gladiators.index(self.first_blood_victim) if self.first_blood_victim in self.gladiators else -1,
            "gladiators": [
                {
                    "name": g.name,
                    "is_player": g.is_player,
                    "hp": g.hp,
                    "base_atk": g.base_atk,
                    "base_def_stat": g.base_def_stat,
                    "atk": g.atk,
                    "def_stat": g.def_stat,
                    "stance": g.stance.value,
                    "atk_mult": g.atk_mult,
                    "def_mult": g.def_mult,
                    "gold": g.gold,
                    "is_alive": g.is_alive,
                    "personality": g.personality
                } for g in self.gladiators
            ]
        }
        with open(filename, "w") as f:
            json.dump(state, f)

    def load_game(self, filename: str = "arena_save.json") -> bool:
        if not os.path.exists(filename):
            return False
            
        with open(filename, "r") as f:
            state = json.load(f)
        
        self.pot = state.get("pot", 10)
        self.round_num = state.get("round_num", 1)
        
        self.gladiators = []
        for g_data in state.get("gladiators", []):
            g = Gladiator(g_data["name"], g_data["is_player"])
            g.name = g_data["name"] 
            g.hp = g_data["hp"]
            g.base_atk = g_data["base_atk"]
            g.base_def_stat = g_data["base_def_stat"]
            g.atk = g_data["atk"]
            g.def_stat = g_data["def_stat"]
            g.stance = Stance(g_data["stance"])
            g.atk_mult = g_data["atk_mult"]
            g.def_mult = g_data["def_mult"]
            g.gold = g_data["gold"]
            g.is_alive = g_data["is_alive"]
            g.personality = g_data.get("personality", "Berserker")
            self.gladiators.append(g)
            
        self.player = next((g for g in self.gladiators if g.is_player), self.gladiators[0])
        
        fb_idx = state.get("first_blood_idx", -1)
        if 0 <= fb_idx < len(self.gladiators):
            self.first_blood_victim = self.gladiators[fb_idx]
        else:
            self.first_blood_victim = None
            
        return True

    def get_alive_gladiators(self) -> List[Gladiator]:
        return [g for g in self.gladiators if g.is_alive]

    def sort_gladiators(self) -> None:
        self.gladiators.sort(key=lambda g: (g.is_alive, g.is_player), reverse=True)

    def get_idx_name(self, g: Gladiator) -> str:
        if g in self.gladiators:
            idx = self.gladiators.index(g) + 1
            if not g.is_player:
                return f"[{idx}]"
            return f"[{idx}] {g.name}"
        return g.name

    def reset_arena(self) -> None:
        self.pot = 10
        self.first_blood_victim = None
        for g in self.gladiators:
            g.hp = 100
            g.atk = g.base_atk
            g.def_stat = g.base_def_stat
            g.is_alive = True
            g.stance = Stance.NEUTRAL
            g.atk_mult = 1.0
            g.def_mult = 1.0
        self.sort_gladiators()

    def log_event(self, msg: str, delay: float = 0) -> None:
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
        self.ui_queue.put(('LOG', msg))
        if delay > 0:
            time.sleep(delay)

    def render_arena(self) -> None:
        lines = []
        lines.append("=" * 90)
        lines.append(f"THE ARENA - Current Pot: {self.pot} Gold".center(90))
        lines.append("=" * 90)
        
        def pad_ansi(text: str, width: int) -> str:
            visible_text = re.sub(r'\033\[.*?m', '', text)
            padding_needed = max(0, width - len(visible_text))
            return text + (" " * padding_needed)

        num_glads = len(self.gladiators)
        num_rows = (num_glads + 1) // 2
        
        for i in range(num_rows):
            left_glad = self.gladiators[i]
            left_str_raw = left_glad.display_stats(i + 1)
            
            if not left_glad.is_alive:
                left_str_raw = f"{Colors.GRAY}{left_str_raw}{Colors.RESET}"
                
            left_str_raw = pad_ansi(left_str_raw, 65)
                
            right_idx = i + num_rows
            if right_idx < num_glads:
                right_glad = self.gladiators[right_idx]
                right_str_raw = right_glad.display_stats(right_idx + 1)
                if not right_glad.is_alive:
                    right_str_raw = f"{Colors.GRAY}{right_str_raw}{Colors.RESET}"
                lines.append(f"{left_str_raw}   ||   {right_str_raw}")
            else:
                lines.append(f"{left_str_raw}   ||")
            
        lines.append("=" * 90)
        self.ui_queue.put(('RENDER', "\n".join(lines)))

    def loot_gladiator(self, survivor: Gladiator, deceased: Gladiator) -> None:
        atk_boost = max(1, deceased.atk // 4)
        def_boost = max(1, deceased.def_stat // 4)
        
        if survivor.is_player:
            self.render_arena()
            choice = self.gui_input("LOOT", {"deceased": deceased.name, "atk": atk_boost, "def": def_boost})
            if choice == '1':
                survivor.atk += atk_boost
                self.log_event(f"Player took the weapon! Temp Atk is now {survivor.atk}.")
            elif choice == '2':
                survivor.def_stat += def_boost
                self.log_event(f"Player took the shield! Temp Def is now {survivor.def_stat}.")
            elif choice == '3':
                self.log_event("Player respectfully leaves the gear untouched.")
        else:
            if random.random() > 0.5:
                survivor.atk += atk_boost
            else:
                survivor.def_stat += def_boost

    def player_turn(self, player: Gladiator) -> Optional[str]:
        while True:
            self.render_arena()
            choice = self.gui_input("MAIN_ACTION")
            
            if choice == '1':
                player.stance = Stance.ATTACK
                player.atk_mult = 1.0
                player.def_mult = 0.5
                self.player_attack_logic(player)
                break
            elif choice == '2':
                player.stance = Stance.DEFEND
                player.atk_mult = 0.5
                player.def_mult = 1.0
                self.log_event("Player takes a defensive stance!")
                break
            elif choice == '3':
                player.stance = Stance.GESTURE
                player.atk_mult = 1.0
                player.def_mult = 1.0
                cheer = max(1, int(self.pot * 0.01))
                self.pot += cheer
                self.log_event(f"Player pumps up the crowd! The pot increases by {cheer}!")
                break
            elif choice == 'S':
                self.save_game()
                self.log_event(f"{Colors.YELLOW}Game saved successfully.{Colors.RESET}")
            elif choice == 'L':
                if self.load_game():
                    self.log_event(f"{Colors.YELLOW}Game loaded successfully.{Colors.RESET}")
                    return "LOADED"
                else:
                    self.log_event(f"{Colors.RED}No save file found!{Colors.RESET}")
        return None

    def player_attack_logic(self, player: Gladiator) -> None:
        while True:
            self.render_arena()
            valid_targets = [(i+1, g.name) for i, g in enumerate(self.gladiators) if g != player and g.is_alive]
            if not valid_targets:
                break
                
            choice = self.gui_input("TARGET_SELECT", valid_targets)
            if choice is not None:
                try:
                    target_idx = int(choice) - 1
                    target = self.gladiators[target_idx]
                    self.execute_attack(player, target)
                    break
                except (ValueError, IndexError):
                    self.log_event(f"{Colors.RED}Invalid target selected.{Colors.RESET}")

    def ai_turn(self, ai: Gladiator) -> None:
        alive = self.get_alive_gladiators()
        targets = [g for g in alive if g != ai]
        
        if not targets:
            return

        weights = {'attack': 60, 'defend': 20, 'gesture': 20}
        
        if ai.hp < 40 or ai.personality == "Survivor":
            weights['defend'] += 40
            weights['attack'] -= 20
        
        if ai.personality == "Berserker":
            weights['attack'] += 30
            weights['defend'] -= 15
            weights['gesture'] -= 10
            
        w_vals = [max(1, w) for w in weights.values()]
        action = random.choices(list(weights.keys()), weights=w_vals)[0]
        
        if action == 'attack':
            ai.stance = Stance.ATTACK
            ai.atk_mult = 1.0
            ai.def_mult = 0.5
            
            if ai.personality == "Assassin":
                target = min(targets, key=lambda t: t.hp)
            elif ai.personality == "Slayer":
                target = max(targets, key=lambda t: t.hp)
            elif ai.personality == "Tactician":
                target = min(targets, key=lambda t: t.def_stat * t.def_mult)
            elif ai.personality == "GoldDigger":
                top_targets = sorted(targets, key=lambda t: t.gold, reverse=True)[:5]
                target = random.choice(top_targets)
            else:
                target = random.choice(targets)
                
            self.execute_attack(ai, target)
            
        elif action == 'defend':
            ai.stance = Stance.DEFEND
            ai.atk_mult = 0.5
            ai.def_mult = 1.0
            
        elif action == 'gesture':
            ai.stance = Stance.GESTURE
            ai.atk_mult = 1.0
            ai.def_mult = 1.0
            cheer = max(1, int(self.pot * 0.01))
            self.pot += cheer

    def _apply_damage(self, target: Gladiator, dmg_calc: float) -> int:
        dmg = max(0, int(dmg_calc))
        target.hp = max(0, target.hp - dmg)
        if target.hp == 0:
            target.is_alive = False
        return dmg

    def execute_attack(self, attacker: Gladiator, defender: Gladiator) -> None:
        att_name = self.get_idx_name(attacker)
        def_name = self.get_idx_name(defender)
        
        self.log_event(f"{att_name} attacks {def_name}!")
        
        att_atk = attacker.atk * attacker.atk_mult
        att_def = attacker.def_stat * attacker.def_mult
        
        def_base_atk = defender.atk * defender.atk_mult
        def_base_def = defender.def_stat * defender.def_mult

        if defender.is_player:
            reaction = self.player_reaction(attacker)
        else:
            if defender.hp < 30 or defender.personality == "Survivor":
                reaction = 'defend'
            elif defender.personality == "Berserker":
                reaction = 'counter'
            elif defender.personality == "Tactician":
                if (att_atk - (def_base_def * 0.75)) > 15:
                    reaction = 'defend' 
                else:
                    reaction = 'counter' 
            else:
                reaction = random.choice(['counter', 'defend'])
        
        if reaction == 'counter':
            self.log_event(f"{def_name} chooses to counterattack!")
            final_def_def = def_base_def * 0.75
            final_def_atk = def_base_atk * 1.50
        elif reaction == 'defend':
            self.log_event(f"{def_name} blocks and strikes back!")
            final_def_def = def_base_def * 1.50
            final_def_atk = def_base_atk * 0.75
            
        dmg_in = self._apply_damage(defender, att_atk - final_def_def)
        self.log_event(f"{att_name} hits for {dmg_in} damage!", delay=0.1)
        
        if dmg_in == 0:
            self.pot += 2
            self.log_event(f"{Colors.GREEN}FLAWLESS DEFENSE! The crowd throws 2 gold into the pot!{Colors.RESET}")
            
        if defender.is_alive:
            dmg_out = self._apply_damage(attacker, final_def_atk - att_def)
            self.log_event(f"{def_name} hits back for {dmg_out} damage!", delay=0.1)
            
            if dmg_out == 0:
                self.pot += 2
                self.log_event(f"{Colors.GREEN}FLAWLESS DEFENSE! The crowd throws 2 gold into the pot!{Colors.RESET}")

        if not defender.is_alive:
            self.pot += 25
            self.log_event(f"{Colors.GREEN}*** {def_name} HAS FALLEN! The crowd cheers (+25 Pot) ***{Colors.RESET}")
            if self.first_blood_victim is None and not defender.is_player:
                self.first_blood_victim = defender
            if attacker.is_alive:
                stolen_gold = defender.gold // 2
                attacker.gold += stolen_gold
                defender.gold -= stolen_gold
                self.log_event(f"{att_name} claims {stolen_gold} gold from {def_name}!")
                self.loot_gladiator(attacker, defender)
                
        if not attacker.is_alive:
            self.pot += 25
            self.log_event(f"{Colors.GREEN}*** {att_name} HAS FALLEN! The crowd cheers (+25 Pot) ***{Colors.RESET}")
            if self.first_blood_victim is None and not attacker.is_player:
                self.first_blood_victim = attacker
            if defender.is_alive:
                stolen_gold = attacker.gold // 2
                defender.gold += stolen_gold
                attacker.gold -= stolen_gold
                self.log_event(f"{def_name} claims {stolen_gold} gold from {att_name}!")
                self.loot_gladiator(defender, attacker)

        self.sort_gladiators()
        self.render_arena() # Ensure visual GUI updates when AI attacks finish

    def player_reaction(self, attacker: Gladiator) -> str:
        self.render_arena()
        att_name = self.get_idx_name(attacker)
        choice = self.gui_input("REACTION", att_name)
        return 'counter' if choice == '1' else 'defend'

    def preparation_phase(self, gladiator: Gladiator, is_winner: bool) -> None:
        """Handles automatic dynamic stat growth between rounds."""
        # Calculate the delta between their current stats (with looted gear) and their base stats
        delta_atk = max(0, gladiator.atk - gladiator.base_atk)
        delta_def = max(0, gladiator.def_stat - gladiator.base_def_stat)
        
        if is_winner:
            atk_gain = max(2, int(delta_atk ** (1/3)))
            def_gain = max(2, int(delta_atk ** (1/3)))
        else:
            atk_gain = max(1, int(delta_atk ** (1/3)))
            def_gain = max(1, int(delta_def ** (1/3)))
            
        gladiator.base_atk += atk_gain
        gladiator.base_def_stat += def_gain
        
        if gladiator.is_player:
            msg = (
                f"PREPARATION PHASE (Auto-Progression)\n\n"
                f"Attack Growth: {delta_atk} Temp -> +{atk_gain} Permanent Base\n"
                f"Defense Growth: {delta_def} Temp -> +{def_gain} Permanent Base\n\n"
                f"Final Base Attack: {gladiator.base_atk}\n"
                f"Final Base Defense: {gladiator.base_def_stat}"
            )
            self.gui_input("MESSAGE", msg)
                    
    def play(self) -> None:
        while True:
            self.reset_arena()
            self.round_num = 1
            self.log_event(f"Welcome to the ARENA. {len(self.gladiators)} combatants remain!")
            
            player_fallen_msg_shown = False
            
            while len(self.get_alive_gladiators()) > 1:
                if not self.player.is_alive and not player_fallen_msg_shown:
                    self.log_event(f"{Colors.RED}You have fallen! The remaining gladiators finish the match...{Colors.RESET}")
                    player_fallen_msg_shown = True
                    
                if self.player.is_alive:
                    self.log_event(f"\n--- ROUND {self.round_num} BEGINS ---")
                
                loaded_from_menu = False
                
                for gladiator in list(self.get_alive_gladiators()):
                    if not gladiator.is_alive:
                        continue
                        
                    if gladiator.is_player:
                        action = self.player_turn(gladiator)
                        if action == "LOADED":
                            loaded_from_menu = True
                            break
                    else:
                        self.ai_turn(gladiator)
                        
                if loaded_from_menu:
                    continue
                    
                self.round_num += 1
                
            alive = self.get_alive_gladiators()
            
            lines = []
            lines.append("=" * 80)
            winner = None
            if alive:
                winner = alive[0]
                winner_share = int(self.pot * 0.50)
                num_losers = len(self.gladiators) - 1
                loser_share = (self.pot - winner_share) // num_losers if num_losers > 0 else 0
                
                lines.append(f"THE ARENA FALLS SILENT. {winner.name} IS THE VICTOR!".center(80))
                lines.append("=" * 80)
                lines.append(f"Total Pot: {self.pot} Gold")
                lines.append("-" * 80)
                lines.append(f"{winner.name} receives the Champion's Share: {winner_share} Gold!")
                lines.append(f"All other gladiators receive a Consolation Share: {loser_share} Gold.")
                
                winner.gold += winner_share
                for g in self.gladiators:
                    if g != winner:
                        g.gold += loser_share
                        
                if self.first_blood_victim and self.first_blood_victim in self.gladiators:
                    lines.append("-" * 80)
                    lines.append(f"First Blood Penalty: A fallen Gladiator is permanently removed from the games!")
                    self.gladiators.remove(self.first_blood_victim)
            else:
                lines.append("NO COMBATANTS SURVIVED. THE ARENA CLAIMS ALL.".center(80))
                lines.append("=" * 80)
            
            self.ui_queue.put(('RENDER', "\n".join(lines)))
            
            choice = self.gui_input("ROUND_END", {"winner": winner.name if winner else "None", "pot": self.pot, "score": self.player.gold})
            
            if choice == 'Q':
                self.log_event(f"\nThanks for playing Arena! Your Final Score (Gold): {self.player.gold}")
                self.gui_input("EXIT", None)
                break
            else:
                self.log_event("The combatants retreat to the shadows to hone their skills...\n", delay=1.5)
                for g in self.gladiators:
                    # Pass whether this specific gladiator is the winner
                    self.preparation_phase(g, is_winner=(g == winner))

# --- GUI (PYTK APP) ---

class ArenaApp(tk.Tk):
    """The main Tkinter application integrating dual panes and input capture."""
    def __init__(self):
        super().__init__()
        
        self.title("The Arena")
        self.attributes('-fullscreen', True)
        self.configure(bg='black')
        
        self.ui_queue = queue.Queue()
        self.input_event = threading.Event()
        self.game = ArenaGame(self.ui_queue, self.input_event)
        
        # Dictionary to store active keybinds for the current prompt
        self.current_keybinds = {}
        
        self._build_ui()
        
        # Global Key Binds for Keyboard Controls
        self.bind("<Key>", self._handle_keypress)
        self.bind("<Return>", self._handle_return)
        
        self.game_thread = threading.Thread(target=self.game.play, daemon=True)
        self.game_thread.start()
        
        self.after(50, self._poll_queue)

    def _handle_keypress(self, event):
        """Catches character keys (1, 2, 3, S, L, C, Q) and triggers their action."""
        char = event.char.upper()
        if char in self.current_keybinds:
            action = self.current_keybinds[char]
            if callable(action):
                action()
            else:
                self._submit_input(action)

    def _handle_return(self, event):
        """Catches the Enter key specifically for Confirming/Continuing."""
        if "ENTER" in self.current_keybinds:
            action = self.current_keybinds["ENTER"]
            if callable(action):
                action()
            else:
                self._submit_input(action)

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=8, uniform="split") # Left (Arena 75%)
        self.grid_columnconfigure(1, weight=3, uniform="split") # Right (Log 25%)
        
        # Left Panel (Arena Display & Controls)
        self.left_frame = tk.Frame(self, bg='black')
        self.left_frame.grid(row=0, column=0, sticky='nsew')
        
        self.arena_text = tk.Text(self.left_frame, bg='black', fg='white', font=('Courier', 8), state='disabled', bd=0)
        self.arena_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.controls_frame = tk.Frame(self.left_frame, bg='#1a1a1a', bd=4, relief='ridge')
        self.controls_frame.pack(fill='x', side='bottom', padx=10, pady=10)
        
        # Right Panel (Battle Log)
        self.log_frame = tk.Frame(
            self, 
            bg='#111111', 
            highlightthickness=2, 
            highlightbackground='#555555'
        )
        self.log_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        tk.Label(self.log_frame, text="--- BATTLE LOG ---", bg='#111111', fg='#FF55FF', font=('Courier', 14, 'bold')).pack(pady=10)
        self.log_text = scrolledtext.ScrolledText(self.log_frame, bg='#111111', fg='white', font=('Courier', 8), state='disabled', bd=0)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.bind("<Escape>", lambda e: self.destroy())

    def insert_ansi(self, widget: tk.Text, text: str, replace: bool = False):
        """Parses simple terminal ANSI color codes into Tkinter text tags."""
        widget.configure(state='normal')
        if replace:
            widget.delete(1.0, tk.END)
            
        color_map = {
            '31': '#FF5555', '32': '#55FF55', '33': '#FFFF55', '35': '#FF55FF', '38;5;239': '#AAAAAA'
        }
        for code, hex_color in color_map.items():
            widget.tag_configure(code, foreground=hex_color)
            
        parts = re.split(r'\033\[(.*?)m', text)
        current_tag = None
        
        for i, part in enumerate(parts):
            if i % 2 == 1:
                if part == '0':
                    current_tag = None
                elif part in color_map:
                    current_tag = part
                elif part.startswith("38;2;"):
                    try:
                        _, _, r, g, b = part.split(';')
                        hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                        widget.tag_configure(hex_color, foreground=hex_color)
                        current_tag = hex_color
                    except ValueError:
                        pass
            else:
                if part:
                    if current_tag:
                        widget.insert(tk.END, part, (current_tag,))
                    else:
                        widget.insert(tk.END, part)
                        
        if not replace:
            widget.insert(tk.END, '\n')
            widget.see(tk.END)
            
        widget.configure(state='disabled')

    def _create_btn(self, text, command, color='#333333'):
        btn = tk.Button(self.controls_frame, text=text, command=command, bg=color, fg='white', font=('Arial', 12, 'bold'), cursor='hand2')
        btn.pack(fill='x', pady=3, padx=20)
        return btn

    def _submit_input(self, choice):
        # Disable keybinds immediately after a choice is made to prevent double-firing
        self.current_keybinds.clear()
        
        for widget in self.controls_frame.winfo_children():
            widget.destroy()
        tk.Label(self.controls_frame, text="Waiting for simulation...", fg='gray', bg='#1a1a1a', font=('Arial', 12, 'italic')).pack(pady=15)
        
        self.game.user_response = choice
        self.game.input_event.set()

    def show_prompt(self, ptype: str, data: Any):
        """Dynamically generates buttons in the bottom-left pane based on thread input requests."""
        for widget in self.controls_frame.winfo_children():
            widget.destroy()

        # Reset keybinds for the new prompt
        self.current_keybinds.clear()

        if ptype == "MAIN_ACTION":
            tk.Label(self.controls_frame, text="It is your turn! Choose action:", fg='#FF55FF', bg='#1a1a1a', font=('Arial', 14, 'bold')).pack(pady=5)
            self._create_btn("[1] Attack (100% Atk / 50% Def)", lambda: self._submit_input('1'), color='#662222')
            self._create_btn("[2] Defend (100% Def / 50% Atk)", lambda: self._submit_input('2'), color='#226622')
            self._create_btn("[3] Gesture to Crowd (+1% Pot)", lambda: self._submit_input('3'), color='#666622')
            
            save_frame = tk.Frame(self.controls_frame, bg='#1a1a1a')
            save_frame.pack(fill='x', pady=5, padx=20)
            tk.Button(save_frame, text="[S]ave Game", command=lambda: self._submit_input('S'), bg='#222266', fg='white').pack(side='left', expand=True, fill='x', padx=2)
            tk.Button(save_frame, text="[L]oad Game", command=lambda: self._submit_input('L'), bg='#222266', fg='white').pack(side='left', expand=True, fill='x', padx=2)
            
            # Map standard inputs
            self.current_keybinds = {'1': '1', '2': '2', '3': '3', 'S': 'S', 'L': 'L'}

        elif ptype == "TARGET_SELECT":
            tk.Label(self.controls_frame, text="Select target to attack:", fg='white', bg='#1a1a1a', font=('Arial', 12)).pack(pady=5)
            
            target_names = [f"[{idx}] {name}" for idx, name in data]
            target_var = tk.StringVar(value=target_names[0] if target_names else "")
            
            combo = ttk.Combobox(self.controls_frame, textvariable=target_var, values=target_names, state="readonly", font=('Arial', 12))
            combo.pack(fill='x', pady=10, padx=20)
            combo.focus_set() # Puts your keyboard cursor directly into the combo box
            
            def on_confirm():
                selection = target_var.get()
                if selection:
                    idx = selection.split(']')[0][1:]
                    self._submit_input(idx)
                    
            self._create_btn("Confirm Attack [Enter]", on_confirm, color='#882222')
            # Only map Enter here so you can still type numbers into the Combobox search freely
            self.current_keybinds["ENTER"] = on_confirm

        elif ptype == "REACTION":
            tk.Label(self.controls_frame, text=f"!!! {data} is attacking you! !!!", fg='#FF5555', bg='#1a1a1a', font=('Arial', 14, 'bold')).pack(pady=10)
            self._create_btn("[1] Counterattack (-25% Def, +50% Atk)", lambda: self._submit_input('1'), color='#883333')
            self._create_btn("[2] Defend (+50% Def, -25% Atk)", lambda: self._submit_input('2'), color='#338833')
            
            self.current_keybinds = {'1': '1', '2': '2'}

        elif ptype == "LOOT":
            tk.Label(self.controls_frame, text=f"You defeated {data['deceased']}! Scavenge:", fg='#55FF55', bg='#1a1a1a', font=('Arial', 14, 'bold')).pack(pady=10)
            self._create_btn(f"[1] Take Weapon (+{data['atk']} Temp Atk)", lambda: self._submit_input('1'), color='#444444')
            self._create_btn(f"[2] Take Shield (+{data['def']} Temp Def)", lambda: self._submit_input('2'), color='#444444')
            self._create_btn("[3] Leave gear in the dust", lambda: self._submit_input('3'), color='#222222')
            
            self.current_keybinds = {'1': '1', '2': '2', '3': '3'}

        elif ptype == "PREP":
            tk.Label(self.controls_frame, text=f"PREPARATION PHASE\nPoints Remaining: {data['points']}", fg='#FFFF55', bg='#1a1a1a', font=('Arial', 14, 'bold')).pack(pady=10)
            self._create_btn(f"[1] Upgrade Attack (Base: {data['atk']})", lambda: self._submit_input('1'))
            self._create_btn(f"[2] Upgrade Defense (Base: {data['def']})", lambda: self._submit_input('2'))
            
            self.current_keybinds = {'1': '1', '2': '2'}

        elif ptype == "MESSAGE":
            tk.Label(self.controls_frame, text=data, fg='white', bg='#1a1a1a', font=('Arial', 12)).pack(pady=10)
            self._create_btn("Continue [Enter]", lambda: self._submit_input('1'), color='#224466')
            
            self.current_keybinds["ENTER"] = lambda: self._submit_input('1')

        elif ptype == "ROUND_END":
            stats = f"ROUND OVER\n\nWinner: {data['winner']}\nPot: {data['pot']} Gold\nYour Final Gold: {data['score']}"
            tk.Label(self.controls_frame, text=stats, fg='#55FFFF', bg='#1a1a1a', font=('Arial', 12, 'bold')).pack(pady=10)
            self._create_btn("[C]ontinue to Next Round", lambda: self._submit_input('C'), color='#226622')
            self._create_btn("[Q]uit Game", lambda: self._submit_input('Q'), color='#662222')
            
            self.current_keybinds = {'C': 'C', 'Q': 'Q'}

        elif ptype == "EXIT":
            tk.Label(self.controls_frame, text="Game Over. The Application will now close.", fg='white', bg='#1a1a1a', font=('Arial', 12)).pack(pady=20)
            self._create_btn("Exit App [Enter]", self.destroy, color='#882222')
            
            self.current_keybinds["ENTER"] = self.destroy

    def _poll_queue(self):
        try:
            while True:
                msg_type, payload, *rest = self.ui_queue.get_nowait()
                if msg_type == 'LOG':
                    self.insert_ansi(self.log_text, payload, replace=False)
                elif msg_type == 'RENDER':
                    self.insert_ansi(self.arena_text, payload, replace=True)
                elif msg_type == 'PROMPT':
                    context = rest[0] if rest else None
                    self.show_prompt(payload, context)
        except queue.Empty:
            pass
            
        self.after(50, self._poll_queue)

if __name__ == "__main__":
    app = ArenaApp()
    app.mainloop()