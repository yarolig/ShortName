#!/usr/bin/env python
# coding: utf-8
import pyglet

from gamelib.sky import startsky
from gamelib.ui import window, font_name


def load_mode_draw():
    window.clear()
    startsky().draw()
    pyglet.text.Label(load_mode_text, font_name=font_name,
                      font_size=18, x=30, y=window.height // 2).draw()

    load_mode_action()


load_mode_action = lambda: True
load_mode_text = 'Loading...'
