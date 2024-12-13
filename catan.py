#!/usr/bin/python3.11
# Version 1.26

import random
import os
from prettytable import PrettyTable

os.system('clear')

SETTLEMENT_COST = {'brick': 1, 'lumber': 1, 'grain': 1, 'wool': 1}
CITY_COST = {'ore': 3, 'grain': 2}

class Player:
    def __init__(self, name, is_human=False, personality=None):
        self.name = name
        self.resources = {'brick': 0, 'lumber': 0, 'ore': 0, 'grain': 0, 'wool': 0}
        self.victory_points = 0
        self.settlements = []
        self.cities = []
        self.roads = []
        self.is_human = is_human
        self.personality = personality

    def add_resources(self, resource, amount):
        self.resources[resource] += amount

    def spend_resources(self, cost):
        for resource, amt in cost.items():
            if self.resources[resource] < amt:
                return False
        for resource, amt in cost.items():
            self.resources[resource] -= amt
        return True

    def show_resources(self):
        return ', '.join([f"{k}: {v}" for k, v in self.resources.items()])

    def missing_for_build(self, cost):
        missing = 0
        for r, amt in cost.items():
            if self.resources[r] < amt:
                missing += (amt - self.resources[r])
        return missing

    def can_build(self, cost):
        return all(self.resources[r] >= amt for r, amt in cost.items())

    def evaluate_trade_ai(self, offer, request, scarcity=False):
        # AI logic as previously implemented, considering ratio, scarcity, personality, and building help
        for r, amt in request.items():
            if self.resources.get(r, 0) < amt:
                return (False, None)

        sum_offer = sum(offer.values())
        sum_request = sum(request.values())
        ratio = sum_offer / sum_request if sum_request > 0 else float('inf')

        # Simulate post-trade resources
        temp_res = self.resources.copy()
        for r, a in request.items():
            temp_res[r] -= a
        for r, a in offer.items():
            temp_res[r] += a

        def missing_after_trade(temp_resources, cost):
            m = 0
            for r, amt in cost.items():
                have = temp_resources.get(r, 0)
                if have < amt:
                    m += (amt - have)
            return m

        current_settlement_missing = self.missing_for_build(SETTLEMENT_COST)
        current_city_missing = self.missing_for_build(CITY_COST)
        settlement_missing_after = missing_after_trade(temp_res, SETTLEMENT_COST)
        city_missing_after = missing_after_trade(temp_res, CITY_COST)
        helps_settlement = (settlement_missing_after < current_settlement_missing)
        helps_city = (city_missing_after < current_city_missing)

        def propose_counter(offer, factor_increase=1):
            offered_resources = [r for r, a in offer.items() if a > 0]
            if offered_resources:
                extra_res = random.choice(offered_resources)
                counter_offer = offer.copy()
                counter_offer[extra_res] += factor_increase
                return counter_offer
            else:
                return None

        if self.personality == "generous":
            if ratio >= 1.0:
                return (True, None)
            else:
                if helps_settlement or helps_city:
                    return (True, None)
                else:
                    counter = propose_counter(offer, max(1, int((1.0 * sum_request - sum_offer))))
                    return (False, counter) if counter else (False, None)

        elif self.personality == "fair":
            if ratio >= 1.0:
                return (True, None)
            else:
                if helps_settlement or helps_city:
                    if ratio >= 0.9:
                        return (True, None)
                    else:
                        needed_increase = max(1, int((0.9 * sum_request - sum_offer)))
                        counter = propose_counter(offer, needed_increase)
                        return (False, counter) if counter else (False, None)
                else:
                    counter = propose_counter(offer, max(1, int((1.0 * sum_request - sum_offer))))
                    return (False, counter) if counter else (False, None)

        elif self.personality == "greedy":
            if ratio > 1.0:
                return (True, None)
            else:
                if helps_settlement or helps_city:
                    if ratio >= 1.0:
                        return (True, None)
                    else:
                        needed_increase = max(1, int((1.0 * sum_request - sum_offer)))
                        counter = propose_counter(offer, needed_increase)
                        return (False, counter) if counter else (False, None)
                else:
                    needed_increase = max(1, int((1.1 * sum_request - sum_offer)))
                    counter = propose_counter(offer, needed_increase)
                    return (False, counter) if counter else (False, None)
        else:
            # default to fair
            if ratio >= 1.0:
                return (True, None)
            else:
                counter = propose_counter(offer, max(1, int((1.0 * sum_request - sum_offer))))
                return (False, counter) if counter else (False, None)


