import random
import time
import os

class Gladiator:
    def __init__(self, name, is_player=False):
        self.name = name
        self.is_player = is_player
        self.hp = 100
        
        # Permanent Base Stats
        self.base_atk = random.randint(10, 15)
        self.base_def_stat = random.randint(10, 15)
        
        # Active Combat Stats (Can be temporarily boosted by looting)
        self.atk = self.base_atk
        self.def_stat = self.base_def_stat
        
        # Gold is now a high score/bounty mechanic
        self.gold = 10 
        self.is_defending = False
        self.is_alive = True

    def display_stats(self, index):
        def_marker = " (D)" if self.is_defending and self.is_alive else ""
        return f"[{index:2}] {self.name:12}: HP {self.hp:3} Atk {self.atk:2} Def {self.def_stat:2} ${self.gold:3}{def_marker}"

    def take_damage(self, amount, on_the_fly_defend=False):
        mitigation = 0
        if self.is_defending:
            mitigation += self.def_stat
        if on_the_fly_defend:
            mitigation += (self.def_stat * 0.5)
            
        actual_damage = max(0, int(amount - mitigation))
        self.hp -= actual_damage
        
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
            self.is_defending = False
            
        return actual_damage

class ArenaGame:
    def __init__(self):
        self.pot = 10
        self.messages = []
        self.first_blood_victim = None
        
        # Initialize gladiators. All AI are just named "Gladiator".
        self.gladiators = [Gladiator("Player", is_player=True)]
        self.player = self.gladiators[0]
        for _ in range(19):
            self.gladiators.append(Gladiator("Gladiator"))
            
        if os.name == 'nt':
            os.system('color')

    def get_alive_gladiators(self):
        return [g for g in self.gladiators if g.is_alive]

    def sort_gladiators(self):
        # Sorts living to the top, dead to the bottom. Player takes priority at the very top.
        self.gladiators.sort(key=lambda g: (g.is_alive, g.is_player), reverse=True)

    def get_idx_name(self, g):
        """Helper function to dynamically get the gladiator's current roster number for the log."""
        if g in self.gladiators:
            idx = self.gladiators.index(g) + 1
            if g.name == "Gladiator":
                return f"[{idx}]"
            return f"[{idx}] {g.name}"
        return g.name

    def reset_arena(self):
        self.pot = 10
        self.messages = []
        self.first_blood_victim = None
        for g in self.gladiators:
            g.hp = 100
            # Strip scavenged gear, reset to permanent upgraded stats
            g.atk = g.base_atk
            g.def_stat = g.base_def_stat
            g.is_alive = True
            g.is_defending = False
        self.sort_gladiators()

    def log_and_render(self, msg, delay=0.3):
        if msg:
            self.messages.append(msg)
            if len(self.messages) > 5:
                self.messages.pop(0)
                
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Widened to 110 to accommodate the gold display
        print("=" * 110)
        print(f"THE ARENA - Current Pot: {self.pot} Gold".center(110))
        print("=" * 110)
        
        # Dynamic Row Calculation based on shrinking roster
        num_glads = len(self.gladiators)
        num_rows = (num_glads + 1) // 2
        
        for i in range(num_rows):
            left_glad = self.gladiators[i]
            left_str_raw = f"{left_glad.display_stats(i + 1):<51}"
            if not left_glad.is_alive:
                left_str_raw = f"\033[90m{left_str_raw}\033[0m"
                
            right_idx = i + num_rows
            if right_idx < num_glads:
                right_glad = self.gladiators[right_idx]
                right_str_raw = right_glad.display_stats(right_idx + 1)
                if not right_glad.is_alive:
                    right_str_raw = f"\033[90m{right_str_raw}\033[0m"
                print(f"{left_str_raw} |   {right_str_raw}")
            else:
                # If odd number of gladiators, the last row only has a left column
                print(f"{left_str_raw} |")
            
        print("=" * 110)
        print("BATTLE LOG".center(110))
        print("-" * 110)
        
        for i in range(5):
            if i < len(self.messages):
                print(self.messages[i])
            else:
                print("")
                
        print("=" * 110)
        
        if delay > 0:
            time.sleep(delay)

    def loot_gladiator(self, survivor, deceased):
        atk_boost = max(1, deceased.atk // 3)
        def_boost = max(1, deceased.def_stat // 3)
        
        surv_name = self.get_idx_name(survivor)
        dec_name = self.get_idx_name(deceased)
        
        if survivor.is_player:
            self.log_and_render(f"You stand victorious over a fallen {dec_name}!", delay=0)
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
                self.log_and_render(f"{surv_name} scavenges a weapon (+{atk_boost} Temp Atk).")
            else:
                survivor.def_stat += def_boost
                self.log_and_render(f"{surv_name} scavenges a shield (+{def_boost} Temp Def).")

    def player_turn(self, player):
        self.log_and_render("It is your turn!", delay=0)
        print("1. Attack")
        print("2. Defend (100% Def until next turn)")
        print("3. Gesture to Crowd (Increase Pot by 1%)")
        
        while True:
            choice = input("Choose action (1-3): ").strip()
            if choice == '1':
                self.player_attack_logic(player)
                break
            elif choice == '2':
                player.is_defending = True
                self.log_and_render("You raise your shield! (Defense maximized)")
                break
            elif choice == '3':
                cheer = max(1, int(self.pot * 0.01))
                self.pot += cheer
                self.log_and_render(f"You pump up the crowd! The pot increases by {cheer}!")
                break

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
        action = random.choices(['attack', 'defend', 'gesture'], weights=[60, 20, 20])[0]
        ai_name = self.get_idx_name(ai)
        
        if action == 'attack':
            alive = self.get_alive_gladiators()
            targets = [g for g in alive if g != ai]
            if targets:
                target = random.choice(targets)
                self.execute_attack(ai, target)
        elif action == 'defend':
            ai.is_defending = True
            self.log_and_render(f"{ai_name} takes a defensive stance.")
        elif action == 'gesture':
            cheer = max(1, int(self.pot * 0.01))
            self.pot += cheer
            self.log_and_render(f"{ai_name} gestures to the crowd. Pot +{cheer}.")

    def execute_attack(self, attacker, defender):
        att_name = self.get_idx_name(attacker)
        def_name = self.get_idx_name(defender)
        
        self.log_and_render(f"{att_name} attacks {def_name}!")
        
        if defender.is_player:
            reaction = self.player_reaction(attacker)
        else:
            reaction = random.choice(['counter', 'defend'])
            
        if reaction == 'defend':
            self.log_and_render(f"{def_name} tries to block the blow on the fly!")
            dmg = defender.take_damage(attacker.atk, on_the_fly_defend=True)
            self.log_and_render(f"{att_name} hits for {dmg} damage!")
            
            if dmg == 0:
                self.pot += 10
                self.log_and_render(f"FLAWLESS DEFENSE! The crowd throws 10 gold into the pot!")
            
        elif reaction == 'counter':
            self.log_and_render(f"{def_name} chooses to counterattack!")
            dmg_in = defender.take_damage(attacker.atk, on_the_fly_defend=False)
            self.log_and_render(f"{att_name} hits for {dmg_in} damage!")
            
            if dmg_in == 0 and defender.is_defending:
                self.pot += 10
                self.log_and_render(f"FLAWLESS DEFENSE! The crowd throws 10 gold into the pot!")
            
            if defender.is_alive:
                dmg_out = attacker.take_damage(defender.atk, on_the_fly_defend=False)
                self.log_and_render(f"{def_name} hits back for {dmg_out} damage!")
                
                if dmg_out == 0 and attacker.is_defending:
                    self.pot += 10
                    self.log_and_render(f"FLAWLESS DEFENSE! The crowd throws 10 gold into the pot!")

        # Process deaths, stealing gold, and looting
        if not defender.is_alive:
            self.pot += 25
            self.log_and_render(f"*** {def_name} HAS FALLEN! The crowd cheers (+25 Pot) ***", delay=1.0)
            if self.first_blood_victim is None and not defender.is_player:
                self.first_blood_victim = defender
            if attacker.is_alive:
                stolen_gold = defender.gold // 2
                attacker.gold += stolen_gold
                defender.gold -= stolen_gold
                self.log_and_render(f"{att_name} claims {stolen_gold} gold from {def_name}!", delay=0.5)
                self.loot_gladiator(attacker, defender)
                
        if not attacker.is_alive:
            self.pot += 25
            self.log_and_render(f"*** {att_name} HAS FALLEN! The crowd cheers (+25 Pot) ***", delay=1.0)
            if self.first_blood_victim is None and not attacker.is_player:
                self.first_blood_victim = attacker
            if defender.is_alive:
                stolen_gold = attacker.gold // 2
                defender.gold += stolen_gold
                attacker.gold -= stolen_gold
                self.log_and_render(f"{def_name} claims {stolen_gold} gold from {att_name}!", delay=0.5)
                self.loot_gladiator(defender, attacker)

        # Sort the roster immediately after someone dies to dynamically update the list
        self.sort_gladiators()

    def player_reaction(self, attacker):
        att_name = self.get_idx_name(attacker)
        self.log_and_render(f"!!! An enemy {att_name} is attacking you! !!!", delay=0)
        print("1. Counterattack (Take normal damage, hit back)")
        print("2. Defend on the fly (Reduce incoming damage by 50% Def)")
        
        while True:
            choice = input("Reaction (1-2): ").strip()
            if choice == '1':
                return 'counter'
            elif choice == '2':
                return 'defend'

    def preparation_phase(self, winner):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 60)
        print("PREPARATION PHASE".center(60))
        print("=" * 60)
        print(f"The Champion {winner.name} hones their skills!")
        print("Base Attack increases by 1!")
        print("Base Defense increases by 1!")
        print("=" * 60)
        
        # Apply the winner's stat bump
        winner.base_atk += 1
        winner.base_def_stat += 1
        
        input("\nPress Enter to return to the Arena...")

    def play(self):
        while True:
            self.reset_arena()
            self.log_and_render(f"Welcome to the ARENA. {len(self.gladiators)} combatants remain!", delay=2.0)
            
            round_num = 1
            while len(self.get_alive_gladiators()) > 1:
                if not self.player.is_alive:
                    self.log_and_render("You have fallen in the Arena...", delay=0)
                    break
                    
                self.log_and_render(f"--- ROUND {round_num} BEGINS ---")
                
                # Copy the list for iteration so dynamic sorting doesn't skip turns
                for gladiator in list(self.get_alive_gladiators()):
                    if not gladiator.is_alive:
                        continue
                        
                    gladiator.is_defending = False
                    
                    if gladiator.is_player:
                        self.player_turn(gladiator)
                    else:
                        self.ai_turn(gladiator)
                        
                round_num += 1
                
            alive = self.get_alive_gladiators()
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 60)
            
            winner = None
            if alive:
                winner = alive[0]
                print(f"THE ARENA FALLS SILENT. {winner.name} IS THE VICTOR!".center(60))
                print("=" * 60)
                print(f"{winner.name} takes the Grand Pot: {self.pot} Gold!")
                
                # Winner takes the entire pot
                winner.gold += self.pot
                        
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
            
            if q_c == 'Q' or not self.player.is_alive:
                print(f"\nThanks for playing Arena! Your Final Score (Gold): {self.player.gold}")
                break
            else:
                if winner:
                    self.preparation_phase(winner)

if __name__ == "__main__":
    game = ArenaGame()
    game.play()