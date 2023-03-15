#!/usr/bin/env python
# coding: utf-8

game_ = None

def xyrange(w,h):
    for x in range(w):
        for y in range(h):
            yield x, y

def set_game(g):
    global game_
    print('set game')
    game_ = g

def game():
    """

    @rtype: gamelib.game.Game
    """
    return game_


frameno = 0
AIR = 0
PLATFORM = 1
LADDER = 2
SOLID = 3
MAGMA = 4
