#!/usr/bin/env python3
from game import Game
from player import Player

g = Game([Player(), Player(), Player(), Player()])
g.play_game()
