#!/usr/bin/env python
# coding: utf-8
import random

import pyglet

from gamelib import data
from gamelib.common import game
from gamelib.stats import Stats


class WeaponEffect:
    NONE = 0
    HIT = 1
    CHANGE_WEAPON = 2
    FIREBALL = 3
    FORCEWAVE = 4
    ICEBLAST = 5
    def __init__(self, kind=NONE, reach=0):
        self.kind = kind
        self.reach = reach


class WeaponAnim:
    XF = 0
    Y = 1
    ANGLE = 2
    TIME = 3
    HIT = 4
    NEXT = 5
    DROP = 6
    grip = 'default'
    states = {
    #           x*f y   angle  time effect next
    'default': [25, 32, 0,      12, 0,                  []],
    'thrust':  [15, 32, 105,    8,  WeaponEffect(1,20), ['thrust2']],
    'thrust2': [45, 32, 90,     4,  0,                  ['default']],
    'chop':    [35, 32, 100,    2,  WeaponEffect(1,10), ['chop2']],
    'chop2':   [15, 32, 190,    2,  0,                  ['default']],
    'fire':    [35, 32, 100,    2,  WeaponEffect(3),    ['fire2']],
    'fire2':   [15, 32, 190,    2,  0,                  ['default']],
    'force':   [35, 32, 100,    2,  WeaponEffect(4),    ['force2']],
    'force2':  [15, 32, 190,    2,  0,                  ['default']],
    'ice':     [35, 32, 100,    2,  WeaponEffect(5),    ['ice2']],
    'ice2':    [15, 32, 190,    2,  0,                  ['default']],
    'change':  [0, 22,  220,    8,  WeaponEffect(2),    []],
    'drop':    [0, 0,   360+90, 8,  WeaponEffect(6),    ['default']],
    'axe':     [35, 32, -60,    6,  0,                  ['axe2']],
    'axe2':    [15, 32, 100,    4,  WeaponEffect(1,10), ['axe3']],
    'axe3':    [15, 32, 220,    4,  0,                  ['default']],

    'staff_default': [25, 12, 0,      12, 0,                  []],
    'staff_thrust':  [15, 32, 105,    8,  WeaponEffect(1,20), ['staff_thrust2']],
    'staff_thrust2': [45, 32, 90,     2,  0,                  ['staff_default']],
    'staff_chop':    [35, 24, 100,    2,  WeaponEffect(1,10), ['staff_chop2']],
    'staff_chop2':   [15, 32, 190,    2,  0,                  ['default']],
    }
    def __init__(self):
        self.src = 'default'
        self.tgt = 'default'
        self.time_left = 0
        self.time_total = 0
        self.state = WeaponAnim.states['default'][:]

    def prn(self):
        print("WA: src=%s tgt=%s t=(%s/%s) s=%s" % (
                self.src, self.tgt,
                self.time_left, self.time_total,
                ",".join(str(s) for s in self.state)))
    def draw(self, m):
        if m.right_hand is None:
            return
        m.right_hand.draw(
            sx=m.x + self.state[self.XF] * m.facing,
            sy=m.y + self.state[self.Y],
            angle=self.state[self.ANGLE] * m.facing)

    def update_grip(self, m):
        if m.right_hand is None:
            return
        self.state = WeaponAnim.states[m.right_hand.itemtype.grip][:]

    def update(self, m):
        if self.time_left == 0:
            return
        self.time_left -= 1
        x = 1.0 * self.time_left / self.time_total

        for i in [self.XF, self.Y, self.ANGLE]:
            self.state[i] = (WeaponAnim.states[self.src][i] * x +
                             WeaponAnim.states[self.tgt][i] * (1.0 - x))
        if self.time_left == 0:
            effect = WeaponAnim.states[self.tgt][self.HIT]
            if effect and effect.kind in (3,4,5):
                d = {3:'fire', 4:'force', 5:'ice'}
                pt = ProjectileType.get(d[effect.kind])
                p = Projectile(pt)
                rhr = 0
                if m.right_hand:
                    rhr = m.right_hand.itemtype.reach
                p.x = m.x + (32 + rhr) * m.facing
                p.y = m.y + 32
                p.vx = m.facing * pt.speed
                p.vy = 0
                p.ttl = pt.ttl
                #print 'cast', d[effect.kind]
                game().level.projectiles.append(p)

            if effect and effect.kind == 2:
                if m.inventory:
                    new_weapon = m.inventory.pop() if m.inventory else None
                    old_weapon = m.right_hand
                    if new_weapon:
                        m.right_hand = new_weapon
                        if old_weapon:
                            m.inventory.insert(0, old_weapon)


            if effect and effect.kind == 6:
                new_weapon = m.inventory.pop() if m.inventory else None
                old_weapon = m.right_hand
                if old_weapon:
                    game().level.items.append(old_weapon)
                    old_weapon.x = m.x
                    old_weapon.y = m.y
                m.right_hand = new_weapon

            if effect and effect.kind == 1:
                for mm in game().enum_monsters():
                    if mm is m: continue
                    if mm.nodam: continue
                    hit = False
                    ydist = 32
                    rhr = 0
                    hand_offset = 22
                    belly_offset = 18
                    dam = 5
                    if m.right_hand:
                        rhr = m.right_hand.itemtype.reach
                        dam = m.right_hand.itemtype.damage
                    xdist = hand_offset + belly_offset + rhr + effect.reach
                    #print 'xdist=', xdist, hand_offset, rhr, effect.reach
                    if m.y - ydist <= mm.y <= m.y+ydist:
                        if m.facing == 1:
                            if m.x <= mm.x <= m.x + xdist:
                                hit = True
                        else:
                            if m.x - xdist <= mm.x <= m.x:
                                hit = True
                    if hit:
                        mm.vy += 5
                        mm.vx += m.facing * 15
                        damage_monster(mm, dam)


            self.src = self.tgt
            if WeaponAnim.states[self.tgt][self.NEXT]:
                self.tgt = random.choice(WeaponAnim.states[self.tgt][self.NEXT])
                self.time_left = WeaponAnim.states[self.tgt][self.TIME]
                self.time_total = WeaponAnim.states[self.tgt][self.TIME]

    def start_attack1(self, monster, tgt):
        if self.time_left != 0:
            # can't attack if previous attack not finished
            return

        self.tgt = tgt
        self.time_left = WeaponAnim.states[self.tgt][self.TIME]
        self.time_total = WeaponAnim.states[self.tgt][self.TIME]


