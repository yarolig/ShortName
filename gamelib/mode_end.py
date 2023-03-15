#!/usr/bin/env python
# coding: utf-8
import pyglet
from pyglet.window import key

from gamelib.common import game
from gamelib.logic import change_level
from gamelib.sky import startsky
from gamelib.stats import Stats
from gamelib.ui import window, font_name, keys


def end_mode_draw():
    window.clear()
    startsky().draw()
    pyglet.text.Label(game().end_text, font_name=font_name,
                      font_size=28, x=window.width // 2, y=window.height - 50, anchor_x='center').draw()
    pyglet.text.Label(game().end_bottom_text, font_name=font_name,
                      font_size=14, x=50, y=20).draw()

    class T:
      pos = 290
      dpos = 30
    t = T()
    def d(text):
      pyglet.text.Label(text, font_name=font_name,
                        font_size=18, x=30, y=window.height - t.pos).draw()
      t.pos += t.dpos
    for s in ['orcs defeated: %d' % Stats.orcs,
              'goblins defeated: %d' % Stats.goblins,
              'trolls defeated: %d' % Stats.trolls,
              'dragons defeated: %d' % Stats.dragons,
              'sacks destroyed: %d' % Stats.sacks,
              'restarts: %d' % Stats.restarts, ]:
      d(s)


def end_phy():
    if keys[key.SPACE]:
        game().mode = 'game'
        Stats.restarts += 1
        change_level(game().last_level, game().last_entry)
