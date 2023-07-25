#!/usr/bin/env python3
import logging

from game import Game
from player import Player
from basic_strategies import RandomBidder, RandomPlayer

logging.basicConfig(level=logging.DEBUG)
g = Game([Player(RandomBidder(), RandomPlayer(), name='a'), Player(RandomBidder(), RandomPlayer(), name='b'), Player(RandomBidder(), RandomPlayer(), name='c'), Player(RandomBidder(), RandomPlayer(), name='d')])
g.play_game(num_hands=3)