class ProjectileType:
    alltypes = {}
    def __init__(self, name, fpath, damage=10, reach=10, speed=5, ttl=200):
        if fpath:
            self.image = pyglet.image.load(data.filepath(fpath))
            self.image.anchor_x = 32
            self.image.anchor_y = 32
        else:
            self.image = None
        ProjectileType.alltypes[name]=self
        self.name = name
        self.damage = damage
        self.reach = reach
        self.ttl = ttl
        self.speed = speed

    def draw(self, sx, sy):
        if self.image is None:
            return
        s = pyglet.sprite.Sprite(self.image, x=sx, y=sy)
        s.draw()
    @classmethod
    def get(cls, name):
        result = cls.alltypes.get(name)
        if not result:
            print(name, cls.alltypes)
        return result


class Projectile:
    def __init__(self, ptype, x=0, y=0, vx=0, vy=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ptype = ptype
        self.ttl = 100
    def draw(self):
        self.ptype.draw(self.x, self.y)


def damage_monster(m, amount):
    if m.nodam: return
    m.hp -= amount
    if m.hp <= 0:
        if m.name.startswith('goblin'):
            Stats.goblins += 1
        if m.name.startswith('orc'):
            Stats.orcs += 1
        if m.name.startswith('troll'):
            Stats.trolls += 1
        if m.name.startswith('dragon'):
            Stats.dragons += 1
        if m.name.startswith('sack'):
            Stats.sacks += 1

        if m is game().player:
            return
        weapon = m.right_hand
        m.right_hand = None
        if weapon:
            game().level.items.append(weapon)
            weapon.x = m.x
            weapon.y = m.y
        for i in m.inventory:
            game().level.items.append(i)
            i.x = m.x
            i.y = m.y
        m.inventory = []


def init_projectiles():
    fire = ProjectileType('fire', 'pics/fire.png', damage=10, ttl=20, speed=18)
    ice = ProjectileType('ice', 'pics/ice.png', damage=20, ttl=300, speed=3)
    force = ProjectileType('force', 'pics/force.png', damage=30, ttl=20, speed=10)
