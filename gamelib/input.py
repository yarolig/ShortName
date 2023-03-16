#!/usr/bin/env python
# coding: utf-8
from typing import List

from pyglet.input import Device
from pyglet.window import key

import gamelib.ui
from gamelib.common import game
from gamelib.ui import keys
import pyglet.input
import  pyglet

from collections import defaultdict
'''
controllers = pyglet.input.get_devices()
print (controllers)

open_controllers: list[Device] = []
for c in controllers:
    c.open()
    open_controllers.append(c)
    break
'''

class JoystickHandler:
    def __init__(self):
        self.keys = defaultdict(bool)
        self.hatx = 0
        self.haty = 0

    def on_joybutton_press(self, joystick, button):
        print('on_joybutton_press', button)
        self.keys[button] = True

    def on_joybutton_release(self, joystick, button):
        print('on_joybutton_release', button)
        self.keys[button] = False

    def on_joyaxis_motion(self,joystick, axis, value):
        if axis=='hat_x':
            self.hatx = value
            print('hatx', value)
        if axis=='hat_y':
            print('haty', value)
            self.haty = value
        #print('on_joyaxis_motion', axis, value)

jh = JoystickHandler()

joysticks = pyglet.input.get_joysticks()
print(joysticks)
for c in joysticks:
    c.open()
    c.push_handlers(jh)

def process_input():
    game().player.reset_input()
    #print ( ' '.join([key.symbol_string(k) for k in keys.keys() if keys[k]]) + ' | ' + str(jh.keys.items()))
    #print keys
    #print(jh.hatx, jh.haty, jh.keys)
    if keys[key.LEFT] or keys[key.A] or jh.hatx < -0.5:
        game().player.in_a = True
    if keys[key.RIGHT] or keys[key.D] or jh.hatx > 0.5:
        game().player.in_d = True
    if keys[key.DOWN] or keys[key.S] or jh.haty < -0.5:
        game().player.in_s = True
    if keys[key.UP] or keys[key.W] or jh.haty > 0.5:
        game().player.in_w = True

    if keys[key.SPACE] or jh.keys[1]:
        game().player.in_jump = True

    if keys[key.J] or keys[key.V]  or jh.keys[0]:
        game().player.in_thrust = True
    if keys[key.K] or keys[key.F]  or jh.keys[2]:
        game().player.in_swing = True

    if keys[key.X] or jh.keys[5]:
         game().player.in_change = True
    if keys[key.E] or jh.keys[3]:
        game().player.in_use = True
    if keys[key.G] or jh.keys[4]:
        game().player.in_drop = True

    if keys[key.F1] or jh.keys[10]:
        if game().mode in ('start', 'game'):
            game().previous_mode = game().mode
            game().mode = 'controls'
