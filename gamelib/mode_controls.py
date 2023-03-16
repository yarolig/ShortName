#!/usr/bin/env python
# coding: utf-8
import pyglet
from pyglet.window import key

import gamelib.input
from gamelib.common import game
from gamelib.sky import startsky
from gamelib.ui import window, font_name, keys


def controls_mode_draw():
    window.clear()
    startsky().draw()
    class T:
        pos = 120
        dpos = 30
    t = T()
    def d(text):
        pyglet.text.Label(text, font_name=font_name,
                          font_size=18, x=30, y=window.height - t.pos).draw()
        t.pos += t.dpos
    for s in ['WSAD, Arrows - move',
              'F,K - thrust weapon',
              'V,J - swing weapon',
              'E - pick up, use, travel',
              'X - change weapon',
              'G - drop weapon',
              'Space - Jump',
              'S+Space, Down+Space - Jump down',
              'F1 - view controls',
              'Esc - quit',
              '',
              'Press Space to continue',
              ]:
        d(s)


def controls_phy():
    if keys[key.SPACE] or gamelib.input.jh.keys[1]:
        game().mode = game().previous_mode
