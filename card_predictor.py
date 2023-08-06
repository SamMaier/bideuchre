from cards import Suit, Card

class CardPredictor:
  # self.others has:
  #  0 -> left opponent
  #  1 -> partner
  #  2 -> right opponent
  # Each entry is dict, containing the following keys:
  #  "known_cards" - 100% deduced
  #  "higher_odds_cards" - usually based on bidding, these are more likely
  #                        to show up in this player's hand than others
  #  "lowest_card_per_suit" - deduced from throwaways
  def __init__(self, 
               bids: list[Bid],
               my_index: int,
               known_missing_cards: Optional[list[Card]] = None):
):
    self.known_missing_cards = known_missing_cards
    lowest_bid = min(bids, key=lambda x: x[0] if x else 1234)
    winning_suit = min(bids, key=lambda x: x[0] if x else 0)[1]
    self.others = [None, None, None]
    for i, b in enumerate(bids):
      if i == my_index:
        continue
      if i < my_idx:
        others_idx = i - my_idx
      else:
        others_idx = i - 1 - my_idx

      self.others[others_idx] = self._construct_card_knowledge(b, lowest_bid==bid, trump)

  def _construct_card_knowledge(self, bid: Bid, is_lowest_bidder: bool, trump: Suit):
    card_knowledge = {'known_cards': [],
        'higher_odds_cards': [],
        'lowest_card_per_suit': {s: 9 for s in Suit if s != trump}}
    if bid:
      if bid[0] <= 3 and is_lowest_bidder:
        card_knowledge['known_cards'] = # TODO fill in bauers
      else:
        card_knowledge['higher_odds_cards'] = # TODO fill in this
    else:
      # TODO - could incoporate zero bid passers as having no aces or bauers, but only
      # when we know they are trying (ie. not when the game is close to out of reach).
      pass

    return card_knowledge

  def update(self, cards_laid: list[Card], cards_remaining: list[Card], my_index: int):
    suit_led = cards_laid[0].suit
    for i, c in enumerate(cards_laid):
      if i == my_index:
        continue
      if i < my_idx:
        others_idx = i - my_idx
      else:
        others_idx = i - 1 - my_idx
      other = self.others[others_idx]
      if c in other['known_cards']:
        other['known_cards'].remove(c)
      if c.suit != suit_led:
        other['lowest_card_per_suit'][suit_led] = None
      is_throwaway = Card.max(cards_laid[:i]) != i
      if is_throwaway:
        other['lowest_card_per_suit'][c.suit] = c.number

    for s in Suit:
      min_card_remaining = min([x.number for x in cards_remaining if x.suit == s], default=None)
      for o in self.others:
        if not min_card_remaining or
           (o['lowest_card_per_suit'][s] and o['lowest_card_per_suit'][s] < min_card_remaining):
          o['lowest_card_per_suit'][s] = min_card_remaining

    cards_to_be_assigned = cards_remaining
    for o in others:
      for c in o['known_cards']:
        cards_to_be_assigned.remove(c)
    for c in cards_to_be_assigned:
      other_who_could = None
      two_others_could = False
      for o in self.others:
        if o['lowest_card_per_suit'][c.suit] and c.number >= o['lowest_card_per_suit'][c.suit]:
          if other_who_could:
            two_others_could = True
            break
          other_who_could = o
      if not two_others_could:
        other_who_could['known_cards'].append(c)
    