class Game:
    def __init__(self, human_name):
        self.players = [
            Player(human_name, is_human=True),
            Player("AI Player 1", personality="generous"),
            Player("AI Player 2", personality="greedy"),
            Player("AI Player 3", personality="fair")
        ]
        self.board = self.generate_board()
        self.turn_order = self.players[:]
        self.current_player_index = 0
        self.total_players = len(self.players)
        self.distribute_starting_resources()

    def roll_dice(self):
        return random.randint(1, 6) + random.randint(1, 6)

    def generate_board(self):
        resources = ['brick', 'lumber', 'ore', 'grain', 'wool', 'desert']
        hexes = resources * 3
        random.shuffle(hexes)
        numbers = list(range(2, 13)) * 3
        random.shuffle(numbers)
        return [{'resource': resource, 'number': number, 'owner': []} for resource, number in zip(hexes, numbers)]

    def distribute_resources(self, roll):
        if roll == 7:
            print("\n--- Dice Roll Explanation ---")
            print("You rolled a 7. The robber would be activated (not yet implemented):")
            print("- No hexes produce resources this turn.")
            print("- The robber would move to a chosen hex, blocking it.")
            print("- Players with >7 cards would discard half of them.")
            self.display_game_state()
            return

        print("\n--- Dice Roll Explanation ---")
        print(f"You rolled a {roll}. Any hex with number {roll} now produces resources for players")
        print("with settlements (1 resource each) or cities (2 each) on that hex.")
        print("Desert hexes never produce resources.")

        for hex_number, hex_ in enumerate(self.board):
            if hex_['number'] == roll and hex_['owner']:
                for owner in hex_['owner']:
                    base_amount = 0
                    settle_count = (hex_number in owner.settlements)
                    city_count = (hex_number in owner.cities)

                    if settle_count:
                        base_amount += 1
                    if city_count:
                        base_amount += 2

                    if hex_['resource'] != 'desert' and base_amount > 0:
                        owner.add_resources(hex_['resource'], base_amount)
                        print(f"{owner.name} collects {base_amount} {hex_['resource']}(s) from hex {hex_number + 1}.")

        self.display_game_state()

    def distribute_starting_resources(self):
        for player in self.players:
            total_resources = 5
            resource_types = list(player.resources.keys())
            while total_resources > 0:
                resource = random.choice(resource_types)
                player.add_resources(resource, 1)
                total_resources -= 1

    def display_board(self):
        print("\n--- Board ---")
        grid_size = 4
        for i in range(0, len(self.board), grid_size):
            row = self.board[i:i + grid_size]
            row_display = []
            for j, hex_ in enumerate(row):
                hex_index = i + j
                owner_str_list = []
                for owner in hex_['owner']:
                    if hex_index in owner.cities:
                        owner_str_list.append(f"{owner.name}(C)")
                    elif hex_index in owner.settlements:
                        owner_str_list.append(f"{owner.name}(S)")
                    else:
                        owner_str_list.append(f"{owner.name}")

                owners_str = ""
                if owner_str_list:
                    owners_str = " Owners: " + ", ".join(owner_str_list)

                cell_str = f"[{hex_index+1}] {hex_['resource']} ({hex_['number']}){owners_str}"
                row_display.append(cell_str.ljust(40))
            print(' '.join(row_display))

    def display_game_state(self):
        table = PrettyTable()
        table.field_names = [
            "Player", "Brick", "Lumber", "Ore", "Grain", "Wool", 
            "Settlements", "Cities", "Roads", "Victory Points"
        ]
        for player in self.players:
            table.add_row([
                player.name,
                player.resources['brick'],
                player.resources['lumber'],
                player.resources['ore'],
                player.resources['grain'],
                player.resources['wool'],
                len(player.settlements),
                len(player.cities),
                len(player.roads),
                player.victory_points,
            ])
        print(table)

    def take_turn(self):
        player = self.turn_order[self.current_player_index]
        print(f"\n{player.name}'s turn!")
        self.display_board()

        roll = self.roll_dice()
        self.distribute_resources(roll)

        if player.is_human:
            self.human_action(player)
        else:
            self.ai_action(player)

    def give_random_resource(self, player):
        resource_types = list(player.resources.keys())
        chosen_resource = random.choice(resource_types)
        player.add_resources(chosen_resource, 1)
        print(f"{player.name} received 1 {chosen_resource} for passing!")

    def handle_build_action(self, player):
        print("\n1. Build Settlement (Cost: 1 brick, 1 lumber, 1 grain, 1 wool)")
        print("2. Build Road (Cost: 1 brick, 1 lumber)")
        print("3. Upgrade Settlement to City (Cost: 3 ore, 2 grain, must have a settlement first)")
        choice = input("What do you want to build? ").strip()
        if choice == "1":
            if player.spend_resources({'brick': 1, 'lumber': 1, 'grain': 1, 'wool': 1}):
                print("\nChoose a hex number to place your settlement.")
                try:
                    hex_number = int(input("Enter hex number: ")) - 1
                except ValueError:
                    print("Invalid number.")
                    return False
                if 0 <= hex_number < len(self.board):
                    self.board[hex_number]['owner'].append(player)
                    player.settlements.append(hex_number)
                    player.victory_points += 1
                    print(f"You built a settlement on hex {hex_number + 1}.")
                    self.display_game_state()
                    return True
                else:
                    print("Invalid hex.")
                    return False
            else:
                print("Not enough resources to build a settlement!")
                return False
        elif choice == "2":
            if player.spend_resources({'brick': 1, 'lumber': 1}):
                player.roads.append("road")
                print("You built a road!")
                self.display_game_state()
                return True
            else:
                print("Not enough resources to build a road!")
                return False
        elif choice == "3":
            if len(player.settlements) == 0:
                print("You don't have any settlements to upgrade!")
                return False
            else:
                if player.spend_resources({'ore': 3, 'grain': 2}):
                    print("\nChoose one of your existing settlement hex numbers to upgrade to a city.")
                    print("Your settlements are on these hexes:", [h+1 for h in player.settlements])
                    try:
                        hex_choice = int(input("Enter hex number: ")) - 1
                    except ValueError:
                        print("Invalid number.")
                        return False
                    if hex_choice in player.settlements:
                        player.settlements.remove(hex_choice)
                        player.cities.append(hex_choice)
                        player.victory_points += 1
                        print(f"You upgraded the settlement on hex {hex_choice + 1} to a city!")
                        self.display_game_state()
                        return True
                    else:
                        print("You do not have a settlement on that hex.")
                        return False
                else:
                    print("Not enough resources to upgrade to a city!")
                    return False
        else:
            print("Invalid choice.")
            return False

    def human_action(self, player):
        action_taken = False
        while True:
            print("\nActions: 1. Build  2. Pass  3. Trade")
            action = input("Choose an action: ").strip()

            if action == "1":
                build_success = self.handle_build_action(player)
                if build_success:
                    break
                else:
                    continue
            elif action == "2":
                print("You passed your turn.")
                if not action_taken:
                    self.give_random_resource(player)
                self.display_game_state()
                break
            elif action == "3":
                trade_success = self.trade_resources(initiator=player)
                self.display_game_state()
                if trade_success:
                    action_taken = True
                    continue
                else:
                    continue
            else:
                print("Invalid action.")
                continue

    def ai_build(self, player):
        if player.spend_resources({'brick':1,'lumber':1,'grain':1,'wool':1}):
            possible_hexes = [i for i, h in enumerate(self.board) if player not in h['owner']]
            if not possible_hexes:
                possible_hexes = list(range(len(self.board)))
            chosen_hex = random.choice(possible_hexes)
            self.board[chosen_hex]['owner'].append(player)
            player.settlements.append(chosen_hex)
            player.victory_points += 1
            print(f"{player.name} built a settlement on hex {chosen_hex + 1}.")
            return True

        if player.settlements and player.spend_resources({'ore':3,'grain':2}):
            chosen_hex = random.choice(player.settlements)
            player.settlements.remove(chosen_hex)
            player.cities.append(chosen_hex)
            player.victory_points += 1
            print(f"{player.name} upgraded a settlement on hex {chosen_hex + 1} to a city!")
            return True

        if player.spend_resources({'brick':1,'lumber':1}):
            player.roads.append("road")
            print(f"{player.name} built a road.")
            return True

        return False

    def ai_action(self, player):
        action_taken = False
        if self.ai_build(player):
            print(f"{player.name} ended their turn after building.")
            action_taken = True
        else:
            if random.choice([True, False]):
                if self.ai_trade_resources(player):
                    action_taken = True
                else:
                    print(f"{player.name} decides to pass this turn.")
                    if not action_taken:
                        self.give_random_resource(player)
            else:
                print(f"{player.name} decides to pass this turn.")
                if not action_taken:
                    self.give_random_resource(player)

        self.display_game_state()

    def trade_resources(self, initiator, initiator_offer=None, initiator_request=None):
        if initiator_offer is None or initiator_request is None:
            # Human-initiated trade
            print("You have the following resources:")
            print(initiator.show_resources())
            offer_res = input("Which resource do you offer? (brick/lumber/ore/grain/wool): ").strip().lower()
            if offer_res not in initiator.resources:
                print("Invalid resource type.")
                return False
            try:
                offer_amt = int(input(f"How many {offer_res} do you offer?: ").strip())
            except ValueError:
                print("Invalid number.")
                return False
            if initiator.resources.get(offer_res, 0) < offer_amt:
                print("You do not have enough resources to offer that trade.")
                return False

            request_res = input("Which resource do you want in return?: ").strip().lower()
            if request_res not in initiator.resources:
                print("Invalid resource type.")
                return False
            try:
                request_amt = int(input(f"How many {request_res} do you want?: ").strip())
            except ValueError:
                print("Invalid number.")
                return False

            original_offer = {offer_res: offer_amt}
            original_request = {request_res: request_amt}
        else:
            original_offer = initiator_offer
            original_request = initiator_request

        suppliers = 0
        for p in self.players:
            if p is not initiator:
                can_supply = True
                for r, a in original_request.items():
                    if p.resources.get(r, 0) < a:
                        can_supply = False
                        break
                if can_supply:
                    suppliers += 1

        scarcity = (suppliers == 1)

        # Attempt trade with each other player
        for potential_partner in self.players:
            if potential_partner is not initiator:
                if potential_partner.is_human:
                    print(f"\n{initiator.name} offers {original_offer} and wants {original_request} from {potential_partner.name}.")
                    decision = input("Do you accept this trade? (y/n/c for counter): ").strip().lower()
                    if decision == 'y':
                        if initiator.spend_resources(original_offer):
                            if potential_partner.spend_resources(original_request):
                                for r, a in original_request.items():
                                    initiator.add_resources(r, a)
                                for r, a in original_offer.items():
                                    potential_partner.add_resources(r, a)
                                print(f"{potential_partner.name} accepted the trade!")
                                print("Trade completed successfully.")
                                return True
                            else:
                                print(f"{potential_partner.name} can't complete the trade.")
                                for r, a in original_offer.items():
                                    initiator.add_resources(r, a)
                                continue
                        else:
                            print(f"{initiator.name} no longer has the resources.")
                            return False
                    elif decision == 'c':
                        print("Enter your counter-offer. You can add more demanded resources from the initiator.")
                        new_offer_res = input("Which resource do you want more of from the initiator?: ").strip().lower()
                        if new_offer_res not in initiator.resources:
                            print("Invalid resource.")
                            continue
                        try:
                            additional_amount = int(input("How many additional units?: ").strip())
                        except ValueError:
                            print("Invalid number.")
                            continue

                        counter = original_offer.copy()
                        counter[new_offer_res] = counter.get(new_offer_res, 0) + additional_amount

                        # If initiator is human, ask them; if AI, evaluate AI logic
                        if initiator.is_human:
                            print(f"{potential_partner.name} proposes a counter-offer: {counter} instead of {original_offer}")
                            ans = input("Do you accept this counter-offer? (y/n): ").strip().lower()
                            if ans == 'y':
                                if initiator.spend_resources(counter):
                                    if potential_partner.spend_resources(original_request):
                                        for r,a in original_request.items():
                                            initiator.add_resources(r,a)
                                        for r,a in counter.items():
                                            potential_partner.add_resources(r,a)
                                        print("Trade completed with the new terms.")
                                        return True
                                    else:
                                        print(f"{potential_partner.name} can't fulfill request.")
                                        for r,a in counter.items():
                                            initiator.add_resources(r,a)
                                        continue
                                else:
                                    print("Initiator doesn't have enough resources.")
                                    continue
                            else:
                                print("Counter-offer declined.")
                                continue
                        else:
                            # Initiator is AI, evaluate AI logic
                            accepted, ai_counter = initiator.evaluate_trade_ai(counter, original_request, scarcity=scarcity)
                            if accepted:
                                if initiator.spend_resources(counter):
                                    if potential_partner.spend_resources(original_request):
                                        for r,a in original_request.items():
                                            initiator.add_resources(r,a)
                                        for r,a in counter.items():
                                            potential_partner.add_resources(r,a)
                                        print("Trade completed with new terms.")
                                        if not initiator.is_human and not potential_partner.is_human:
                                            print(f"AI-to-AI trade: {initiator.name} gave {counter} to {potential_partner.name} for {original_request}.")
                                        return True
                                    else:
                                        print(f"{potential_partner.name} can't pay.")
                                        for r,a in counter.items():
                                            initiator.add_resources(r,a)
                                        continue
                                else:
                                    print(f"{initiator.name} cannot afford the counter offer.")
                                    continue
                            else:
                                print(f"{initiator.name} (AI) declined the counter-offer.")
                                continue

                    else:
                        print(f"{potential_partner.name} declined the trade.")
                        continue

                else:
                    # AI partner
                    accepted, counter = potential_partner.evaluate_trade_ai(original_offer, original_request, scarcity=scarcity)
                    if accepted:
                        if initiator.spend_resources(original_offer):
                            if potential_partner.spend_resources(original_request):
                                for r, a in original_request.items():
                                    initiator.add_resources(r, a)
                                for r, a in original_offer.items():
                                    potential_partner.add_resources(r, a)
                                print(f"{potential_partner.name} accepted the trade!")
                                print("Trade completed.")
                                if not initiator.is_human and not potential_partner.is_human:
                                    print(f"AI-to-AI trade: {initiator.name} gave {original_offer} to {potential_partner.name} for {original_request}.")
                                return True
                            else:
                                print(f"{potential_partner.name} can't complete the trade.")
                                for r, a in original_offer.items():
                                    initiator.add_resources(r, a)
                                continue
                        else:
                            print("Initiator no longer has resources.")
                            return False
                    else:
                        if counter is not None:
                            if initiator.is_human:
                                print(f"{potential_partner.name} proposes a counter-offer: {counter}")
                                ans = input("Accept counter? (y/n): ").strip().lower()
                                if ans == 'y':
                                    if initiator.spend_resources(counter):
                                        if potential_partner.spend_resources(original_request):
                                            for r,a in original_request.items():
                                                initiator.add_resources(r,a)
                                            for r,a in counter.items():
                                                potential_partner.add_resources(r,a)
                                            print("Trade completed with new terms.")
                                            if not initiator.is_human and not potential_partner.is_human:
                                                print(f"AI-to-AI trade: {initiator.name} gave {counter} to {potential_partner.name} for {original_request}.")
                                            return True
                                        else:
                                            print(f"{potential_partner.name} can't fulfill request.")
                                            for r,a in counter.items():
                                                initiator.add_resources(r,a)
                                            continue
                                    else:
                                        print("Initiator can't afford counter.")
                                        continue
                                else:
                                    print("Counter-offer declined.")
                                    continue
                            else:
                                # AI initiator declines counters
                                print(f"{initiator.name} (AI) declines the counter-offer.")
                                continue
                        else:
                            print(f"{potential_partner.name} declined the trade.")
                            continue

        print("No one accepted your trade.")
        return False

    def ai_trade_resources(self, player):
        possible_resources = ['brick','lumber','ore','grain','wool']
        ai_offer_res = random.choice(possible_resources)
        ai_request_res = random.choice([r for r in possible_resources if r != ai_offer_res])
        ai_offer_amt = 1
        ai_request_amt = 1

        if player.resources.get(ai_offer_res, 0) < ai_offer_amt:
            return False

        return self.trade_resources(
            initiator=player,
            initiator_offer={ai_offer_res: ai_offer_amt},
            initiator_request={ai_request_res: ai_request_amt}
        )

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % self.total_players

    def is_game_over(self):
        for player in self.players:
            if player.victory_points >= 10:
                print(f"\nGame Over! {player.name} wins!")
                return True
        return False

    def play(self):
        print("Welcome to Catan!")
        print("\n--- Purpose of the Game ---")
        print("Earn 10 Victory Points (VP) by building settlements, roads, and cities.")

        print("\n--- How the Game Works ---")
        print("1. The board is composed of hexes, each producing a specific resource (brick, lumber, ore, grain, wool) or desert.")
        print("   Each hex has a number (2-12). At the start of a turn, you roll two dice. The sum determines which hexes produce resources.")
        print("2. Settlements adjacent to a producing hex earn 1 resource; cities earn 2 of that resource. Desert hexes never produce.")
        print("3. If a 7 is rolled, no one collects resources and the robber would be activated (not fully implemented here).")
        print("4. Your goal is to reach 10 VP. Settlements grant 1 VP, cities grant an additional VP over a settlement, reaching 2 total.")
        print("5. On your turn, you can:")
        print("   - Build: Use resources to construct a settlement, road, or upgrade a settlement to a city.")
        print("   - Trade: Offer your resources and request others. AI players consider fairness, scarcity, and personal benefit. You can accept, reject, or counter trades offered to you.")
        print("   - Pass: If you pass without having built or traded, you gain 1 random resource as a bonus.")
        print("6. The game features AI players with different personalities (generous, fair, greedy) who evaluate trades differently.")
        print("7. Once you or another player reaches 10 VP, the game ends immediately and that player wins.")
        print("8. After the last player in a round finishes their turn, press Enter to continue and start the next round.")
        print("\nStarting the game!")

        while not self.is_game_over():
            self.take_turn()
            if self.current_player_index == self.total_players - 1:
                self.next_player()
                input("\nEnd of round. Press Enter to continue to the next round...")
                os.system('clear')
            else:
                self.next_player()


if __name__ == "__main__":
    human_name = input("Enter your name: ").strip()
    game = Game(human_name)
    game.play()

