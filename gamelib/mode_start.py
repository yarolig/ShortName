#!/usr/bin/env python
# coding: utf-8
import pyglet
from pyglet.window import key

from gamelib.common import game
from gamelib.game import start_game
from gamelib.sky import startsky
from gamelib.ui import keys, window, font_name


def start_phy():
    if keys[key.O]:
        game().mode = 'game'
        start_game('orc')
    if keys[key.G]:
        game().mode = 'game'
        start_game('goblin')
    if keys[key.T]:
        game().mode = 'game'
        start_game('troll')

    if keys[key.D]:
        game().mode = 'game'
        start_game('dragon')

    if keys[key.F1]:
        game().mode = 'controls'


def start_mode_draw():
    window.clear()
    startsky().draw()

    class T:
        pos = 150
        dpos = 50
    t = T()
    def d(text):
        pyglet.text.Label(text, font_name=font_name,
                          font_size=18, x=30, y=window.height - t.pos).draw()
        t.pos += t.dpos
    for s in ['Press O to start as an Orc',
              'Press G to start as a Goblin',
              'Press F1 to view controls',
              'Press Esc to exit']:
        d(s)
