import collections
import logging
import math
import random
from typing import Optional

from cards import Suit, Card
from constants import LONE_HAND_POINTS, FULL_DECK
from card_predictor import CardPredictor


Bid = tuple[int, Suit]

class BiddingStrategy:
  def bid(self, hand: list[Card], prev_bids: list[Bid], curr_max: int) -> Bid:
    return None


class RandomBidder(BiddingStrategy):
  def bid(self, hand: list[Card], prev_bids: list[Bid], curr_max: int, score_delta: int, hands_left: int) -> Bid:
    s = random.choice(hand).suit
    num = random.randrange(len(hand))
    if num > curr_max:
      return (num, s)
    else:
      return None

# Does not bid NT nor consider partners.
class BasicBidder(BiddingStrategy):
  def bid(self, hand: list[Card], prev_bids: list[Bid], curr_max: int, score_delta: int, hands_left: int) -> Bid:
    suit_trick_map = collections.defaultdict(int)
    for c in hand:
      if c.number == 14:
        suit_trick_map[Suit.SUIT_1] += 1
        suit_trick_map[Suit.SUIT_2] += 1
        suit_trick_map[Suit.SUIT_3] += 1
        suit_trick_map[Suit.SUIT_4] += 1
      else:
        suit_trick_map[c.suit] += 1
        if c.number == 11:
          suit_trick_map[c.suit.left()] += 1

    best_suit = max(suit_trick_map, key=suit_trick_map.get)
    best_bid = suit_trick_map[best_suit]
    if best_bid > curr_max:
      # Just a random guess of going alone
      if best_bid >= 9:
        return len(hand) + 1, best_suit
      return best_bid, best_suit
    return None
      

