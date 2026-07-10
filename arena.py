import random
import time
import os

class Gladiator:
    def __init__(self, name, is_player=False):
        self.name = name
        self.is_player = is_player
        self.hp = 100
        self.atk = random.randint(15, 30)
        self.def_stat = random.randint(10, 20)
        self.is_defending = False
        self.is_alive = True

    def display_stats(self, index):
        # We no longer replace the string with "DEAD"
        # We just format it normally (HP will naturally be 0)
        def_marker = " (D)" if self.is_defending and self.is_alive else ""
        return f"[{index:2}] {self.name:12}: HP {self.hp:3} Def {self.def_stat:2} Atk {self.atk:2}{def_marker}"

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
        self.pot = 1000
        self.messages = []
        
        self.gladiators = [Gladiator("Player", is_player=True)]
        for i in range(2, 21):
            self.gladiators.append(Gladiator(f"Gladiator {i}"))
            
        # Enable ANSI colors on Windows just in case
        if os.name == 'nt':
            os.system('color')

    def get_alive_gladiators(self):
        return [g for g in self.gladiators if g.is_alive]

    def log_and_render(self, msg, delay=0.6):
        if msg:
            self.messages.append(msg)
            if len(self.messages) > 5:
                self.messages.pop(0)
                
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # --- DRAW HEADER ---
        print("=" * 100)
        print(f"THE ARENA - Current Pot: {self.pot} Gold".center(100))
        print("=" * 100)
        
        # --- DRAW GLADIATORS (With ANSI Gray for Dead) ---
        for i in range(10):
            left_glad = self.gladiators[i]
            right_glad = self.gladiators[i + 10]
            
            # Format the raw strings first to ensure padding doesn't count invisible ANSI codes
            left_str_raw = f"{left_glad.display_stats(i + 1):<47}"
            right_str_raw = right_glad.display_stats(i + 11)
            
            # Wrap in dark gray (\033[90m) if dead, then reset (\033[0m)
            if not left_glad.is_alive:
                left_str_raw = f"\033[90m{left_str_raw}\033[0m"
            if not right_glad.is_alive:
                right_str_raw = f"\033[90m{right_str_raw}\033[0m"
                
            print(f"{left_str_raw} |   {right_str_raw}")
            
        # --- DRAW MESSAGE LOG ---
        print("=" * 100)
        print("BATTLE LOG".center(100))
        print("-" * 100)
        
        for i in range(5):
            if i < len(self.messages):
                print(self.messages[i])
            else:
                print("")
                
        print("=" * 100)
        
        if delay > 0:
            time.sleep(delay)

    def loot_gladiator(self, survivor, deceased):
        # Calculate a slight stat boost based on the fallen enemy's gear
        atk_boost = max(1, deceased.atk // 4)
        def_boost = max(1, deceased.def_stat // 4)
        
        if survivor.is_player:
            self.log_and_render(f"You stand victorious over {deceased.name}!", delay=0)
            print(f"1. Take their Weapon (+{atk_boost} Atk)")
            print(f"2. Take their Shield (+{def_boost} Def)")
            print("3. Leave their gear in the dust")
            
            while True:
                choice = input("Scavenge (1-3): ").strip()
                if choice == '1':
                    survivor.atk += atk_boost
                    self.log_and_render(f"You took the weapon! Your Atk is now {survivor.atk}.")
                    break
                elif choice == '2':
                    survivor.def_stat += def_boost
                    self.log_and_render(f"You took the shield! Your Def is now {survivor.def_stat}.")
                    break
                elif choice == '3':
                    self.log_and_render("You respectfully leave the gear untouched.")
                    break
        else:
            # AI randomly decides what to loot
            if random.random() > 0.5:
                survivor.atk += atk_boost
                self.log_and_render(f"{survivor.name} scavenges a weapon from {deceased.name} (+{atk_boost} Atk).")
            else:
                survivor.def_stat += def_boost
                self.log_and_render(f"{survivor.name} scavenges a shield from {deceased.name} (+{def_boost} Def).")

    def player_turn(self, player):
        self.log_and_render("It is your turn!", delay=0)
        print("1. Attack")
        print("2. Defend (100% Def until next turn)")
        print("3. Gesture to Crowd (Increase Pot)")
        
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
                cheer = random.randint(100, 500)
                self.pot += cheer
                self.log_and_render(f"You pump up the crowd! The pot increases by {cheer}!")
                break

    def player_attack_logic(self, player):
        while True:
            try:
                target_idx = int(input("Select target by number (1-20): ")) - 1
                if target_idx < 0 or target_idx >= 20:
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
        
        if action == 'attack':
            alive = self.get_alive_gladiators()
            targets = [g for g in alive if g != ai]
            if targets:
                target = random.choice(targets)
                self.execute_attack(ai, target)
        elif action == 'defend':
            ai.is_defending = True
            self.log_and_render(f"{ai.name} takes a defensive stance.")
        elif action == 'gesture':
            cheer = random.randint(50, 200)
            self.pot += cheer
            self.log_and_render(f"{ai.name} gestures to the crowd. Pot +{cheer}.")

    def execute_attack(self, attacker, defender):
        self.log_and_render(f"{attacker.name} attacks {defender.name}!")
        
        if defender.is_player:
            reaction = self.player_reaction(attacker)
        else:
            reaction = random.choice(['counter', 'defend'])
            
        if reaction == 'defend':
            self.log_and_render(f"{defender.name} tries to block the blow on the fly!")
            dmg = defender.take_damage(attacker.atk, on_the_fly_defend=True)
            self.log_and_render(f"{attacker.name} hits for {dmg} damage!")
            
        elif reaction == 'counter':
            self.log_and_render(f"{defender.name} chooses to counterattack!")
            dmg_in = defender.take_damage(attacker.atk, on_the_fly_defend=False)
            self.log_and_render(f"{attacker.name} hits for {dmg_in} damage!")
            
            if defender.is_alive:
                dmg_out = attacker.take_damage(defender.atk, on_the_fly_defend=False)
                self.log_and_render(f"{defender.name} hits back for {dmg_out} damage!")

        # Process deaths and looting
        if not defender.is_alive:
            self.log_and_render(f"*** {defender.name} HAS FALLEN! ***", delay=1.0)
            if attacker.is_alive:
                self.loot_gladiator(attacker, defender)
                
        if not attacker.is_alive:
            self.log_and_render(f"*** {attacker.name} HAS FALLEN! ***", delay=1.0)
            if defender.is_alive:
                self.loot_gladiator(defender, attacker)

    def player_reaction(self, attacker):
        self.log_and_render(f"!!! {attacker.name} is attacking you! !!!", delay=0)
        print("1. Counterattack (Take normal damage, hit back)")
        print("2. Defend on the fly (Reduce incoming damage by 50% Def)")
        
        while True:
            choice = input("Reaction (1-2): ").strip()
            if choice == '1':
                return 'counter'
            elif choice == '2':
                return 'defend'

    def play(self):
        self.log_and_render("Welcome to the ARENA. The fight begins!", delay=2.0)
        
        round_num = 1
        while len(self.get_alive_gladiators()) > 1:
            if not self.gladiators[0].is_alive:
                self.log_and_render("You have fallen in the Arena... Game Over.", delay=0)
                break
                
            self.log_and_render(f"--- ROUND {round_num} BEGINS ---")
            
            for gladiator in self.get_alive_gladiators():
                if not gladiator.is_alive:
                    continue
                    
                gladiator.is_defending = False
                
                if gladiator.is_player:
                    self.player_turn(gladiator)
                else:
                    self.ai_turn(gladiator)
                    
            round_num += 1
            
        alive = self.get_alive_gladiators()
        if alive:
            winner = alive[0]
            winner_share = int(self.pot * 0.70)
            loser_share = (self.pot - winner_share) // 19
            
            self.log_and_render(f"THE ARENA FALLS SILENT. {winner.name} IS THE VICTOR!", delay=0)
            print(f"{winner.name} takes the lion's share: {winner_share} Gold!")
            print(f"The fallen gladiators' estates each receive: {loser_share} Gold.")

if __name__ == "__main__":
    game = ArenaGame()
    game.play()