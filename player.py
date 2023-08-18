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

  def deal_hand(self, hand: list[Card], team: bool):
    self.hand = sorted(hand, reverse=True)
    self.discarded_cards = None
    self.team = team

  def bid(self, prev_bids: list[Bid], curr_bid: int, score_delta: int, hands_left: int) -> Bid:
    b = self.bidding_strat.bid(self.hand, prev_bids, curr_bid, score_delta, hands_left)
    if b:
      logging.info(f'{self.name} bidding {b[0]}{b[1]}')
    else:
      logging.info(f'{self.name} passing')
    logging.debug('   with hand ' + Card.stringify(self.hand))
    return b

  def bidding_finished(self,
                       trump: Suit,
                       prev_bids: list[Bid],
                       my_index: int,
                       kitty: Optional[list[Card]] = None,
                       partner_alone: Optional[bool] = None) -> Optional[list[Card]]:
    if trump != Suit.TRUMP:
      self.hand = Card.convert_to_trump(self.hand, trump)
    if partner_alone:
      give_two = self.playing_strat.give_two_to_partner(self.hand, trump)
      for c in give_two:
        self.hand.remove(c)
      return give_two

    if kitty:
      logging.debug(f'{self.name} wins kitty {Card.stringify(kitty)}')
      kitty = Card.convert_to_trump(kitty, trump)
      self.hand.extend(kitty)
      self.discarded_cards = self.playing_strat.take_kitty(self.hand, len(kitty))
      for d in self.discarded_cards:
        self.hand.remove(d)
      logging.debug(f'{self.name} discards {Card.stringify(self.discarded_cards)}')

    self.playing_strat.start_hand(hand, prev_bids, my_index, self.discarded_cards)
    if kitty:
      return self.discarded_cards


  def update(self, cards_laid: dict[int, Card], cards_remaining: list[Card], my_index: int):
    cr = cards_remaining.copy()
    for c in self.hand:
      cr.remove(c)
    self.playing_strat.update(cards_laid, cr, my_index)

  def play_card(self, cards_laid: dict[int, Card], cards_remaining: list[Card]) -> Card:
    cards_laid
    if self.discarded_cards:
      cards_remaining = cards_remaining.copy()
      for x in self.discarded_cards:
        cards_remaining.remove(x)

    if cards_laid:
      card = self.playing_strat.follow(self.hand, cards_remaining, cards_laid)
    else:
      card = self.playing_strat.lead(self.hand, cards_remaining)
    if not card:
      logging.error(f'{self.name} failed to play with:')
      logging.error(f'Hand failed to play with: {Card.stringify(self.hand)}')
      logging.error(f'Laid: {Card.stringify(cards_laid)}')
      logging.error(f'Remaining: {Card.stringify(cards_remaining)}')

    self.hand.remove(card)
    return card
    
