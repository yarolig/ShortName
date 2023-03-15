#!/usr/bin/env python
# coding: utf-8
from pyglet.window import key

from gamelib.common import game
from gamelib.ui import keys


def process_input():
    game().player.reset_input()
    #print keys
    if keys[key.LEFT] or keys[key.A]:
        game().player.in_a = True
    if keys[key.RIGHT] or keys[key.D]:
        game().player.in_d = True
    if keys[key.DOWN] or keys[key.S]:
        game().player.in_s = True
    if keys[key.UP] or keys[key.W]:
        game().player.in_w = True

    if keys[key.SPACE]:
        game().player.in_jump = True
    if keys[key.J] or keys[key.V]:
        game().player.in_thrust = True
    if keys[key.K] or keys[key.F]:
        game().player.in_swing = True
    if keys[key.L]:
        game().player.in_kick = True
    if keys[key.X]:
         game().player.in_change = True
    if keys[key.E]:
        game().player.in_use = True
    if keys[key.G]:
        game().player.in_drop = True

    if keys[key.F1]:
        if game().mode in ('start', 'game'):
            game().previous_mode = game().mode
            game().mode = 'controls'
