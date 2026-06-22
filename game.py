from itertools import product, combinations
import random

# UI/UX styling constants
RESET   = "\033[0m"
RED     = "\033[91m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
BG_CARD = "\033[47m\033[30m"
BG_RED  = "\033[47m\033[91m"
CYAN    = "\033[96m"
YELLOW  = "\033[93m"
GREEN   = "\033[92m"

SUIT_SYMBOLS  = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}
VALUE_LABELS  = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}
POS_LABELS    = [f"{YELLOW}1st{RESET}", f"{WHITE}2nd{RESET}", f"{RED}3rd{RESET}", f"{CYAN}4th{RESET}", f"{GREEN}5th{RESET}"]


class Card:
    def __init__(self, suit, value):
        self.suit  = suit
        self.value = value

    def color(self):
        return BG_RED if self.suit in ('H', 'D') else BG_CARD

    def render(self):
        sym   = SUIT_SYMBOLS[self.suit]
        label = VALUE_LABELS.get(self.value, str(self.value))
        col   = self.color()
        pad   = " " if len(label) == 1 else ""
        return "\n".join([
            f"{col}┌─────┐{RESET}",
            f"{col}│{label}{pad}   │{RESET}",
            f"{col}│  {sym}  │{RESET}",
            f"{col}│   {pad}{label}│{RESET}",
            f"{col}└─────┘{RESET}"
        ])

    def __repr__(self):
        return f"{VALUE_LABELS.get(self.value, self.value)}{SUIT_SYMBOLS[self.suit]}"


class Deck:
    def __init__(self):
        self.cards = [Card(s, v) for s, v in product(['H', 'C', 'D', 'S'], range(1, 14))]
        random.shuffle(self.cards)
        self.used = set()

    def pick_auto(self):
        for i, card in enumerate(self.cards):
            if i not in self.used:
                self.used.add(i)
                return card

    def pick_manual(self):
        print(f"\nAvailable cards: {len(self.cards) - len(self.used)}")
        printed = 0
        for i, card in enumerate(self.cards):
            if i in self.used:
                continue
            label = VALUE_LABELS.get(card.value, str(card.value))
            print(f"  [{i}] {card.color()}{label}{SUIT_SYMBOLS[card.suit]}{RESET}", end="  ")
            printed += 1
            if printed % 8 == 0:
                print()
        print()
        while True:
            try:
                idx = int(input(f"Pick a card index (0-{len(self.cards)-1}): "))
                if not (0 <= idx < len(self.cards)):
                    print(f"{RED}Invalid index.{RESET}")
                elif idx in self.used:
                    print(f"{RED}Card already taken!{RESET}")
                else:
                    self.used.add(idx)
                    return self.cards[idx]
            except ValueError:
                print(f"{RED}Enter a valid number.{RESET}")


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []

    def add_card(self, card):
        self.hand.append(card)

    def _values_desc(self):
        return tuple(sorted((14 if c.value == 1 else c.value for c in self.hand), reverse=True))

    def _is_trike(self):
        return self.hand[0].value == self.hand[1].value == self.hand[2].value

    def _run_tiebreak(self):
        """Returns tiebreak tuple if hand is a run, else None."""
        raw = sorted(c.value for c in self.hand)
        if raw == [1, 2, 3]:
            return (15, 14, 13)  # A-2-3 is the highest run in Teen Patti
        vals = sorted(14 if c.value == 1 else c.value for c in self.hand)
        if vals[1] - vals[0] == 1 and vals[2] - vals[1] == 1:
            return tuple(reversed(vals))
        return None

    def _is_same_suit(self):
        return len({c.suit for c in self.hand}) == 1

    def _is_pair(self):
        return any(x.value == y.value for x, y in combinations(self.hand, 2))

    def evaluate(self):
        values_desc = self._values_desc()
        if self._is_trike():
            return (6, "Trike ", values_desc)
        tiebreak = self._run_tiebreak()
        if tiebreak is not None:
            if self._is_same_suit():
                return (5, "Pakki Run ", tiebreak)
            return (4, "Run ", tiebreak)
        if self._is_same_suit():
            return (3, "Colour ", values_desc)
        if self._is_pair():
            return (2, "Jut / Pair ", values_desc)
        return (1, "High Card", values_desc)

    def display(self, hand_type, score):
        print(f"\n{BOLD}{YELLOW}  ♟  {self.name}{RESET}")
        lines = [c.render().split('\n') for c in self.hand]
        for row in zip(*lines):
            print("  ".join(row))
        print(f"  {GREEN}Hand  : {BOLD}{hand_type}{RESET}")
        raw_s = score[0]
        actual = 1 if raw_s in (14, 15) else raw_s
        display_score = VALUE_LABELS.get(actual, str(actual))
        print(f"  {WHITE}Score : {display_score}{RESET}")


class Game:
    def __init__(self):
        self.deck    = Deck()
        self.players = self._setup_players()
        self.manual  = input("Manual card selection? (y/n): ").strip().lower() == 'y'

    def _setup_players(self):
        while True:
            try:
                count = int(input("Enter number of players (2-5): "))
                if 2 <= count <= 5:
                    break
                print(f"{RED}Must be between 2 and 5.{RESET}")
            except ValueError:
                print(f"{RED}Enter a valid number.{RESET}")
        return [Player(input(f"Enter name for Player {i+1}: ")) for i in range(count)]

    def deal(self):
        for player in self.players:
            if self.manual:
                print(f"\n{BOLD}{YELLOW}  ♟  {player.name} — pick 3 cards{RESET}")
            for _ in range(3):
                card = self.deck.pick_manual() if self.manual else self.deck.pick_auto()
                player.add_card(card)

    def show_results(self):
        print(f"{BOLD}{CYAN}         CARDS DISTRIBUTED TO PLAYERS  {RESET}")
        results = {}
        for player in self.players:
            rank, hand_type, score = player.evaluate()
            results[player.name] = {"rank": rank, "type": hand_type, "score": score}
            player.display(hand_type, score)

        # Sort by (hand rank, score tuple) — both compared in descending order
        ranking = sorted(results.items(), key=lambda x: (x[1]["rank"], x[1]["score"]), reverse=True)

        print(f"\n{BOLD}{CYAN}              FINAL RESULT {RESET}")
        for pos, (name, data) in zip(POS_LABELS, ranking):
            s = data['score'][0]
            actual_s = 1 if s in (14, 15) else s
            display_score = VALUE_LABELS.get(actual_s, str(actual_s))
            print(f"  {pos} {BOLD}{YELLOW}{name:<10}{RESET}  →  {GREEN}{data['type']:<16}{RESET}  Score={WHITE}{display_score}{RESET}")

        # Announce winner or tie
        top_key = lambda x: (x[1]["rank"], x[1]["score"])
        if len(ranking) > 1 and top_key(ranking[0]) == top_key(ranking[1]):
            top = top_key(ranking[0])
            tied = [n for n, d in ranking if (d["rank"], d["score"]) == top]
            print(f"\n{BOLD}{CYAN}🤝 TIE between: {', '.join(tied)}{RESET}")
        else:
            print(f"\n{BOLD}{GREEN}🏆 Winner: {ranking[0][0]} with {ranking[0][1]['type']}!{RESET}")

        print(f"\n{BOLD}{CYAN}Hand Ranking Priority:{RESET}")
        print("  Trike > Pakki Run > Run > Colour > Jut/Pair > High Card")

    def run(self):
        self.deal()
        self.show_results()


if __name__ == "__main__":
    Game().run()
