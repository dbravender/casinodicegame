from copy import copy, deepcopy
from collections import Counter, defaultdict
from functools import partial
import json
import random
from operator import itemgetter

import gevent

COLORS = ('blue', 'red', 'black', 'green', 'white')


bills = ([60] * 5 + [70] * 5 + [80] * 5 + [90] * 5 + [10] * 6 + [40] * 6 +
         [50] * 6 + [20] * 8 + [30] * 8)


class Game(object):
    def __init__(self):
        self.bills = copy(bills)
        random.shuffle(self.bills)
        self.players = []
        self.next_color = 0
        self.current_player = None
        self.player_by_color = {}
        self.casino_bills = {}
        self.casino_dice = {}
        self.round = 0
        self.state = 'join'

    def reset(self):
        self.bills = copy(bills)
        random.shuffle(self.bills)
        for player in self.players:
            player.bills = []
        self.round = 0
        self.start_game()

    def serialize(self):
        state = deepcopy(self.__dict__)
        state['dice_per_casino'] = {c: self.dice_per_casino(c)
                                    for c in range(1, 7)}
        state['winners_by_casino'] = self.winners_by_casino()
        state['last_played_dice'] = self.last_played_dice()
        return json.dumps(
            state,
            default=lambda o: (hasattr(o, 'serialize') and o.serialize() or
                               o.__dict__))

    def join(self, player_id):
        if self.state != 'join' or len(self.players) >= 5:
            return
        color = COLORS[self.next_color]
        self.next_color += 1
        player = Player(color, player_id, game=self)
        self.players.append(player)
        self.player_by_color[color] = player
        return player

    def start_game(self):
        if len(self.players) < 2:
            raise TooFewPlayers()
        self.state = 'play'
        self.starting_player = self.players[-1]
        self.start_round()

    def last_played_dice(self):
        if not self.current_player:
            return {}
        played = defaultdict(dict)
        for casino in range(1, 7):
            total_white_played = sum(
                player.last_played_dice.get(casino, [0, 0])[1]
                for player in self.players)
            played[casino]['white'] = [None] * (
                self.casino_dice.get(casino, {}).get('white', 0) -
                total_white_played)
            for player in one_cycle(self.players, self.current_player):
                color_played, white_played = player.last_played_dice.get(
                    casino, [0, 0])
                played[casino]['white'].extend([player.color] * white_played)
                played[casino][player.color] = (
                    [None] * (self.casino_dice.get(casino, {})
                                              .get(player.color, 0) -
                              color_played))
                played[casino][player.color].extend([player.color] *
                                                    color_played)
        return played

    def winners_by_casino(self):
        winners = {}
        for casino in range(1, 7):
            dice_per_casino = self.dice_per_casino(casino)
            ties = [number for number, count
                    in (Counter(map(itemgetter(1),
                                    dice_per_casino))
                        .iteritems())
                    if count > 1]
            winners[casino] = [die[0] for die in dice_per_casino
                               if die[1] not in ties]
        return winners

    def score_round(self):
        winners = self.winners_by_casino()
        for casino in range(1, 7):
            for bill, color in zip(self.casino_bills[casino], winners[casino]):
                if color not in self.player_by_color:
                    # the white player is a neutral player sometimes
                    continue
                self.player_by_color[color].bills.append(bill)

    def start_round(self):
        self.round += 1
        if self.round > 4:
            self.state = 'gameover'
            return
        self.starting_player = next_wrap(self.players, self.starting_player)
        self.current_player = self.starting_player
        for player in self.players:
            player.start_round()
        for casino in range(1, 7):
            total = 0
            self.casino_dice[casino] = defaultdict(int)
            self.casino_bills[casino] = []
            while total < 50:
                bill = self.bills.pop()
                total += bill
                self.casino_bills[casino].append(bill)
            self.casino_bills[casino].sort(reverse=True)

    def play(self, casino, sleep=gevent.sleep):
        rolled_dice = self.current_player.rolled_dice[casino]
        self.casino_dice[casino][self.current_player.color] += rolled_dice[0]
        self.casino_dice[casino]['white'] += rolled_dice[1]
        self.current_player.remove_used_dice(casino, rolled_dice)
        self.current_player.roll()
        next_players = filter(
            lambda p: p.remaining_dice() > 0,
            one_cycle(self.players, self.current_player))
        if next_players:
            self.current_player = next_players[0]
        else:
            self.score_round()
            yield
            sleep(5)
            self.start_round()
        yield

    def dice_per_casino(self, casino):
        return sorted([(k, v) for k, v
                       in self.casino_dice.get(casino, {}).iteritems()
                       if v > 0],
                      key=itemgetter(1), reverse=True)


class Player(object):
    def __init__(self, color, player_id, game=None):
        self.game = game
        self.bills = []
        self.rolled_dice = {}
        self.last_played_dice = {}
        self.player_id = player_id
        self.color = color
        self.dice = 0
        self.white_dice = 0

    def serialize(self):
        c = deepcopy(self)
        del c.game  # to avoid circular data structures
        state = c.__dict__
        state['score'] = c.score()
        return state

    def remaining_dice(self):
        return self.dice + self.white_dice

    def score(self):
        return sum(self.bills)

    def start_round(self):
        self.dice = 8
        if len(self.game.players) == 2:
            self.white_dice = 4
        elif len(self.game.players) == 5:
            self.white_dice = 0
        else:
            self.white_dice = 2
        self.roll()

    def roll(self, randint=partial(random.randint, 1, 6)):
        my_dice = Counter([randint()
                           for _ in range(self.dice)])
        white_dice = Counter([randint()
                              for _ in range(self.white_dice)])
        self.rolled_dice = {}
        for x in set(white_dice.keys() + my_dice.keys()):
            self.rolled_dice[x] = [my_dice.get(x, 0), white_dice.get(x, 0)]

    def remove_used_dice(self, casino, used_dice):
        self.last_played_dice = {casino: used_dice}
        self.dice -= used_dice[0]
        self.white_dice -= used_dice[1]


def next_wrap(array, member):
    # itertools.cycle is not easily serializable
    index = array.index(member)
    try:
        return array[index + 1]
    except IndexError:
        return array[0]


def one_cycle(array, member):
    count = 0
    while count < len(array):
        member = next_wrap(array, member)
        yield member
        count += 1


class GameException(Exception):
    pass


class TooFewPlayers(GameException):
    pass
