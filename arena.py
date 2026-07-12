import random
import time
import os
import json
import re

class Colors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    MAGENTA = '\033[35m'
    GRAY = '\033[38;5;239m'
    RESET = '\033[0m'

class Gladiator:
    def __init__(self, name, is_player=False):
        self.is_player = is_player
        
        # AI Personality Profile dictates their name
        if self.is_player:
            self.personality = "Player"
            self.name = name
        else:
            self.personality = random.choice(["Assassin", "Slayer", "Tactician", "Berserker", "Survivor", "GoldDigger"])
            self.name = self.personality

        self.hp = 100
        
        # Permanent Base Stats
        self.base_atk = random.randint(15, 20)
        self.base_def_stat = random.randint(15, 20)
        
        # Active Combat Stats
        self.atk = self.base_atk
        self.def_stat = self.base_def_stat
        
        # Stance Multipliers
        self.stance = "Neutral"
        self.atk_mult = 1.0
        self.def_mult = 1.0
        
        self.gold = 10 
        self.is_alive = True

    def display_stats(self, index):
        marker = ""
        if self.is_alive:
            if self.stance == "Attack": marker = f"{Colors.RED} (A){Colors.RESET}"
            elif self.stance == "Defend": marker = f"{Colors.GREEN} (D){Colors.RESET}"
            elif self.stance == "Gesture": marker = f"{Colors.YELLOW} (G){Colors.RESET}"
            
        return f"[{index:2}] {self.name:12}: HP {self.hp:3} | Atk {self.atk:2} | Def {self.def_stat:2} | $ {self.gold:3} |{marker}"

