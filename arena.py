import random
import time
import os
import sys
import json
import re
import subprocess
import shutil
from typing import List, Optional, Dict, Any
from enum import Enum

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
        
        # AI Personality Profile dictates their name
        if self.is_player:
            self.personality = "Player"
            self.name = name
        else:
            self.personality = random.choice(["Assassin", "Slayer", "Tactician", "Berserker", "Survivor", "GoldDigger"])
            self.name = self.personality

        self.hp: int = 100
        
        # Permanent Base Stats
        self.base_atk: int = random.randint(15, 20)
        self.base_def_stat: int = random.randint(15, 20)
        
        # Active Combat Stats
        self.atk: int = self.base_atk
        self.def_stat: int = self.base_def_stat
        
        # Stance Multipliers
        self.stance: Stance = Stance.NEUTRAL
        self.atk_mult: float = 1.0
        self.def_mult: float = 1.0
        
        self.gold: int = 10 
        self.is_alive: bool = True

    def display_stats(self, index: int) -> str:
        """Returns a formatted string of the gladiator's current combat statistics."""
        marker = ""
        if self.is_alive:
            if self.stance == Stance.ATTACK: marker = f"{Colors.RED} (A){Colors.RESET}"
            elif self.stance == Stance.DEFEND: marker = f"{Colors.GREEN} (D){Colors.RESET}"
            elif self.stance == Stance.GESTURE: marker = f"{Colors.YELLOW} (G){Colors.RESET}"
            
        return f"[{index:2}] {self.name:12}: HP {self.hp:3} | Atk {self.atk:2} | Def {self.def_stat:2} | $ {self.gold:3} |{marker}"


