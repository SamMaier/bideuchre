from collections.abc import Callable

from cards import Suit, Card

Bid = tuple[Suit, int]

class BiddingStrategy:
  def bid(self, hand: list[Card], prev_bids: list[Bid]) -> Bid:
    return None

class PlayingStrategy:
  def lead(self, hand: list[Card], cards_remaining: list[Card]) -> Card:
    return hand[0]

  def follow(self, hand: list[Card], cards_remaining: list[Card], cards_laid: list[Card]) -> Card:
    return hand[0]

  def take_kitty(self, hand: list[Card], trump: Suit, kitty: list[Card]):
    return kitty
    

class Player:
  def __init__(self, bidding_strat: BiddingStrategy, playing_strat: PlayingStrategy):
    self.bidding_strat = bidding_strat
    self.playing_strat = playing_strat
    self.hand = []
    self.discarded_cards = None

  def deal_hand(self, hand: list[Card]):
    self.hand = hand
    self.discarded_cards = None

  def bid(self, prev_bids: list[Bid]) -> Bid:
    return bidding_strat.bid(self.hand, prev_bids)

  def bidding_finished(self, trump: Suit, kitty: Optional[list[Card]] = None):
    if kitty:
      num_cards_for_assert = len(self.hand) + len(kitty)
      self.discarded_cards = self.playing_strat.take_kitty(self.hand, trump, kitty)
      assert num_cards_for_assert == len(self.hand) + len(self.discarded_cards)
    if trump == Suit.TRUMP:
      return # No trump
    for c in self.hand:
      if c.suit == trump:
        c.suit = Suit.TRUMP
        if c.number == 11:
          c.number = 16
      elif c.number == 11 and (c.suit + 1) // 2 == (trump + 1) // 2: 
        c.suit = Suit.TRUMP
        c.number = 15

  def play_card(self, cards_remaining: list[Card], cards_laid: list[Card]) -> Card:
    if self.discarded_cards:
      cards_remaining = cards_remaining.copy()
      cards_remaining.remove(self.discarded_cards)

    if cards_laid:
      card = self.playing_strat.follow(self.hand, cards_remaining, cards_laid)
    else:
      card = self.playing_strat.lead(self.hand, cards_remaining)

    self.hand.remove(card)
    
    