class GoodBidder(BiddingStrategy):
  # Lone hands are > 11, but to choose which one, we can be 12-17
  def bid(self, hand: list[Card], prev_bids: list[Bid], curr_max: int, score_delta: int, hands_left: int) -> Bid:
    assert len(prev_bids) <= 3 # This is a 4-hand only strat
    partner_bid = None
    opp_bids = []
    for i, b in enumerate(reversed(prev_bids)):
      if i % 2:
        if b:
          partner_bid = b
        else:
          partner_bid = 0, Suit.TRUMP
      else:
        opp_bids.append(b)
    trust_indication = len(prev_bids) == 2 or (len(prev_bids) == 3 and not opp_bids[0])

    # Approx how many tricks worth we expect with this suits trump.
    per_suit_trump_score = {}

    # 3 for right, 1 for left
    per_suit_bauer_score = {}
    offsuit_fixed_tricks = collections.defaultdict(int)
    no_trump_bid = 0
    for s in Suit.just_suits():
      cards = sorted([c for c in hand if s == c.suit], reverse=True)

      left_bauers = [c for c in hand if Suit.left(s) == c.suit and c.number == 11]
      per_suit_trump_score[s] = len(left_bauers) * 1.25
      per_suit_bauer_score[s] = len(left_bauers)
      for c in cards:
        if c.number == 11:
          per_suit_bauer_score[s] += 3
          per_suit_trump_score[s] += 1.6
        elif c.number >= 13:
          per_suit_trump_score[s] += 0.9
        else:
          per_suit_trump_score[s] += 0.7

      # AAK is safe unless someone else bid 4+ in this suit.
      fixed_threshold = 3
      for b in opp_bids:
        if b and b[1] == s and b[0] >= 4:
          fixed_threshold = 4
      num_nt = 0
      boss_card = 14
      for c in cards:
        if c.number == boss_card or num_nt >= fixed_threshold:
          num_nt += 1
          if num_nt % 2 == 0:
            boss_card -= 1
        else:
          break

      for z in Suit.just_suits():
        if z != s:
          offsuit_fixed_tricks[z] += num_nt
      no_trump_bid += num_nt

    best_lone, lone_score = self.get_best_lone(per_suit_bauer_score,
        per_suit_trump_score, offsuit_fixed_tricks, no_trump_bid, partner_bid, trust_indication)
    # As a 0-1.0, how many lone hands are needed to catch up, assuming 8 bids otherwise.
    lones_needed_pct = math.ceil((-score_delta) - (hands_left * 5)/(LONE_HAND_POINTS-5))/hands_left
    if lones_needed_pct > 0.8:
      if len(prev_bids) >= 2:
        # Gotta go alone.
        logging.debug('Forced lone hand')
        return 12, best_lone
      else:
        # Have the option to indicate.
        if lone_score > 5.5:
          logging.debug('Decided I am better than partner likely will be')
          return 12, best_lone
        best_indication = self.indicate(per_suit_bauer_score, no_trump_bid)
        if best_indication[0] <= curr_max:
          best_indication = (curr_max + 1, best_indication[1])
        logging.debug('Forced to indicate')
        return best_indication

      
    # NORMAL BIDS - as if we were tied.
    best_bid = self.get_best_bid(per_suit_trump_score, no_trump_bid, offsuit_fixed_tricks, opp_bids, partner_bid, trust_indication)
    logging.debug(f'Best bid: {best_bid}')
    logging.debug(f'Best lone: {lone_score} {best_lone}')
    # See how desperate/safe we should be - positive is more desperate
    desperation = (-score_delta)/hands_left
    if lone_score > 9 - desperation/5:
      return 12, best_lone
    adjusted_bid_val = best_bid[0] + desperation/8
    if adjusted_bid_val < 6:
      indication = self.indicate(per_suit_bauer_score, no_trump_bid)
      if indication[0] > curr_max:
        return indication
    # Don't want to bid something we've evaled to be 2 tricks but not an indicate 2 bid.
    if adjusted_bid_val > max(curr_max, 3):
      return max(round(adjusted_bid_val), curr_max+1), best_bid[1]
    return None

     
  # Return the bid you'd make if we were even scores.
  def get_best_bid(self,
                   per_suit_trump_score: dict[Suit, float],
                   no_trump_bid: int,
                   offsuit_fixed_tricks: dict[Suit, int],
                   opp_bids: list[Bid],
                   partner_bid: Bid,
                   trust_indication: bool) -> tuple[float, Suit]:
    # Assuming 0.5 in all for a partner we know nothing about.
    net_scores = {s: 0.5 for s in Suit}
    if partner_bid and partner_bid[0] == 0:
      # Partner passed
      if len(opp_bids) == 1 or not opp_bids[0] or opp_bids[0][0] <= 4:
        # Partner has nothing
        net_scores = {s: 0 for s in Suit}
    elif partner_bid:
      if partner_bid[1] == Suit.TRUMP:
        net_scores = {s: 0.25*partner_bid[0] for s in Suit.just_suits()}
        net_scores[Suit.TRUMP] = partner_bid[0] - 1
      else:
        # Indicate 1->1.5 trick
        # Indicate 2->2.5 trick
        # Indicate 3->2.5 trick
        # Indicate 4+ -> tricks/2
        if trust_indication and partner_bid[0] <= 3:
          net_scores[partner_bid[1]] = (partner_bid[0] // 2) + 1.5
        else:
          net_scores[partner_bid[1]] = partner_bid[0]/2
    # Subtracting off bids from opponents
    for b in opp_bids:
      if b:
        net_scores[b[1]] -= b[0] / 2
        left = Suit.left(b[1])
        if left != b[1]:
          net_scores[left] -= 1

    net_scores[Suit.TRUMP] += no_trump_bid
    for s in Suit.just_suits():
      net_scores[s] += per_suit_trump_score[s]
      # Only count all offsuit if we have a good enough hand to get to offsuit.
      if net_scores[s] > 6.5:
        net_scores[s] += offsuit_fixed_tricks[s]
      elif net_scores[s] > 4:
        net_scores[s] += offsuit_fixed_tricks[s]/2

    suit = max(net_scores, key=net_scores.get)
    return net_scores[suit], suit

  def indicate(self, per_suit_bauer_score: dict[Suit, int], no_trump_fixed: int) -> Bid:
    suit = max(per_suit_bauer_score, key=per_suit_bauer_score.get)
    if per_suit_bauer_score[suit] == 3:
      return 1, suit
    elif per_suit_bauer_score[suit] == 6:
      return 2, suit
    elif per_suit_bauer_score[suit] == 4:
      return 3, suit
    return no_trump_fixed, Suit.TRUMP


  # 11 is basically a sure lone hand. 9 is a very sketchy one. 12+ is almost a laydown.
  def get_best_lone(self,
                    per_suit_bauer_score: dict[Suit, int],
                    per_suit_trump_score: dict[Suit, int],
                    offsuit_fixed_tricks: dict[Suit, int],
                    no_trump_bid: int,
                    partner_bid: Bid,
                    trust_indication: bool) -> tuple[Suit,float]:
    lone_scores = per_suit_bauer_score.copy()
    lone_scores[Suit.TRUMP] = no_trump_bid + 1.5 # For tiebreaker
    if partner_bid:
      partner_amount = partner_bid[0]
      partner_suit = partner_bid[1]
      if partner_suit == Suit.TRUMP:
        lone_scores[Suit.TRUMP] += min(2, partner_amount)
      else:
        adjusted_partner_amount = 3
        left_amount = 1
        if trust_indication:
          # Can trust indication.
          if partner_amount == 3:
            adjusted_partner_amount = 4
            left_amount = 4
          elif partner_amount == 2:
            adjusted_partner_amount = 6
            left_amount = 2
        
        lone_scores[partner_suit] += adjusted_partner_amount
        lone_scores[Suit.left(partner_suit)] += left_amount

    for s in Suit.just_suits():
      if per_suit_trump_score[s] < 5:
        lone_scores[s] -= 1
      elif per_suit_trump_score[s] > 6:
        lone_scores[s] += math.floor(per_suit_trump_score[s]) - 5
      offsuit = offsuit_fixed_tricks[s]
      if lone_scores[s] >= 8:
        lone_scores[s] += offsuit
      elif lone_scores[s] >= 6.5:
        lone_scores[s] += offsuit/2

    best_lone = max(lone_scores, key=lone_scores.get)
    return best_lone, lone_scores[best_lone]

class PlayingStrategy:
  def start_hand(self,
                 hand: list[Card],
                 bids: list[Bid],
                 my_index: int,
                 known_missing_cards: Optional[list[Card]] = None):
    self.card_predictor = CardPredictor(bids, my_index, known_missing_cards)

  @staticmethod
  def get_legal_plays(hand: list[Card], cards_laid: list[Card]) -> set[Card]:
    suit = cards_laid[0].suit
    follow_suit = {c for c in hand if c.suit == suit}
    if follow_suit:
      return follow_suit
    return set(hand)

  def give_two_to_partner(self, hand: list[Card], trump: Suit) -> list[Card]:
    def _eval(card):
      if not card:
        return 0
      # Basically, you always give a bauer. Then, next priority is offsuit aces.
      # So, you want offsuit aces to score higher than trump aces.
      # RB -> 32
      # LB -> 30
      # AOff -> 29
      # AT -> 28
      # ...
      # 8T -> 16 (higher than other offsuit)
      if card.suit == Suit.TRUMP:
        return card.number * 2
      else:
        if card.number == 14:
          return 29
        else:
          return card.number

    best_card = None
    second_card = None
    for c in hand:
      if _eval(c) > _eval(best_card):
        second_card = best_card
        best_card = c
      elif _eval(c) > _eval(second_card):
        second_card = c
    return [best_card, second_card]

  def lead(self, hand: list[Card], cards_remaining: list[Card]) -> Card:
    raise Exception()
  def follow(self, hand: list[Card], cards_remaining: list[Card], cards_laid: list[Card]) -> Card:
    raise Exception()
  # Returns discarded cards.
  def take_kitty(self, hand: list[Card], kitty_size: int) -> list[Card]:
    raise Exception()



class RandomPlayer(PlayingStrategy):
  def lead(self, hand: list[Card], cards_remaining: list[Card]) -> Card:
    return random.choice(hand)

  def follow(self, hand: list[Card], cards_remaining: list[Card], cards_laid: list[Card]) -> Card:
    return random.choice(list(PlayingStrategy.get_legal_plays(hand, cards_laid)))

  # Returns discarded cards.
  def take_kitty(self, hand: list[Card], kitty_size: int) -> list[Card]:
    return random.sample(hand, kitty_size)


class BasicPlayer(PlayingStrategy):
  # Basic player always leads boss cards if they have one, random else.
  def lead(self, hand: list[Card], cards_remaining: list[Card]) -> Card:
    selection = None
    for c in hand:
      boss_value = c.is_boss(cards_remaining)
      if boss_value == 10:
        return c
      if boss_value == 1:
        selection = c
    if selection:
      return selection
    return random.choice(hand)

  def basic_throwaway(legal_plays: list[Card]):
    min_card = Card(Suit.TRUMP, 1000)
    for c in legal_plays:
      if c.suit == Suit.TRUMP: 
        if min_card.suit == Suit.TRUMP and c.number < min_card.number:
          min_card = c
      elif c.number < min_card.number or min_card.suit == Suit.TRUMP:
        min_card = c
    return min_card


  # Basic player wins with boss card if they have one, lowest else.
  def follow(self, hand: list[Card], cards_remaining: list[Card], cards_laid: list[Card]) -> Card:
    legal_plays = list(PlayingStrategy.get_legal_plays(hand, cards_laid))
    for c in legal_plays:
      if c.is_boss(cards_remaining) and Card.max(cards_laid + [c]) == len(cards_laid):
        return c

    return BasicPlayer.basic_throwaway(legal_plays)
      

  # Removes lowest value offsuit.
  def take_kitty(self, hand: list[Card], kitty_size: int) -> list[Card]:
    hand = hand.copy()
    throwaways = []
    for i in range(kitty_size):
      c = BasicPlayer.basic_throwaway(hand)
      hand.remove(c)
      throwaways.append(c)
    return throwaways


class GoodPlayer(PlayingStrategy):

  def take_kitty(self, hand: list[Card], kitty_size: int) -> list[Card]:
    hand = hand.copy()
    throwaways = []

    # Ignore trump since we will never throw it away.
    suit_counts_with_ace_ct = {s: [0, 0] for s in Suit.JUST_SUITS}
    for c in hand:
      suit_count = suit_counts_with_bare_ace[c.suit]
      suit_count[0] += 1
      if c.number == 14:
        suit_count[1] += 1
    # Priority 1 - Shortsuit any non-Ace suits
    no_ace_suits = {k, v for k, v in suit_counts_with_ace_ct.items() if v[1] == 0 and v[0] >= 1}
    while True:
      min_suit = min(no_ace_suits,
                     key=lambda x: no_ace_suits[x][0])
      if no_ace_suits[min_suit][0] <= kitty_size - len(throwaways):
        for c in hand:
          if c.suit == min_suit:
            hand.remove(c)
            throwaways.append(c)
        del(no_ace_suits[min_suit])
      else:
        break

    # Priority 2 - Make 1 ace bare
    one_ace_suits = {k, v for k, v in suit_counts_with_ace_ct.items() if v[1] == 1 and v[0] >= 1}
    min_suit = min(one_ace_suits,
                   key=lambda x: one_ace_suits[x][0])
    if one_ace_suits[min_suit][0] - 1 <= kitty_size - len(throwaways):
      for c in hand:
        if c.suit == min_suit and c.number != 14:
          hand.remove(c)
          throwaways.append(c)
    
    # Priority 3 - throwaway logic
    for i in range(kitty_size - len(throwaways)):
      c = GoodPlayer.optimal_throwaway(hand, hand)
      hand.remove(c)
      throwaways.append(c)

    assert len(throwaways) == kitty_size
    return 

  def optimal_throwaway(legal_plays: list[Card]):
    # If all same suit, play lowest.
    # If choices of suit,
    #  aim to short suit if suit has no ace
    #  keep 1 backup if no ace in suit laid yet
    #  play from suit less likely for opponents to have
    pass
