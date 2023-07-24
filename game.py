from cards import Suit, Card
from player import Player

FULL_DECK = [Card(s, i) for i in range(9, 15) for s in [Suit.SUIT_1, Suit.SUIT_2, Suit.SUIT_3, Suit.SUIT_4]] * 2
print(', '.join(map(str, FULL_DECK)))
class Hand:
  def __init__(self, players: list[Player], dealer: int):
    self.players = players[dealer:] + players[:dealer]

  def play_hand(self):
    # Deal
    # Bids
    # Kitty
    # Play hand
    pass

class Game:
  def __init__(self, players: list[Player]):
    assert len(players) == 4
    self.players = players

  def play_game(self, num_hands=12):
    # TODO Pick first dealer.
    first_deal = 0
    for i in range(num_hands):
      h = Hand(self.players, dealer=(i + first_deal) % 4)
      #TODO scores
      results = h.play_hand()
