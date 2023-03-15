#!/usr/bin/env python
# coding: utf-8

import pyglet
from pyglet.window import key

keys = key.KeyStateHandler()
window = pyglet.window.Window()
window.push_handlers(keys)

font_name = 'Times New Roman'
label = pyglet.text.Label('100 hp',
                          font_name=font_name,
                          font_size=36,
                          x=10, y=10)
roadsign = pyglet.text.Label('To forest',
                        font_name=font_name,
                        font_size=22,
                        x=10, y=window.height - 50)
hintsign = pyglet.text.Label('Press E to win',
                        font_name=font_name,
                        font_size=14,
                        x=8, y=window.height - 120)
