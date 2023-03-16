#!/usr/bin/env python
# coding: utf-8
import json
import random

import pyglet

import gamelib.common
from gamelib import data
from gamelib.common import xyrange, game, AIR, LADDER, SOLID, PLATFORM, MAGMA
from gamelib.item import Item, ItemType
from gamelib.monster import Monster


class Place:
    NONE = 0
    TRAVEL = 1
    CHAT = 2
    LABEL = 3
    ENTRY = 4
    kind = 0
    label = ''
    value = ''
    entry = '' # entry name for changing levels
    item = ''
    responce = ''


class Level:
    def __init__(self, tw, th):
        self.tiles = [Tile('air','') for i in range(tw*th)]
        self.tw=tw
        self.th=th
        self.monsters=[]
        self.items=[]
        self.b = None
        self.bs = []
        self.sky = None
        self.places = []
        self.projectiles = []

    def tile(self,tx,ty):
        if 0 <= tx < self.tw and 0 <= ty < self.th:
            return self.tiles[tx+self.tw*ty]
        return None

    def set_tile(self,tx,ty,t):
        if 0 <= tx < self.tw and 0 <= ty < self.th:
            self.tiles[tx+self.tw*ty] = t
    def get_tx_ty_tile_at(self,mx,my):
        tx = mx // 64
        ty = my // 64
        t = self.tile(tx, ty)
        return (tx, ty, t)

    def draw(self):
        if self.b is not None and gamelib.common.frameno > 1:
            self.b.draw()
            return

        self.b = pyglet.graphics.Batch()
        self.bs = []
        for tx, ty in xyrange(self.tw, self.th):
            t = self.tile(tx,ty)
            self.bs.append(t.draw(sx=tx*64, sy=ty*64, batch=self.b))
        self.b.draw()

    def enum_monsters(self):
        yield game().player
        for i in self.monsters:
            yield i


class Tile:
    alltiles = {}
    def __init__(self, name, fpath):
        if fpath:
            self.image = pyglet.image.load(data.filepath(fpath))
        else:
            self.image = None
        Tile.alltiles[name]=self
        self.solid = AIR
    def draw(self, sx, sy, batch=None):
        if self.image is None:
            return
        s = pyglet.sprite.Sprite(self.image, x=sx, y=sy, batch=batch)
        if batch is None:
            s.draw()
        return s
    @classmethod
    def get(cls, name):
        return cls.alltiles.get(name)


allmaps = {}


def getmap(name):
    level = allmaps.get(name)
    if level:
        return level
    level = loadmap(name)
    allmaps[name]=level
    return level


def loadmap(fn):
    js= json.load(open(fn))
    w=int(js['width'])
    h=int(js['height'])
    #print 'wh:', w, h
    level = Level(w, h)

    dat = js['layers'][0]['data']
    tsf = json.load(open('data/tileset.json'))
    ts = tsf['tiles'] #js['tilesets'][0]['tiles']
    tp = tsf['tileproperties'] #js['tilesets'][0]['tileproperties']

    lp = js['layers'][0].get("properties")# or {}
    sky_file = lp.get('sky')
    if sky_file:
        level.sky = pyglet.sprite.Sprite(pyglet.image.load(data.filepath(sky_file)), x=0, y=0)
    else:
        assert 'no sky file'
        level.sky = pyglet.sprite.Sprite(pyglet.image.load(data.filepath('sky/clouds.png')), x=0, y=0)
    i=0
    for n, tt in list(ts.items()):
        #print tt, tp[n]
        if i > 1000:
            t = Tile(tt['image'], '')
        else:
            t = Tile(tt['image'], tt['image'])

        solid = tp[n].get('solid', 'stairs')
        s = LADDER
        if solid == 'air': s = AIR
        if solid == 'solid': s = SOLID
        if solid == 'stairs': s = LADDER
        if solid == 'ladder': s = LADDER
        if solid == 'platform': s = PLATFORM
        if solid == 'roof': s = PLATFORM
        if solid == 'magma': s = MAGMA
        t.solid = s
        i+=1
    i=0
    for ny,x in xyrange(h, w):
        y = h-1-ny
        try:
            s=dat[i]
            if s == 0:
                pass
            else:
                level.set_tile(x, y, Tile.get(ts[str(s - 1)]['image']))
            #print dat[i],
        except:
            pass
        i += 1
    object_layer = js['layers'][1]['objects']
    for o in object_layer:
        #print "o=", o
        if o['type'] == 'monster':
            props = o.get('properties') or {}
            inv = props.get('inv') or None
            create_monster(level, o['name'],
                           int(o['x']), h*64-int(o['y']),
                           inv)
        if o['type'] == 'travel':
            p = Place()
            p.x = int(o['x'])
            p.y = h*64-int(o['y'])
            p.kind = p.TRAVEL
            p.label = o['name']
            p.value = o['properties']['file']
            p.entry = o['properties'].get('entry') or 'entry'
            level.places.append(p)
        if o['type'] == 'label':
            p = Place()
            p.x = int(o['x'])
            p.y = h*64-int(o['y'])
            p.kind = p.LABEL
            p.label = o['value']
            level.places.append(p)

        if o['type'] == 'chat':
            p = Place()
            p.x = int(o['x'])
            p.y = h*64-int(o['y'])
            p.kind = p.CHAT
            p.label = o['name']

            prp = o.get('properties') or {}
            race = prp.get('tgt')
            reject = False
            if race == 'orc' and game().player.race == 'goblin':
                reject = True
            if race == 'goblin' and game().player.race == 'orc':
                reject = True

            p.item = prp.get('item')
            if not reject:
                level.places.append(p)

        if o['type'] == 'entry':
            p = Place()
            p.x = int(o['x'])
            p.y = h*64-int(o['y'])
            p.kind = p.ENTRY
            p.value = o['name']
            p.entry = o['name']
            level.places.append(p)

    return level