class ArenaGame:
    """Main controller for the Arena combat simulation."""
    
    def __init__(self) -> None:
        self.pot: int = 10
        self.first_blood_victim: Optional[Gladiator] = None
        self.round_num: int = 1
        self.log_file: str = "arena_battle_log.txt"
        
        self.gladiators: List[Gladiator] = [Gladiator("Player", is_player=True)]
        self.player: Gladiator = self.gladiators[0]
        
        for _ in range(19):
            self.gladiators.append(Gladiator("AI")) # Name is overwritten by archetype
            
        if os.name == 'nt':
            os.system('color')
            
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"{Colors.MAGENTA}--- BATTLE LOG INITIALIZED ---{Colors.RESET}\n")

    def _clear_screen(self) -> None:
        """Helper method to clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def launch_log_window(self) -> None:
        """Spawns the secondary log viewer process in a new terminal."""
        script_path = os.path.abspath(__file__)
        if os.name == 'nt':
            subprocess.Popen(['start', 'cmd', '/c', sys.executable, script_path, '--log-viewer'], shell=True)
        else:
            terminals = ['x-terminal-emulator', 'gnome-terminal', 'xterm', 'konsole']
            for term in terminals:
                if shutil.which(term):
                    if term in ['gnome-terminal', 'x-terminal-emulator']:
                        subprocess.Popen([term, '--', sys.executable, script_path, '--log-viewer'])
                    else:
                        subprocess.Popen([term, '-e', f'{sys.executable} {script_path} --log-viewer'])
                    return
            print("Warning: Could not launch log window automatically. Run 'python arena.py --log-viewer'.")

    def save_game(self, filename: str = "arena_save.json") -> None:
        """Serializes the current game state to a JSON file."""
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
        """Deserializes game state from a JSON file. Returns True if successful."""
        if not os.path.exists(filename):
            return False
            
        with open(filename, "r") as f:
            state = json.load(f)
        
        self.pot = state.get("pot", 10)
        self.round_num = state.get("round_num", 1)
        
        self.gladiators = []
        for g_data in state.get("gladiators", []):
            g = Gladiator(g_data["name"], g_data["is_player"])
            g.name = g_data["name"] # Override random init
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
        """Returns a list of all currently living gladiators."""
        return [g for g in self.gladiators if g.is_alive]

    def sort_gladiators(self) -> None:
        self.gladiators.sort(key=lambda g: (g.is_alive, g.is_player), reverse=True)

    def get_idx_name(self, g: Gladiator) -> str:
        """Retrieves formatted display name with index for rendering logs."""
        if g in self.gladiators:
            idx = self.gladiators.index(g) + 1
            if not g.is_player:
                return f"[{idx}]"
            return f"[{idx}] {g.name}"
        return g.name

    def reset_arena(self) -> None:
        """Resets arena state for a new round of combat."""
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
        """Writes a message to the external battle log."""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
        if delay > 0:
            time.sleep(delay)

    def render_arena(self) -> None:
        """Renders the gladiator stats in the primary window."""
        self._clear_screen()
        
        print("=" * 110)
        print(f"THE ARENA - Current Pot: {self.pot} Gold".center(110))
        print("=" * 110)
        
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
                
            left_str_raw = pad_ansi(left_str_raw, 75)
                
            right_idx = i + num_rows
            if right_idx < num_glads:
                right_glad = self.gladiators[right_idx]
                right_str_raw = right_glad.display_stats(right_idx + 1)
                if not right_glad.is_alive:
                    right_str_raw = f"{Colors.GRAY}{right_str_raw}{Colors.RESET}"
                print(f"{left_str_raw} ||   {right_str_raw}")
            else:
                print(f"{left_str_raw} ||")
            
        print("=" * 110)
        print("BATTLE LOG FORKED TO EXTERNAL WINDOW".center(110))
        print("=" * 110)

    def loot_gladiator(self, survivor: Gladiator, deceased: Gladiator) -> None:
        """Processes gear upgrades when one gladiator defeats another."""
        atk_boost = max(1, deceased.atk // 4)
        def_boost = max(1, deceased.def_stat // 4)
        
        if survivor.is_player:
            self.render_arena()
            print(f"{Colors.GREEN}You stand victorious over a fallen {deceased.name}!{Colors.RESET}")
            print(f"1. Take their Weapon (+{atk_boost} Temp Atk)")
            print(f"2. Take their Shield (+{def_boost} Temp Def)")
            print("3. Leave their gear in the dust")
            
            while True:
                choice = input("Scavenge (1-3): ").strip()
                if choice == '1':
                    survivor.atk += atk_boost
                    self.log_event(f"Player took the weapon! Temp Atk is now {survivor.atk}.")
                    break
                elif choice == '2':
                    survivor.def_stat += def_boost
                    self.log_event(f"Player took the shield! Temp Def is now {survivor.def_stat}.")
                    break
                elif choice == '3':
                    self.log_event("Player respectfully leaves the gear untouched.")
                    break
        else:
            if random.random() > 0.5:
                survivor.atk += atk_boost
            else:
                survivor.def_stat += def_boost

    def player_turn(self, player: Gladiator) -> Optional[str]:
        """Handles input and logic for the player's turn."""
        while True:
            self.render_arena()
            print(f"{Colors.MAGENTA}It is your turn!{Colors.RESET}")
            print("1. Attack (100% Atk / 50% Def until next turn)")
            print("2. Defend (100% Def / 50% Atk until next turn)")
            print("3. Gesture to Crowd (Increase Pot by 1%)")
            print(f"{Colors.YELLOW}[S]ave Game | [L]oad Game{Colors.RESET}")
            
            choice = input("Choose action (1-3, S, L): ").strip().upper()
            
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
                self.log_event("Game saved successfully.")
            elif choice == 'L':
                if self.load_game():
                    self.log_event("Game loaded successfully.")
                    return "LOADED"
                else:
                    print(f"{Colors.RED}No save file found!{Colors.RESET}")
        return None

    def player_attack_logic(self, player: Gladiator) -> None:
        num_glads = len(self.gladiators)
        while True:
            self.render_arena()
            try:
                target_idx = int(input(f"Select target by number (1-{num_glads}): ")) - 1
                if target_idx < 0 or target_idx >= num_glads:
                    print("Invalid number.")
                    continue
                
                target = self.gladiators[target_idx]
                if target == player:
                    print("You cannot attack yourself.")
                    continue
                if not target.is_alive:
                    print("That gladiator is already dead.")
                    continue
                    
                self.execute_attack(player, target)
                break
            except ValueError:
                print("Please enter a valid number.")

    def ai_turn(self, ai: Gladiator) -> None:
        alive = self.get_alive_gladiators()
        targets = [g for g in alive if g != ai]
        
        if not targets:
            return

        # Base decision weights
        weights = {'attack': 60, 'defend': 20, 'gesture': 20}
        
        # Modify weights based on personality and current HP
        if ai.hp < 40 or ai.personality == "Survivor":
            weights['defend'] += 40
            weights['attack'] -= 20
        
        if ai.personality == "Berserker":
            weights['attack'] += 30
            weights['defend'] -= 15
            weights['gesture'] -= 10
            
        # Ensure no negative weights
        w_vals = [max(1, w) for w in weights.values()]
        action = random.choices(list(weights.keys()), weights=w_vals)[0]
        
        if action == 'attack':
            ai.stance = Stance.ATTACK
            ai.atk_mult = 1.0
            ai.def_mult = 0.5
            
            # Smart Target Selection based on Personality
            if ai.personality == "Assassin":
                target = min(targets, key=lambda t: t.hp)
            elif ai.personality == "Slayer":
                target = max(targets, key=lambda t: t.hp)
            elif ai.personality == "Tactician":
                target = min(targets, key=lambda t: t.def_stat * t.def_mult)
            elif ai.personality == "GoldDigger":
                # Targets 1 of the 5 wealthiest gladiators
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
        """Helper method to encapsulate damage application and HP floor bounding."""
        dmg = max(0, int(dmg_calc))
        target.hp = max(0, target.hp - dmg)
        if target.hp == 0:
            target.is_alive = False
        return dmg

    def execute_attack(self, attacker: Gladiator, defender: Gladiator) -> None:
        """Resolves an attack action between two combatants."""
        att_name = self.get_idx_name(attacker)
        def_name = self.get_idx_name(defender)
        
        involves_player = attacker.is_player or defender.is_player
        
        self.log_event(f"{att_name} attacks {def_name}!")
        
        # Base active stats for Attacker
        att_atk = attacker.atk * attacker.atk_mult
        att_def = attacker.def_stat * attacker.def_mult
        
        # Base active stats for Defender
        def_base_atk = defender.atk * defender.atk_mult
        def_base_def = defender.def_stat * defender.def_mult

        if defender.is_player:
            reaction = self.player_reaction(attacker)
        else:
            # Smart AI Reactions
            if defender.hp < 30 or defender.personality == "Survivor":
                reaction = 'defend'
            elif defender.personality == "Berserker":
                reaction = 'counter'
            elif defender.personality == "Tactician":
                # Will the incoming attack hurt significantly?
                if (att_atk - (def_base_def * 0.75)) > 15:
                    reaction = 'defend' # Brace for impact
                else:
                    reaction = 'counter' # Take the small hit and strike back
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
            
        # Step 1: Attacker hits Defender
        dmg_in = self._apply_damage(defender, att_atk - final_def_def)
            
        self.log_event(f"{att_name} hits for {dmg_in} damage!", delay=0.1)
        
        if dmg_in == 0:
            self.pot += 2
            self.log_event(f"{Colors.GREEN}FLAWLESS DEFENSE! The crowd throws 2 gold into the pot!{Colors.RESET}")
            
        # Step 2: Defender strikes back (if they survive)
        if defender.is_alive:
            dmg_out = self._apply_damage(attacker, final_def_atk - att_def)
                
            self.log_event(f"{def_name} hits back for {dmg_out} damage!", delay=0.1)
            
            if dmg_out == 0:
                self.pot += 2
                self.log_event(f"{Colors.GREEN}FLAWLESS DEFENSE! The crowd throws 2 gold into the pot!{Colors.RESET}")

        # Process deaths, stealing gold, and looting
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

    def player_reaction(self, attacker: Gladiator) -> str:
        self.render_arena()
        att_name = self.get_idx_name(attacker)
        print(f"{Colors.RED}!!! An enemy {att_name} is attacking you! !!!{Colors.RESET}")
        print("1. Counterattack (Take damage at -25% Def, hit back +50% Atk)")
        print("2. Defend (Take damage at +50% Def, hit back at -25% Atk)")
        
        while True:
            choice = input("Reaction (1-2): ").strip()
            if choice == '1':
                return 'counter'
            elif choice == '2':
                return 'defend'

    def preparation_phase(self, winner: Gladiator) -> None:
        points = 4
        
        if winner.is_player:
            while points > 0:
                self._clear_screen()
                print("=" * 60)
                print("PREPARATION PHASE".center(60))
                print("=" * 60)
                print(f"You are the Champion! You have {points} stat points to spend.")
                print("-" * 60)
                print(f"1. Upgrade Attack  (Current Base: {winner.base_atk})")
                print(f"2. Upgrade Defense (Current Base: {winner.base_def_stat})")
                print("=" * 60)
                
                choice = input("Select a stat to upgrade (1-2): ").strip()
                if choice == '1':
                    winner.base_atk += 1
                    points -= 1
                elif choice == '2':
                    winner.base_def_stat += 1
                    points -= 1
                    
            self._clear_screen()
            print("=" * 60)
            print("PREPARATION COMPLETE".center(60))
            print("=" * 60)
            print(f"Final Base Attack:  {winner.base_atk}")
            print(f"Final Base Defense: {winner.base_def_stat}")
            print("=" * 60)
            input("\nPress Enter to return to the Arena...")
            
        else:
            self._clear_screen()
            print("=" * 60)
            print("PREPARATION PHASE".center(60))
            print("=" * 60)
            print(f"The Champion {winner.name} hones their skills in the shadows...")
            
            for _ in range(points):
                if random.random() > 0.5:
                    winner.base_atk += 1
                else:
                    winner.base_def_stat += 1
                    
            print("=" * 60)
            input("\nPress Enter to return to the Arena...")

    def play(self) -> None:
        """Main game loop handler."""
        self.launch_log_window()
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
            self._clear_screen()
            print("=" * 60)
            
            winner = None
            if alive:
                winner = alive[0]
                winner_share = int(self.pot * 0.50)
                
                num_losers = len(self.gladiators) - 1
                loser_share = (self.pot - winner_share) // num_losers if num_losers > 0 else 0
                
                print(f"THE ARENA FALLS SILENT. {winner.name} IS THE VICTOR!".center(60))
                print("=" * 60)
                print(f"Total Pot: {self.pot} Gold")
                print("-" * 60)
                print(f"{winner.name} receives the Champion's Share: {winner_share} Gold!")
                print(f"All other gladiators receive a Consolation Share: {loser_share} Gold.")
                
                winner.gold += winner_share
                for g in self.gladiators:
                    if g != winner:
                        g.gold += loser_share
                        
                if self.first_blood_victim and self.first_blood_victim in self.gladiators:
                    print("-" * 60)
                    print(f"First Blood Penalty: A fallen Gladiator is permanently removed from the games!")
                    self.gladiators.remove(self.first_blood_victim)
            else:
                print("NO COMBATANTS SURVIVED. THE ARENA CLAIMS ALL.".center(60))
                print("=" * 60)
                
            print("=" * 60)
            
            while True:
                q_c = input("\n[Q]uit or [C]ontinue? ").strip().upper()
                if q_c in ['Q', 'C']:
                    break
            
            if q_c == 'Q':
                print(f"\nThanks for playing Arena! Your Final Score (Gold): {self.player.gold}")
                break
            else:
                if winner:
                    self.preparation_phase(winner)

def run_log_viewer() -> None:
    """Standalone loop to tail the battle log file."""
    if os.name == 'nt':
        os.system('color')
    print(f"{Colors.YELLOW}--- EXTERNAL BATTLE LOG ---{Colors.RESET}")
    print("Waiting for events...\n")
    
    log_file = "arena_battle_log.txt"
    if not os.path.exists(log_file):
        open(log_file, 'w').close()
        
    with open(log_file, 'r', encoding='utf-8') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.05)
                continue
            sys.stdout.write(line)
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--log-viewer':
        try:
            run_log_viewer()
        except KeyboardInterrupt:
            sys.exit(0)
    else:
        game = ArenaGame()
        game.play()