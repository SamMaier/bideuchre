#!/usr/bin/env python3
import logging
import time

from game import Game
from player import Player
from basic_strategies import RandomBidder, RandomPlayer, BasicBidder, BasicPlayer, GoodBidder, GoodPlayer

def run_many_games(game: Game, num_games_to_run: int):
  logging.info(f'Running {num_games_to_run}')

  victories = [0,0]
  team_0_diff = 0

  start = time.clock_gettime(time.CLOCK_MONOTONIC)
  for i in range (num_games_to_run):
    score = game.play_game(num_hands=12)
    team_0_diff += score[0] - score[1]
    if score[0] > score[1]:
      victories[0] += 1
    elif score[0] < score[1]:
      victories[1] += 1
    else:
      # Tie, doesn't affect accumulated stats
      continue
  end = time.clock_gettime(time.CLOCK_MONOTONIC)
  logging.debug(f'Took {end-start} seconds.')

  logging.warning(f'{game.team0}: {victories[0]} games')
  logging.warning(f'{game.team1}: {victories[1]} games')
  logging.warning(f'Avg margin for {game.team0} = {team_0_diff/num_games_to_run}')


logging.basicConfig(level=logging.WARNING)
g = Game([Player(BasicBidder(), BasicPlayer(), name='A'),
          Player(RandomBidder(), BasicPlayer(), name='b'),
          Player(BasicBidder(), BasicPlayer(), name='C'),
          Player(RandomBidder(), BasicPlayer(), name='d')])
run_many_games(g, 1000)
