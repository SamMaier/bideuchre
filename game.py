from cards import Suit, Card
from typing import Optional
import random

import logging
from player import Player


FULL_DECK = sorted([Card(s, i) for i in range(9, 15) for s in [Suit.SUIT_1, Suit.SUIT_2, Suit.SUIT_3, Suit.SUIT_4]] * 2)
DECK_SIZE = len(FULL_DECK)
KITTY_SIZE = 4
PLAYER_COUNT = 4
HAND_SIZE = (len(FULL_DECK) - KITTY_SIZE) // PLAYER_COUNT
class Hand:
  def __init__(self, players: list[Player], dealer: int):
    self.players = players[dealer:] + players[:dealer]

  def play_hand(self) -> tuple[int, int]:
    logging.info(f'Playing hand, dealer is {self.players[0].name}.')
    # Deal
    shuffled = random.sample(FULL_DECK, k=DECK_SIZE)
    kitty = shuffled[-KITTY_SIZE:]
    shuffled = shuffled[:-KITTY_SIZE]
    for i in range(len(self.players)):
      self.players[i].deal_hand(shuffled[i*HAND_SIZE:(i+1)*HAND_SIZE])

    # Bids
    prev_bids = []
    curr_bid = None
    for i, p in enumerate(self.players):
      bid = p.bid(prev_bids, curr_bid)
      if bid is not None:
        if curr_bid is not None:
          assert bid[0] > curr_bid[0]
        curr_bid = bid
        winner = i
      prev_bids.append(curr_bid)
    trump = curr_bid[1]
    amount = curr_bid[0]
    logging.debug(f'Winning bid is {amount}{trump}')

    for i, p in enumerate(self.players):
      c = p.bidding_finished(trump, kitty=kitty if i==winner else None)
      if c:
        discarded_cards = c

    cards_remaining = FULL_DECK.copy()
    if trump != Suit.TRUMP:
      cards_remaining = Card.convert_to_trump(cards_remaining, trump)
    cards_remaining = sorted(cards_remaining)

    # Play hands
    leader = winner
    tricks = [0,0]
    for i in range(HAND_SIZE):
      printstr = f'{i}:'
      cards_laid = []
      for i in range(PLAYER_COUNT):
        player = self.players[(i + leader) % PLAYER_COUNT]
        c = player.play_card(cards_remaining, cards_laid)
        cards_laid.append(c)
        cards_remaining.remove(c)
        printstr += f'  {player.name} {c}'
      leader = (Card.max(cards_laid) + leader) % PLAYER_COUNT
      tricks[leader % 2] += 1
      logging.info(printstr)
    logging.info(f'Bidder won {tricks[winner%2]}, other {tricks[(winner+1)%2]}')
    assert(cards_remaining == sorted(discarded_cards))

    # Score
    if tricks[winner%2] >= amount:
      tricks[winner%2] = amount
    else:
      tricks[winner%2] = -amount
      
    return tricks

class Game:
  def __init__(self, players: list[Player]):
    assert len(players) == PLAYER_COUNT
    self.players = players

  def play_game(self, num_hands=12) -> tuple[int, int]:
    first_deal = random.randrange(4)
    logging.info(f'Starting game - first dealer is {self.players[first_deal].name}')
    team0 = ''
    team1 = ''
    for i in range(len(self.players)):
      if i%2 == 0:
        team0 += self.players[i].name
      else:
        team1 += self.players[i].name
    logging.info(f'{team0} vs {team1}')
    score = [0,0]
    for i in range(num_hands):
      h = Hand(self.players, dealer=(i + first_deal) % 4)
      results = h.play_hand()
      score[0] += results[0]
      score[1] += results[1]
      logging.info(f'{team0}: {score[0]}, {team1}: {score[1]}')

    return score
