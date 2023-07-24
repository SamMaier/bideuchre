from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class Suit(Enum):
  TRUMP = 0
  SUIT_1 = 1 # HEARTS
  SUIT_2 = 2 # DIAMONDS
  SUIT_3 = 3 # CLUBS
  SUIT_4 = 4 # SPADES

  def __str__(self):
    match self:
      case Suit.TRUMP:
        return 'T'
      case Suit.SUIT_1:
        return 'H'
      case Suit.SUIT_2:
        return 'D'
      case Suit.SUIT_3:
        return 'C'
      case Suit.SUIT_4:
        return 'S'

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

  def __str__(self):
    conv_number = str(self.number)
    if conv_number == '11':
      conv_number = 'J'
    elif conv_number == '12':
      conv_number = 'Q'
    elif conv_number == '13':
      conv_number = 'K'
    elif conv_number == '14':
      conv_number = 'A'
    elif conv_number == '15':
      conv_number = 'LB'
    elif conv_number == '16':
      conv_number = 'RB'

    return f'{conv_number}{self.suit}'

