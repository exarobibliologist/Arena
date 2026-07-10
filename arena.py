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
        # Format the gladiator string to fit cleanly in a column
        if not self.is_alive:
            return f"[{index:2}] {self.name:12}: *** DEAD ***"
            
        def_marker = " (D)" if self.is_defending else ""
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
            
        return actual_damage

class ArenaGame:
    def __init__(self):
        self.pot = 1000
        self.messages = []
        
        # Initialize 20 gladiators (Player is index 0)
        self.gladiators = [Gladiator("Player", is_player=True)]
        for i in range(2, 21):
            self.gladiators.append(Gladiator(f"Gladiator {i}"))

    def get_alive_gladiators(self):
        return [g for g in self.gladiators if g.is_alive]

    def log_and_render(self, msg, delay=0.6):
        """Adds a message to the log, limits it to 5, redraws the screen, and pauses."""
        if msg:
            self.messages.append(msg)
            if len(self.messages) > 5:
                self.messages.pop(0)
                
        # Clear the terminal screen (works on Windows/DOS and Unix)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # --- DRAW HEADER ---
        print("=" * 80)
        print(f"THE ARENA - Current Pot: {self.pot} Gold".center(80))
        print("=" * 80)
        
        # --- DRAW GLADIATORS (2 Columns) ---
        # Odds on left (1-10), Evens on right (11-20)
        for i in range(10):
            left_glad = self.gladiators[i]
            right_glad = self.gladiators[i + 10]
            
            left_str = left_glad.display_stats(i + 1)
            right_str = right_glad.display_stats(i + 11)
            
            print(f"{left_str:<39}| {right_str}")
            
        # --- DRAW MESSAGE LOG ---
        print("=" * 80)
        print("BATTLE LOG".center(80))
        print("-" * 80)
        
        # Pad with empty lines if there are fewer than 5 messages
        for i in range(5):
            if i < len(self.messages):
                print(self.messages[i])
            else:
                print("")
                
        print("=" * 80)
        
        # Pause to let the player read the action
        if delay > 0:
            time.sleep(delay)

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

        if not defender.is_alive:
            self.log_and_render(f"*** {defender.name} HAS FALLEN! ***", delay=1.0)
        if not attacker.is_alive:
            self.log_and_render(f"*** {attacker.name} HAS FALLEN! ***", delay=1.0)

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
        # Initial draw
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