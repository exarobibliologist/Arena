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
        self.gold = 0
        
        self.is_defending = False
        self.is_alive = True

    def display_stats(self, index):
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
        self.pot = 10
        self.messages = []
        
        # Initialize gladiators once so they persist across multiple matches
        self.gladiators = [Gladiator("Player", is_player=True)]
        for i in range(2, 21):
            self.gladiators.append(Gladiator(f"Gladiator {i}"))
            
        if os.name == 'nt':
            os.system('color')

    def get_alive_gladiators(self):
        return [g for g in self.gladiators if g.is_alive]

    def reset_arena(self):
        self.pot = 10
        self.messages = []
        for g in self.gladiators:
            g.hp = 100
            g.is_alive = True
            g.is_defending = False

    def log_and_render(self, msg, delay=0.6):
        if msg:
            self.messages.append(msg)
            if len(self.messages) > 5:
                self.messages.pop(0)
                
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 100)
        print(f"THE ARENA - Current Pot: {self.pot} Gold".center(100))
        print("=" * 100)
        
        for i in range(10):
            left_glad = self.gladiators[i]
            right_glad = self.gladiators[i + 10]
            
            left_str_raw = f"{left_glad.display_stats(i + 1):<47}"
            right_str_raw = right_glad.display_stats(i + 11)
            
            if not left_glad.is_alive:
                left_str_raw = f"\033[90m{left_str_raw}\033[0m"
            if not right_glad.is_alive:
                right_str_raw = f"\033[90m{right_str_raw}\033[0m"
                
            print(f"{left_str_raw} |   {right_str_raw}")
            
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
                # Increase pot by exactly 1% (minimum 1 gold)
                cheer = max(1, int(self.pot * 0.01))
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
            cheer = max(1, int(self.pot * 0.01))
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
            
            # Reward for Total Defense
            if dmg == 0:
                self.pot += 20
                self.log_and_render(f"FLAWLESS DEFENSE! The crowd throws 20 gold into the pot!")
            
        elif reaction == 'counter':
            self.log_and_render(f"{defender.name} chooses to counterattack!")
            dmg_in = defender.take_damage(attacker.atk, on_the_fly_defend=False)
            self.log_and_render(f"{attacker.name} hits for {dmg_in} damage!")
            
            # Reward for Total Defense during a counter if they had main-turn defense up
            if dmg_in == 0 and defender.is_defending:
                self.pot += 20
                self.log_and_render(f"FLAWLESS DEFENSE! The crowd throws 20 gold into the pot!")
            
            if defender.is_alive:
                dmg_out = attacker.take_damage(defender.atk, on_the_fly_defend=False)
                self.log_and_render(f"{defender.name} hits back for {dmg_out} damage!")
                
                # Attacker gets total defense reward if they blocked the counter perfectly
                if dmg_out == 0 and attacker.is_defending:
                    self.pot += 20
                    self.log_and_render(f"FLAWLESS DEFENSE! The crowd throws 20 gold into the pot!")

        # Process deaths, looting, and reward for Total Victory
        if not defender.is_alive:
            self.pot += 50
            self.log_and_render(f"*** {defender.name} HAS FALLEN! The crowd cheers (+50 Pot) ***", delay=1.0)
            if attacker.is_alive:
                self.loot_gladiator(attacker, defender)
                
        if not attacker.is_alive:
            self.pot += 50
            self.log_and_render(f"*** {attacker.name} HAS FALLEN! The crowd cheers (+50 Pot) ***", delay=1.0)
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

    def calculate_max_upgrades(self, current_stat, available_gold):
        count = 0
        temp_stat = current_stat
        temp_gold = available_gold
        
        while temp_gold >= max(1, temp_stat // 2):
            temp_gold -= max(1, temp_stat // 2)
            temp_stat += 1
            count += 1
        return count

    def preparation_phase(self):
        player = self.gladiators[0]
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 50)
            print("PREPARATION PHASE".center(50))
            print("=" * 50)
            print(f"Current Gold: {player.gold}")
            print("-" * 50)
            
            atk_cost = max(1, player.atk // 2)
            def_cost = max(1, player.def_stat // 2)
            
            max_atk_upgrades = self.calculate_max_upgrades(player.atk, player.gold)
            max_def_upgrades = self.calculate_max_upgrades(player.def_stat, player.gold)
            
            print(f"1. Upgrade Attack (Current: {player.atk})")
            print(f"   Cost: {atk_cost} Gold | Can afford: {max_atk_upgrades} more upgrades")
            print(f"2. Upgrade Defense (Current: {player.def_stat})")
            print(f"   Cost: {def_cost} Gold | Can afford: {max_def_upgrades} more upgrades")
            print("3. Enter the next Arena battle")
            print("=" * 50)
            
            choice = input("Select an option (1-3): ").strip()
            
            if choice == '1':
                if player.gold >= atk_cost:
                    player.gold -= atk_cost
                    player.atk += 1
                else:
                    input("Not enough gold! Press Enter to continue...")
            elif choice == '2':
                if player.gold >= def_cost:
                    player.gold -= def_cost
                    player.def_stat += 1
                else:
                    input("Not enough gold! Press Enter to continue...")
            elif choice == '3':
                break

    def ai_preparation_phase(self):
        for ai in self.gladiators[1:]:
            while True:
                atk_cost = max(1, ai.atk // 2)
                def_cost = max(1, ai.def_stat // 2)
                
                can_buy_atk = ai.gold >= atk_cost
                can_buy_def = ai.gold >= def_cost
                
                if not can_buy_atk and not can_buy_def:
                    break 
                
                choices = []
                if can_buy_atk: choices.append('atk')
                if can_buy_def: choices.append('def')
                
                pick = random.choice(choices)
                if pick == 'atk':
                    ai.gold -= atk_cost
                    ai.atk += 1
                elif pick == 'def':
                    ai.gold -= def_cost
                    ai.def_stat += 1

    def play(self):
        while True:
            self.reset_arena()
            self.log_and_render("Welcome to the ARENA. The fight begins!", delay=2.0)
            
            round_num = 1
            while len(self.get_alive_gladiators()) > 1:
                if not self.gladiators[0].is_alive:
                    self.log_and_render("You have fallen in the Arena...", delay=0)
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
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 60)
            
            if alive:
                winner = alive[0]
                winner_share = int(self.pot * 0.70)
                loser_share = (self.pot - winner_share) // 19
                
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
            else:
                print("NO COMBATANTS SURVIVED. THE ARENA CLAIMS ALL.".center(60))
                print("=" * 60)
                
            print("=" * 60)
            
            while True:
                q_c = input("\n[Q]uit or [C]ontinue? ").strip().upper()
                if q_c in ['Q', 'C']:
                    break
            
            if q_c == 'Q':
                print("\nThanks for playing Arena!")
                break
            else:
                self.ai_preparation_phase()
                self.preparation_phase()

if __name__ == "__main__":
    game = ArenaGame()
    game.play()