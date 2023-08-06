PLAYER_COUNT = 4
LONE_HAND_POINTS = 16
FULL_DECK = sorted([Card(s, i) for i in range(9, 15) for s in [Suit.SUIT_1, Suit.SUIT_2, Suit.SUIT_3, Suit.SUIT_4]] * 2, reverse=True)
DECK_SIZE = len(FULL_DECK)
KITTY_SIZE = 4
HAND_SIZE = (len(FULL_DECK) - KITTY_SIZE) // PLAYER_COUNT