def make_levelA():
    w=32
    h=32
    grass = Tile('grass', 'pics/grass.png')
    stone = Tile('stone', 'pics/wall.png')
    air = Tile('air', '')
    level = Level(w, h)

    for x, y in xyrange(w, h):
        level.set_tile(x,y, grass)

    def add_platorm(px,py,pl):
        for l in range(pl):
            level.set_tile(px+l,py, stone)

    add_platorm(0,1,100)
    add_platorm(5,6,8)
    add_platorm(2,8,3)

    for platform in range(20):
        px=random.randint(1,w-1)
        py=random.randint(1,h-1)
        pl=random.randint(2,5)
        add_platorm(px,py,pl)
    return level


def create_monster(level, name, x, y, inv=None):
    #print 'create monster', name, x, y, inv
    monsters= {
    'goblin':         ('pics/goblin1.png', 7, 30, 'staff'),
    #'goblin_citizen': ('pics/goblin1.png', 5, 30, ''),
    'goblin_guard':   ('pics/goblin1.png', 6, 40, 'spear polearm axe'),
    'goblin_king':    ('pics/goblin1.png', 4, 150, 'force_wand'),
    'goblin_rogue':   ('pics/goblin1.png', 7, 30, 'sword spear'),
    'goblin_shaman':  ('pics/goblin1.png', 2, 120, 'ice_wand'),
    'goblin_necromancer': ('pics/goblin1.png', 9, 30, 'dagger fire_wand'),
    'orc':             ('pics/orc1.png', 5, 30, ''),
    # 'orc_citizen':     ('pics/orc1.png', 5, 30, ''),
    'orc_guard':       ('pics/orc1.png', 5, 100, 'sword polearm axe'),
    'orc_king':        ('pics/orc1.png', 4, 150, 'force_wand'),
    'orc_bandit':      ('pics/orc1.png', 5, 50, 'sword dagger'),
    'orc_shaman':      ('pics/orc1.png', 5, 50, 'force_wand'),
    'orc_necromancer': ('pics/orc1.png', 6, 40, 'staff fire_wand'),
    #'troll':             ('pics/troll1.png', 5, 30, ''),
    #'troll_citizen':     ('pics/troll1.png', 5, 30, ''),
    'troll_guard':       ('pics/troll1.png', 5, 50, 'spear'),
    'troll_king':        ('pics/troll1.png', 3, 200, 'force_wand'),
    'troll_shaman':      ('pics/troll1.png', 5, 50, 'fire_wand'),
    'troll_necromancer': ('pics/troll1.png', 5, 50, 'fire_wand'),
    'dragon':            ('pics/dragon1.png', 5, 300, 'fire_wand'),
    'sack':              ('pics/sack.png', 0, 50, 'spear potion potion potion'),
    'barrel':            ('pics/barrel.png', 0, 500, ''),
    }

    mm = monsters[name]
    pic = mm[0]
    m = Monster(pic)
    m.x = x
    m.y = y
    m.name = name

    friends = 'citizen guard trader king shaman'.split()
    if game().player.race == 'dragon':
        friends = []

    for f in friends:
        if name.endswith(f):
            m.friendly = True
            m.nodam = True
    if game().player.race == 'goblin':
        if name.startswith('orc'):
            m.friendly = False
            m.nodam = False
    if game().player.race == 'orc':
        if name.startswith('goblin'):
            m.friendly = False
            m.nodam = False

    if inv is None:
        inv = mm[3]

    if name.startswith('sack') or name.startswith('barrel'):
        m.friendly = True
        m.nodam = False
        give_item(m, inv)
        inv = ''

    give_weapon(m, inv)
    m.speed = mm[1]
    m.hp = mm[2]
    m.facing = -1

    level.monsters.append(m)
    return m


def give_weapon(m, desc):
    if not desc:
        return
    s = random.choice(desc.split())
    it = ItemType.alltypes.get(s) or ItemType['dagger']
    m.right_hand = Item(it)
    m.weapon_anim.update_grip(m)


def give_item(m, desc):
    #print 'give item', desc
    if not desc:
        return
    s = random.choice(desc.split())
    it = ItemType.alltypes.get(s) or ItemType['dagger']
    m.inventory.append(Item(it))
