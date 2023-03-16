#!/usr/bin/env python
# coding: utf-8
import pyglet

from gamelib import data


class Item:
    def __init__(self, itemtype):
        self.x = 0
        self.y = 0
        self.itemtype = itemtype

    def draw(self, sx, sy, angle, batch=None):
        self.itemtype.draw(sx, sy, angle, batch)


class ItemType:
    alltypes = {}
    def __init__(self, name, fpath, damage=10, reach=10):
        if fpath:
            self.image = pyglet.image.load(data.filepath(fpath))
            self.image.anchor_x = 32
            self.image.anchor_y = 5

        else:
            self.image = None
        ItemType.alltypes[name]=self
        self.name = name
        self.damage = damage
        self.reach = reach
        self.grip = 'default'
        self.attack1 = 'thrust'
        self.attack2 = 'chop'
        self.health_potion = False

    def draw(self, sx, sy, angle=0, batch=None):
        if self.image is None:
            return
        s = pyglet.sprite.Sprite(self.image, x=sx, y=sy, batch=batch)
        if angle:
            s.rotation = angle
        if batch is None:
            s.draw()
        return s
    @classmethod
    def get(cls, name):
        return cls.alltypes.get(name)


def init_item_types():
    sword= ItemType('sword', 'pics/sword.png', 10, 47)
    sword.grip = 'change'
    spear= ItemType('spear', 'pics/spear.png', 10, 59)
    spear.grip = 'staff_default'
    polearm= ItemType('polearm', 'pics/polearm.png', 25, 59)
    polearm.grip = 'staff_default'

    staff= ItemType('staff', 'pics/staff.png', 5, 60)
    staff.grip = 'staff_default'
    staff.attack1 = 'staff_chop'
    staff.attack2 = 'staff_thrust'

    dagger= ItemType('dagger', 'pics/dagger.png', 30, 16)

    fire_wand= ItemType('fire_wand', 'pics/fire_wand.png', 5, 45)
    fire_wand.attack2 = 'fire'

    ice_wand= ItemType('ice_wand', 'pics/ice_wand.png', 5, 45)
    ice_wand.attack2 = 'ice'

    force_wand= ItemType('force_wand', 'pics/force_wand.png', 15, 60)
    force_wand.attack2 = 'force'
    force_wand.grip = 'staff_default'

    axe= ItemType('axe', 'pics/axe.png', 50, 47)
    axe.attack1 = 'axe'
    axe.attack2 = 'axe'
    axe.grip = 'staff_default'

    potion = ItemType('potion', 'pics/potion.png', 30, 47)
    potion.health_potion = True
