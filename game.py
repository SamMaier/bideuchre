from typing import Optional
import random
import logging

from cards import Suit, Card
from player import Player
from constants import DECK_SIZE, FULL_DECK, HAND_SIZE, KITTY_SIZE, LONE_HAND_POINTS, PLAYER_COUNT


class Hand:
  def __init__(self, players: list[Player], dealer: int, score: list[int], hands_left: int):
    self.reverse_scores = dealer % 2
    self.players = players[dealer:] + players[:dealer]
    self.score_delta = score[0]-score[1]
    if self.reverse_scores:
      self.score_delta = -self.score_delta
    self.hands_left = hands_left

  def play_hand(self) -> tuple[int, int]:
    logging.info(f'Dealer + first bid is {self.players[0].name}.')
    # Deal
    shuffled = random.sample(FULL_DECK, k=DECK_SIZE)
    kitty = shuffled[-KITTY_SIZE:]
    shuffled = shuffled[:-KITTY_SIZE]
    for i in range(len(self.players)):
      self.players[i].deal_hand(shuffled[i*HAND_SIZE:(i+1)*HAND_SIZE])

    # Bids
    prev_bids = []
    curr_max = 0
    for i, p in enumerate(self.players):
      bid = p.bid(prev_bids, curr_max, self.score_delta * (-1 if i % 2 == 1 else 0), self.hands_left)
      if bid is not None:
        assert bid[0] > curr_max
        curr_max = bid[0]
        winner = i
      prev_bids.append(bid)
      if curr_max > HAND_SIZE:
        break
    amount = prev_bids[winner][0]
    trump = prev_bids[winner][1]
    logging.debug(f'Winning bid is {amount}{trump}')

    discarded_cards = []
    out_of_game = None
    # LONE HAND!
    if amount > HAND_SIZE:
      amount = LONE_HAND_POINTS
      # TODO - will need a system for 6 hand to pick who to give.
      out_of_game = (winner + 2) % PLAYER_COUNT
      given_cards = self.players[out_of_game].bidding_finished(trump, None, None, partner_alone = True)
      kitty += given_cards
      discarded_cards += self.players[out_of_game].hand

    for i, p in enumerate(self.players):
      c = p.bidding_finished(trump, prev_bids, i, kitty=kitty if i==winner else None)
      if c:
        discarded_cards += c

    cards_remaining = FULL_DECK.copy()
    if trump != Suit.TRUMP:
      cards_remaining = Card.convert_to_trump(cards_remaining, trump)
    cards_remaining = sorted(cards_remaining, reverse=True)

    # Play hands
    leader = winner
    tricks = [0,0]
    for i in range(HAND_SIZE):
      printstr = f'{i}:'
      cards_laid = []
      for j in range(PLAYER_COUNT):
        idx = (j + leader) % PLAYER_COUNT
        if idx != out_of_game:
          player = self.players[idx]
          c = player.play_card(cards_remaining, cards_laid)
          cards_laid.append(c)
          cards_remaining.remove(c)
          printstr += f'  {player.name} {c}'
      for j in range(PLAYER_COUNT):
        idx = (j + leader) % PLAYER_COUNT
        if idx != out_of_game:
          self.players[idx].update_info(cards_laid, cards_remaining, j)
      trick_win = Card.max(cards_laid)
      if out_of_game is not None and trick_win >= out_of_game:
        trick_win += 1
      leader = (trick_win + leader) % PLAYER_COUNT
      tricks[leader % 2] += 1
      logging.info(printstr)
    logging.info(f'Bidder won {tricks[winner%2]}, other {tricks[(winner+1)%2]}')
    if cards_remaining != sorted(discarded_cards, reverse=True):
      logging.error(f'{Card.stringify(cards_remaining)}')
      logging.error(f'{Card.stringify(sorted(discarded_cards, reverse=True))}')
      assert False

    # Score
    if amount > HAND_SIZE and tricks[winner%2] == HAND_SIZE:
      # Little hack to make lone hands score naturally
      tricks[winner%2] = amount
    if tricks[winner%2] >= amount:
      tricks[winner%2] = amount
    else:
      tricks[winner%2] = -amount
      
    if self.reverse_scores:
      return [tricks[1], tricks[0]]
    return tricks

class Game:
  def __init__(self, players: list[Player]):
    assert len(players) == PLAYER_COUNT
    self.players = players
    self.team0 = ''
    self.team1 = ''
    for i in range(len(self.players)):
      if i%2 == 0:
        self.team0 += self.players[i].name
      else:
        self.team1 += self.players[i].name

  def play_game(self, num_hands=12) -> tuple[int, int]:
    first_deal = random.randrange(4)
    logging.info(f'Starting game - first dealer is {self.players[first_deal].name}')
    logging.info(f'{self.team0} vs {self.team1}')
    score = [0,0]
    for i in range(num_hands):
      if abs(score[0] - score[1]) > LONE_HAND_POINTS * (num_hands - i):
        logging.info(f'Ending game early')
        break
      h = Hand(self.players, (i+first_deal) % 4, score, num_hands-i)
      results = h.play_hand()
      score[0] += results[0]
      score[1] += results[1]
      logging.info(f'{self.team0}: {score[0]}, {self.team1}: {score[1]}')

    return score
