from unittest import TestCase

from casinodicegame.game import (
    Game, Player, TooFewPlayers, next_wrap, one_cycle
)


class TestPlayer(TestCase):
    def test_remaining_dice(self):
        player = Player('red', 'fakeid')
        player.dice = 1
        player.white_dice = 1
        self.assertEqual(player.remaining_dice(), 2)

        player.dice = 0
        self.assertEqual(player.remaining_dice(), 1)

    def test_roll(self):
        player = Player('red', 'fakeid')
        player.dice = 2
        player.white_dice = 0
        fakeroll = iter([2, 2])
        player.roll(randint=fakeroll.next)
        self.assertEqual(player.rolled_dice, {2: [2, 0]})

        player.dice = 3
        player.white_dice = 1
        fakeroll = iter([2, 2, 1, 1])
        player.roll(randint=fakeroll.next)
        self.assertEqual(player.rolled_dice, {2: [2, 0], 1: [1, 1]})

    def test_start_round(self):
        game = Game()
        player1 = game.join('player1')
        game.join('player2')
        player1.start_round()
        self.assertEqual(4, player1.white_dice)
        self.assertEqual(8, player1.dice)

        game.join('player3')
        self.assertEqual(len(game.players), 3)
        player1.start_round()
        self.assertEqual(2, player1.white_dice)
        self.assertEqual(8, player1.dice)

        game.join('player4')
        game.join('player5')
        player1.start_round()
        self.assertEqual(0, player1.white_dice)

    def test_score(self):
        game = Game()
        player1 = game.join('player1')
        player1.bills = [90, 90]
        self.assertEqual(player1.score(), 180)

    def test_remove_used_dice(self):
        game = Game()
        player1 = game.join('player1')
        player1.white_dice = 2
        player1.dice = 4
        player1.remove_used_dice(1, [2, 1])
        self.assertEqual(player1.white_dice, 1)
        self.assertEqual(player1.dice, 2)


class TestGame(TestCase):
    def test_join(self):
        game = Game()
        map(game.join, range(5))
        self.assertEqual(len(game.players), 5)

        game = Game()
        map(game.join, range(6))
        self.assertEqual(len(game.players), 5)

    def test_start_game(self):
        game = Game()
        game.join('player1')
        self.assertRaises(TooFewPlayers, game.start_game)

    def test_serialize(self):
        game = Game()
        game.join('player1')
        game.join('player2')
        game.start_game()
        # no real assertions - just make sure serialization works
        game.serialize()

    def test_round_start(self):
        game = Game(choice=lambda players: players[-1])
        player1 = game.join('player1')
        player2 = game.join('player2')
        game.start_game()
        self.assertEqual(game.round, 1)
        game.bills = [90, 90, 90, 90, 20, 30, 10, 10, 10, 10, 10] * 2
        self.assertEqual(game.current_player, player1)
        self.assertEqual(game.starting_player, player1)
        game.start_round()
        self.assertEqual(
            game.casino_bills,
            {1: [10, 10, 10, 10, 10], 2: [30, 20], 3: [90], 4: [90], 5: [90],
             6: [90]})
        self.assertEqual(game.current_player, player2)
        self.assertEqual(game.starting_player, player2)

    def test_winners_by_casino_and_score_round(self):
        game = Game()
        player1 = game.join('player1')
        player2 = game.join('player2')
        game.start_game()
        game.casino_dice = {
            1: {player1.color: 2},
            2: {player1.color: 2, 'white': 2, player2.color: 1},
            3: {player1.color: 3, 'white': 2, player2.color: 1},
            4: {},
            5: {},
            6: {}
        }
        self.assertEqual(
            game.winners_by_casino(),
            {
                1: [player1.color],
                2: [player2.color],
                3: [player1.color, 'white', player2.color],
                4: [],
                5: [],
                6: []
            })
        game.casino_bills = {
            1: [90, 90],
            2: [90],
            3: [100, 80, 70],
            4: [],
            5: [],
            6: []
        }
        game.score_round()
        self.assertEqual(player1.bills, [90, 100])
        self.assertEqual(player2.bills, [90, 70])

    def test_play(self):
        game = Game(choice=lambda players: players[-1])
        player1 = game.join('player1')
        player2 = game.join('player2')
        game.start_game()
        self.assertEqual(game.current_player, player1)
        game.casino_bills = {
            1: [90, 80],
            2: [50],
            3: [100, 80, 70],
            4: [],
            5: [],
            6: []
        }
        player1.dice = 2
        player1.white_dice = 1
        player1.rolled_dice = {1: [2, 1]}
        player2.dice = 0
        player2.white_dice = 0
        # list forces evaluation
        list(game.play(1, sleep=lambda x: None))
        # the round should be over now because all the dice have been played
        # player1 started so it should now be player2's turn
        self.assertEqual(game.round, 2)
        self.assertEqual(game.current_player, player2)
        self.assertEqual(player1.bills, [90])
        self.assertEqual(player1.last_played_dice, {1: [2, 1]})

    def test_last_played_dice(self):
        game = Game()
        player1 = game.join('player1')
        player2 = game.join('player2')
        player1.last_played_dice = {1: [2, 1]}
        player2.last_played_dice = {1: [3, 1]}
        game.start_game()
        game.current_player = player2
        game.casino_dice = {1: {player1.color: 3, player2.color: 3,
                                'white': 2}}
        self.assertEqual(
            game.last_played_dice()[1],
            {player1.color: [None, player1.color, player1.color],
             player2.color: [player2.color] * 3,
             'white': [player1.color, player2.color]})
        game.casino_dice[1]['white'] = 3
        self.assertEqual(
            game.last_played_dice()[1],
            {player1.color: [None, player1.color, player1.color],
             player2.color: [player2.color] * 3,
             'white': [None, player1.color, player2.color]})


class TestUtil(TestCase):
    def test_next_wrap(self):
        self.assertEqual(next_wrap([0, 1, 2], 2), 0)
        self.assertEqual(next_wrap([0, 1, 2], 1), 2)
        self.assertEqual(next_wrap([0, 1, 2], 0), 1)

    def test_one_cycle(self):
        self.assertEqual(list(one_cycle([0, 1, 2], 1)), [2, 0, 1])
        self.assertEqual(list(one_cycle([0, 1, 2], 2)), [0, 1, 2])
