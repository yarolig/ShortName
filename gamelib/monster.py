#!/usr/bin/env python
# coding: utf-8
import pyglet

from gamelib import data
from gamelib.weapon import WeaponAnim


class Monster:
    def __init__(self, image_prefix):
        self.name = ''
        self.race = ''
        self.hp = 100
        self.maxhp = 100
        self.friendly = False
        self.nodam = False
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.speed = 15
        self.jump_speed = 15

        self.right_hand = None
        self.left_hand = None
        self.armor = None
        self.hat = None
        self.weapon_anim = WeaponAnim()

        self.jump_left = 0
        self.hp = 100
        self.in_s = False
        self.in_w = False
        self.in_a = False
        self.in_d = False
        self.facing = 1
        self.in_thrust = False
        self.in_swing = False
        self.in_kick = False
        self.in_jump = False
        self.in_change = False
        self.in_drop = False
        self.in_use = False
        self.img_still =  pyglet.image.load(data.filepath(image_prefix))
        self.inventory = []
    def reset_input(self):
        self.in_s = False
        self.in_w = False
        self.in_a = False
        self.in_d = False
        self.in_thrust = False
        self.in_swing = False
        self.in_kick = False
        self.in_jump = False
        self.in_change = False
        self.in_drop = False
        self.in_use = False

    def refill_jump(self):
        self.jump_left = 10
    def draw(self):
        s = pyglet.sprite.Sprite(self.img_still,
                                x=self.x - 32 * self.facing,
                                y=self.y)
        if self.facing == -1:
            s.scale_x = -1
        s.draw()
        self.weapon_anim.draw(self)
