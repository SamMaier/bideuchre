from typing import Optional
import logging

from cards import Suit, Card
from basic_strategies import BiddingStrategy, PlayingStrategy, Bid

class Player:
  def __init__(self, bidding_strat: BiddingStrategy, playing_strat: PlayingStrategy, name='?'):
    self.bidding_strat = bidding_strat
    self.playing_strat = playing_strat
    self.name = name
    self.hand = []
    self.discarded_cards = None

  def deal_hand(self, hand: list[Card]):
    self.hand = sorted(hand)
    self.discarded_cards = None

  def bid(self, prev_bids: list[Bid], curr_bid: Optional[Bid]) -> Bid:
    b = self.bidding_strat.bid(self.hand, prev_bids, curr_bid)
    if b:
      logging.info(f'{self.name} bidding {b[0]}{b[1]}')
    else:
      logging.info(f'{self.name} passing')
    logging.debug('   with hand ' + Card.stringify(self.hand))
    return b

  def bidding_finished(self, trump: Suit, kitty: Optional[list[Card]] = None) -> Optional[list[Card]]:
    if trump != Suit.TRUMP:
      self.hand = Card.convert_to_trump(self.hand, trump)
    if kitty:
      logging.debug(f'{self.name} wins kitty {Card.stringify(kitty)}')
      kitty = Card.convert_to_trump(kitty, trump)
      self.hand.extend(kitty)
      self.discarded_cards = self.playing_strat.take_kitty(self.hand, len(kitty))
      for d in self.discarded_cards:
        self.hand.remove(d)
      logging.debug(f'{self.name} discards {Card.stringify(self.discarded_cards)}')
      return self.discarded_cards


  def play_card(self, cards_remaining: list[Card], cards_laid: list[Card]) -> Card:
    if self.discarded_cards:
      cards_remaining = cards_remaining.copy()
      for x in self.discarded_cards:
        cards_remaining.remove(x)

    if cards_laid:
      card = self.playing_strat.follow(self.hand, cards_remaining, cards_laid)
    else:
      card = self.playing_strat.lead(self.hand, cards_remaining)

    self.hand.remove(card)
    return card
    
