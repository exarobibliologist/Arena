import random
import time

class Gladiator:
    def __init__(self, name, is_player=False):
        self.name = name
        self.is_player = is_player
        self.hp = 100
        self.atk = random.randint(15, 30)
        self.def_stat = random.randint(10, 20)
        
        # State trackers
        self.is_defending = False  # Full turn defense (100%)
        self.is_alive = True

    def display_stats(self):
        return f"({self.name}: HP {self.hp}; Def {self.def_stat}; Atk {self.atk})"

    def take_damage(self, amount, on_the_fly_defend=False):
        mitigation = 0
        
        # 100% defense if they spent their main turn defending
        if self.is_defending:
            mitigation += self.def_stat
            
        # 50% defense if they choose to defend "on the fly" against an attack
        if on_the_fly_defend:
            mitigation += (self.def_stat * 0.5)
            
        actual_damage = max(0, amount - mitigation)
        self.hp -= actual_damage
        
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
            
        return actual_damage

class ArenaGame:
    def __init__(self):
        self.pot = 1000
        self.gladiators = [Gladiator("Player", is_player=True)]
        for i in range(2, 21):
            self.gladiators.append(Gladiator(f"Gladiator {i}"))
            
    def get_alive_gladiators(self):
        return [g for g in self.gladiators if g.is_alive]

    def player_turn(self, player):
        print(f"\n{'='*40}")
        print(f"YOUR TURN! {player.display_stats()}")
        print(f"Current Pot: {self.pot} Gold")
        print("1. Attack")
        print("2. Defend (100% Def until next turn)")
        print("3. Gesture to Crowd (Increase Pot)")
        
        choice = input("Choose action (1-3): ")
        
        if choice == '1':
            alive = self.get_alive_gladiators()
            targets = [g for g in alive if g != player]
            
            # Print a few targets so the screen isn't entirely flooded
            print("\nAvailable Targets:")
            for i, target in enumerate(targets):
                print(f"{i + 1}. {target.display_stats()}")
                
            target_idx = int(input(f"Select target (1-{len(targets)}): ")) - 1
            target = targets[target_idx]
            self.execute_attack(player, target)
            
        elif choice == '2':
            print("You raise your shield! (Defense maximized until next turn)")
            player.is_defending = True
            
        elif choice == '3':
            cheer = random.randint(100, 500)
            self.pot += cheer
            print(f"You pump up the crowd! The pot increases by {cheer} to {self.pot}!")
        else:
            print("You hesitated and lost your turn!")

    def ai_turn(self, ai):
        # Simple AI weights: 60% Attack, 20% Defend, 20% Gesture
        action = random.choices(['attack', 'defend', 'gesture'], weights=[60, 20, 20])[0]
        
        if action == 'attack':
            alive = self.get_alive_gladiators()
            targets = [g for g in alive if g != ai]
            if targets:
                target = random.choice(targets)
                self.execute_attack(ai, target)
        elif action == 'defend':
            ai.is_defending = True
            print(f"{ai.name} takes a defensive stance.")
        elif action == 'gesture':
            cheer = random.randint(50, 200)
            self.pot += cheer
            print(f"{ai.name} gestures to the crowd. Pot +{cheer}.")

    def ai_reaction(self, defender):
        # AI decides how to react to an incoming attack
        return random.choice(['counter', 'defend'])

    def player_reaction(self, attacker):
        print(f"\n!!! {attacker.name} is attacking you! !!!")
        print("1. Counterattack (Take normal damage, hit back)")
        print("2. Defend on the fly (Reduce incoming damage by 50% Def)")
        choice = input("Reaction (1-2): ")
        return 'counter' if choice == '1' else 'defend'

    def execute_attack(self, attacker, defender):
        print(f"{attacker.name} attacks {defender.name}!")
        
        # Get reaction
        if defender.is_player:
            reaction = self.player_reaction(attacker)
        else:
            reaction = self.ai_reaction(defender)
            
        if reaction == 'defend':
            print(f"{defender.name} tries to block the blow on the fly!")
            dmg = defender.take_damage(attacker.atk, on_the_fly_defend=True)
            print(f"{attacker.name} hits for {dmg} damage! {defender.name} has {defender.hp} HP left.")
            
        elif reaction == 'counter':
            print(f"{defender.name} chooses to counterattack!")
            # Defender takes normal damage
            dmg_in = defender.take_damage(attacker.atk, on_the_fly_defend=False)
            print(f"{attacker.name} hits for {dmg_in} damage!")
            
            # Defender hits back (if they survived)
            if defender.is_alive:
                dmg_out = attacker.take_damage(defender.atk, on_the_fly_defend=False)
                print(f"{defender.name} counterattacks for {dmg_out} damage!")
            else:
                print(f"{defender.name} was killed before they could counterattack!")

        if not defender.is_alive:
            print(f"*** {defender.name} HAS FALLEN! ***")
        if not attacker.is_alive:
            print(f"*** {attacker.name} HAS FALLEN! ***")

    def play(self):
        print("Welcome to the ARENA!")
        round_num = 1
        
        while len(self.get_alive_gladiators()) > 1:
            # Check if player is dead
            if not self.gladiators[0].is_alive:
                print("\nYou have fallen in the Arena... Game Over.")
                break
                
            print(f"\n--- ROUND {round_num} ---")
            
            for gladiator in self.get_alive_gladiators():
                if not gladiator.is_alive:
                    continue
                    
                # Reset main-turn defense at the START of their turn
                gladiator.is_defending = False
                
                if gladiator.is_player:
                    self.player_turn(gladiator)
                else:
                    self.ai_turn(gladiator)
                    
                time.sleep(0.5) # Slight pause for readability
                
            round_num += 1
            
        # End of game payout
        alive = self.get_alive_gladiators()
        if alive:
            winner = alive[0]
            winner_share = int(self.pot * 0.70)
            loser_share = (self.pot - winner_share) // 19 # Distribute rest to participants
            
            print(f"\n{'-'*40}")
            print(f"THE ARENA FALLS SILENT. {winner.name} IS THE VICTOR!")
            print(f"Total Pot: {self.pot}")
            print(f"{winner.name} takes the lion's share: {winner_share} Gold!")
            print(f"The fallen gladiators' estates each receive: {loser_share} Gold.")

if __name__ == "__main__":
    game = ArenaGame()
    game.play()