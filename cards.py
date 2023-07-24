from dataclasses import dataclass
from enum import Enum

class Suit(Enum):
  TRUMP = 0
  SUIT_1 = 1 # HEARTS
  SUIT_2 = 2 # DIAMONDS
  SUIT_3 = 3 # CLUBS
  SUIT_4 = 4 # SPADES

@dataclass(order=True)
class Card:
  suit: Suit
  number: int

  @staticmethod
  def max(cards: list[Card]) -> int:
    curr_max = 0
    for i in range(1, len(cards)):
      if cards[curr_max].suit != cards[i].suit:
        if cards[i].suit == Suit.TRUMP:
          curr_max = i
      elif cards[curr_max].number < cards[i].number:
        curr_max = i
    return curr_max
        
        
  