class ArenaGame:
    def __init__(self):
        self.pot = 10
        self.messages = []
        self.first_blood_victim = None
        self.round_num = 1
        
        self.gladiators = [Gladiator("Player", is_player=True)]
        self.player = self.gladiators[0]
        for _ in range(19):
            self.gladiators.append(Gladiator("AI")) # Name is overwritten by archetype
            
        if os.name == 'nt':
            os.system('color')

    def save_game(self, filename="arena_save.json"):
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
                    "stance": g.stance,
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

    def load_game(self, filename="arena_save.json"):
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
            g.stance = g_data["stance"]
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

    def get_alive_gladiators(self):
        return [g for g in self.gladiators if g.is_alive]

    def sort_gladiators(self):
        self.gladiators.sort(key=lambda g: (g.is_alive, g.is_player), reverse=True)

    def get_idx_name(self, g):
        if g in self.gladiators:
            idx = self.gladiators.index(g) + 1
            if not g.is_player:
                return f"[{idx}]"
            return f"[{idx}] {g.name}"
        return g.name

    def reset_arena(self):
        self.pot = 10
        self.messages = []
        self.first_blood_victim = None
        for g in self.gladiators:
            g.hp = 100
            g.atk = g.base_atk
            g.def_stat = g.base_def_stat
            g.is_alive = True
            g.stance = "Neutral"
            g.atk_mult = 1.0
            g.def_mult = 1.0
        self.sort_gladiators()

    def log_and_render(self, msg, delay=0):
        if msg:
            self.messages.append(msg)
            if len(self.messages) > 15:
                self.messages.pop(0)
                
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 110)
        print(f"THE ARENA - Current Pot: {self.pot} Gold".center(110))
        print("=" * 110)
        
        def pad_ansi(text, width):
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
        print("BATTLE LOG".center(110))
        print("-" * 110)
        
        for i in range(15):
            if i < len(self.messages):
                print(self.messages[i])
            else:
                print("")
                
        print("=" * 110)
        
        if delay > 0:
            time.sleep(delay)

    def loot_gladiator(self, survivor, deceased):
        atk_boost = max(1, deceased.atk // 4)
        def_boost = max(1, deceased.def_stat // 4)
        
        surv_name = self.get_idx_name(survivor)
        dec_name = self.get_idx_name(deceased)
        
        if survivor.is_player:
            self.log_and_render(f"You stand victorious over a fallen {deceased.name}!", delay=0)
            print(f"1. Take their Weapon (+{atk_boost} Temp Atk)")
            print(f"2. Take their Shield (+{def_boost} Temp Def)")
            print("3. Leave their gear in the dust")
            
            while True:
                choice = input("Scavenge (1-3): ").strip()
                if choice == '1':
                    survivor.atk += atk_boost
                    self.log_and_render(f"You took the weapon! Your Temp Atk is now {survivor.atk}.")
                    break
                elif choice == '2':
                    survivor.def_stat += def_boost
                    self.log_and_render(f"You took the shield! Your Temp Def is now {survivor.def_stat}.")
                    break
                elif choice == '3':
                    self.log_and_render("You respectfully leave the gear untouched.")
                    break
        else:
            if random.random() > 0.5:
                survivor.atk += atk_boost
            else:
                survivor.def_stat += def_boost

    def player_turn(self, player):
        while True:
            self.log_and_render(f"{Colors.MAGENTA}It is your turn!{Colors.RESET}", delay=0)
            print("1. Attack (100% Atk / 50% Def until next turn)")
            print("2. Defend (100% Def / 50% Atk until next turn)")
            print("3. Gesture to Crowd (Increase Pot by 1%)")
            print(f"{Colors.YELLOW}[S]ave Game | [L]oad Game{Colors.RESET}")
            
            choice = input("Choose action (1-3, S, L): ").strip().upper()
            
            if choice == '1':
                player.stance = "Attack"
                player.atk_mult = 1.0
                player.def_mult = 0.5
                self.player_attack_logic(player)
                break
            elif choice == '2':
                player.stance = "Defend"
                player.atk_mult = 0.5
                player.def_mult = 1.0
                self.log_and_render("You take a defensive stance!")
                break
            elif choice == '3':
                player.stance = "Gesture"
                player.atk_mult = 1.0
                player.def_mult = 1.0
                cheer = max(1, int(self.pot * 0.01))
                self.pot += cheer
                self.log_and_render(f"You pump up the crowd! The pot increases by {cheer}!")
                break
            elif choice == 'S':
                self.save_game()
                self.log_and_render(f"{Colors.GREEN}Game saved successfully!{Colors.RESET}", delay=0)
            elif choice == 'L':
                if self.load_game():
                    self.log_and_render(f"{Colors.GREEN}Game loaded successfully!{Colors.RESET}", delay=0)
                    return "LOADED"
                else:
                    self.log_and_render(f"{Colors.RED}No save file found!{Colors.RESET}", delay=0)

    def player_attack_logic(self, player):
        num_glads = len(self.gladiators)
        while True:
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

    def ai_turn(self, ai):
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
            ai.stance = "Attack"
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
            ai.stance = "Defend"
            ai.atk_mult = 0.5
            ai.def_mult = 1.0
            
        elif action == 'gesture':
            ai.stance = "Gesture"
            ai.atk_mult = 1.0
            ai.def_mult = 1.0
            cheer = max(1, int(self.pot * 0.01))
            self.pot += cheer

    def execute_attack(self, attacker, defender):
        att_name = self.get_idx_name(attacker)
        def_name = self.get_idx_name(defender)
        
        involves_player = attacker.is_player or defender.is_player
        
        def c_log(msg, delay=0):
            if involves_player:
                self.log_and_render(msg, delay)
        
        c_log(f"{att_name} attacks {def_name}!")
        
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
            c_log(f"{def_name} chooses to counterattack!")
            final_def_def = def_base_def * 0.75
            final_def_atk = def_base_atk * 1.50
        elif reaction == 'defend':
            c_log(f"{def_name} blocks and strikes back!")
            final_def_def = def_base_def * 1.50
            final_def_atk = def_base_atk * 0.75
            
        # Step 1: Attacker hits Defender
        dmg_in = max(0, int(att_atk - final_def_def))
        defender.hp = max(0, defender.hp - dmg_in)
        if defender.hp == 0:
            defender.is_alive = False
            
        c_log(f"{att_name} hits for {dmg_in} damage!")
        
        if dmg_in == 0:
            self.pot += 2
            c_log(f"{Colors.GREEN}FLAWLESS DEFENSE! The crowd throws 2 gold into the pot!{Colors.RESET}")
            
        # Step 2: Defender strikes back (if they survive)
        if defender.is_alive:
            dmg_out = max(0, int(final_def_atk - att_def))
            attacker.hp = max(0, attacker.hp - dmg_out)
            if attacker.hp == 0:
                attacker.is_alive = False
                
            c_log(f"{def_name} hits back for {dmg_out} damage!")
            
            if dmg_out == 0:
                self.pot += 2
                c_log(f"{Colors.GREEN}FLAWLESS DEFENSE! The crowd throws 2 gold into the pot!{Colors.RESET}")

        # Process deaths, stealing gold, and looting
        if not defender.is_alive:
            self.pot += 25
            c_log(f"{Colors.GREEN}*** {def_name} HAS FALLEN! The crowd cheers (+25 Pot) ***{Colors.RESET}", delay=0)
            if self.first_blood_victim is None and not defender.is_player:
                self.first_blood_victim = defender
            if attacker.is_alive:
                stolen_gold = defender.gold // 2
                attacker.gold += stolen_gold
                defender.gold -= stolen_gold
                c_log(f"{att_name} claims {stolen_gold} gold from {def_name}!", delay=0)
                self.loot_gladiator(attacker, defender)
                
        if not attacker.is_alive:
            self.pot += 25
            c_log(f"{Colors.GREEN}*** {att_name} HAS FALLEN! The crowd cheers (+25 Pot) ***{Colors.RESET}", delay=0)
            if self.first_blood_victim is None and not attacker.is_player:
                self.first_blood_victim = attacker
            if defender.is_alive:
                stolen_gold = attacker.gold // 2
                defender.gold += stolen_gold
                attacker.gold -= stolen_gold
                c_log(f"{def_name} claims {stolen_gold} gold from {att_name}!", delay=0)
                self.loot_gladiator(defender, attacker)

        self.sort_gladiators()

    def player_reaction(self, attacker):
        att_name = self.get_idx_name(attacker)
        self.log_and_render(f"{Colors.RED}!!! An enemy {att_name} is attacking you! !!!{Colors.RESET}", delay=0)
        print("1. Counterattack (Take damage at -25% Def, hit back +50% Atk)")
        print("2. Defend (Take damage at +50% Def, hit back at -25% Atk)")
        
        while True:
            choice = input("Reaction (1-2): ").strip()
            if choice == '1':
                return 'counter'
            elif choice == '2':
                return 'defend'

    def preparation_phase(self, winner):
        points = 4
        
        if winner.is_player:
            while points > 0:
                os.system('cls' if os.name == 'nt' else 'clear')
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
                    
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 60)
            print("PREPARATION COMPLETE".center(60))
            print("=" * 60)
            print(f"Final Base Attack:  {winner.base_atk}")
            print(f"Final Base Defense: {winner.base_def_stat}")
            print("=" * 60)
            input("\nPress Enter to return to the Arena...")
            
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
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

    def play(self):
        while True:
            self.reset_arena()
            self.round_num = 1
            self.log_and_render(f"Welcome to the ARENA. {len(self.gladiators)} combatants remain!", delay=0)
            
            player_fallen_msg_shown = False
            
            while len(self.get_alive_gladiators()) > 1:
                if not self.player.is_alive and not player_fallen_msg_shown:
                    self.log_and_render(f"{Colors.RED}You have fallen! The remaining gladiators finish the match...{Colors.RESET}", delay=5.0)
                    player_fallen_msg_shown = True
                    
                if self.player.is_alive:
                    self.log_and_render(f"--- ROUND {self.round_num} BEGINS ---")
                
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
            os.system('cls' if os.name == 'nt' else 'clear')
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

if __name__ == "__main__":
    game = ArenaGame()
    game.play()