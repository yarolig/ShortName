import data
import pyglet
from pyglet.window import key, mouse
import random
import json
from pyglet.gl import *


keys = key.KeyStateHandler()

def xyrange(w,h):
    for x in xrange(w):
        for y in xrange(h):
            yield x, y

frameno = 0
# coord systems:
# t - tile (1 = 1 tile)
# s - screen (1 = 1 pixel, origin is bottom left corner of window)
# m - map (1 = 1 pixel, origin is bottom left corner of map)

AIR = 0
PLATFORM = 1
LADDER = 2
SOLID = 3
MAGMA = 4

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
            print name, cls.alltypes
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

class Item:
    def __init__(self, itemtype):
        self.x = 0
        self.y = 0
        self.itemtype = itemtype

    def draw(self, sx, sy, angle, batch=None):
        self.itemtype.draw(sx, sy, angle, batch)

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
        self.tiles = [Tile('air','') for i in xrange(tw*th)]
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
        tx = mx / 64
        ty = my / 64
        t = self.tile(tx, ty)
        return (tx, ty, t)

    def draw(self):
        if self.b is not None and frameno > 1:
            self.b.draw()
            return

        self.b = pyglet.graphics.Batch()
        self.bs = []
        for tx, ty in xyrange(self.tw, self.th):
            t = self.tile(tx,ty)
            self.bs.append(t.draw(sx=tx*64, sy=ty*64, batch=self.b))
        self.b.draw()

    def enum_monsters(self):
        yield game.player
        for i in self.monsters:
            yield i

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
    level = Level(w,h)

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
    for n, tt in ts.items():
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
    for ny,x in xyrange(h,w):
        y = h-1-ny
        try:
            s=dat[i]
            if s == 0:
                pass
            else:
                level.set_tile(x,y, Tile.get(ts[str(s-1)]['image']))
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
            if race == 'orc' and game.player.race == 'goblin':
                reject = True
            if race == 'goblin' and game.player.race == 'orc':
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

class MonsterImage:
    def __init__(self, image_name='pics/orc%s.png'):
        pass


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
    }
    def __init__(self):
        self.src = 'default'
        self.tgt = 'default'
        self.time_left = 0
        self.time_total = 0
        self.state = WeaponAnim.states['default'][:]

    def prn(self):
        print "WA: src=%s tgt=%s t=(%s/%s) s=%s" % (
                self.src, self.tgt,
                self.time_left, self.time_total,
                ",".join(str(s) for s in self.state))
    def draw(self, m):
        if m.right_hand is None:
            return
        m.right_hand.draw(
            sx=m.x + self.state[self.XF] * m.facing,
            sy=m.y + self.state[self.Y],
            angle=self.state[self.ANGLE] * m.facing)

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
                game.level.projectiles.append(p)

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
                    game.level.items.append(old_weapon)
                    old_weapon.x = m.x
                    old_weapon.y = m.y
                m.right_hand = new_weapon

            if effect and effect.kind == 1:
                for mm in game.level.enum_monsters():
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
            s.position
        s.draw()
        self.weapon_anim.draw(self)

class Game:
    level = Level(2,2)
    keys = {}
    player = Monster('pics/orc1.png')

window = pyglet.window.Window()
game = Game()
window.push_handlers(keys)
font_name = 'Times New Roman'
label = pyglet.text.Label('100 hp',
                          font_name=font_name,
                          font_size=36,
                          x=10, y=10)
roadsign = pyglet.text.Label('To forest',
                        font_name=font_name,
                        font_size=26,
                        x=10, y=window.height - 50)

roadsign_text = ''
mode = 'start'
end_text = 'You are defeated.'
end_text2 = ''
end_bottom_text = 'Press Space to continue.'

class Stats:
    orcs = 0
    goblins = 0
    trolls = 0
    dragons = 0
    sacks = 0
    restarts = 0

hintsign = pyglet.text.Label('Press E to win',
                        font_name=font_name,
                        font_size=16,
                        x=10, y=window.height - 120)
hintsign_text = ''

startsky = None
load_mode_action = lambda: True
load_mode_text = 'Loading...'

def make_levelA():
    w=32
    h=32
    grass = Tile('grass','pics/grass.png')
    stone = Tile('stone','pics/wall.png')
    air = Tile('air', '')
    level = Level(w, h)

    for x, y in xyrange(w, h):
        level.set_tile(x,y, grass)

    def add_platorm(px,py,pl):
        for l in xrange(pl):
            level.set_tile(px+l,py, stone)

    add_platorm(0,1,100)
    add_platorm(5,6,8)
    add_platorm(2,8,3)

    for platform in xrange(20):
        px=random.randint(1,w-1)
        py=random.randint(1,h-1)
        pl=random.randint(2,5)
        add_platorm(px,py,pl)
    return level


def process_input():
    game.player.reset_input()
    #print keys
    if keys[key.LEFT] or keys[key.A]:
        game.player.in_a = True
    if keys[key.RIGHT] or keys[key.D]:
        game.player.in_d = True
    if keys[key.DOWN] or keys[key.S]:
        game.player.in_s = True
    if keys[key.UP] or keys[key.W]:
        game.player.in_w = True

    if keys[key.SPACE]:
        game.player.in_jump = True
    if keys[key.J] or keys[key.V]:
        game.player.in_thrust = True
    if keys[key.K] or keys[key.F]:
        game.player.in_swing = True
    if keys[key.L]:
        game.player.in_kick = True
    if keys[key.X]:
         game.player.in_change = True
    if keys[key.E]:
        game.player.in_use = True
    if keys[key.G]:
        game.player.in_drop = True

    if keys[key.F1]:
        global mode
        mode = 'controls'

last_level = ''
last_entry = ''
def change_level(name, entryname=None):
    #print 'change level to', name, entryname
    if not entryname:
        entryname = 'entry'

    global last_level
    global last_entry
    last_level = name
    last_entry = entryname
    level = getmap(name)
    game.level = level
    game.player.hp = max(game.player.hp, game.player.maxhp)
    for o in level.places:
        if o.kind == Place.ENTRY:
            #print 'trying entries "%s" "%s"' % (o.value, entryname)
            if o.value == entryname:
                game.player.x = o.x
                game.player.y = o.y
                break
    global mode
    mode = 'load'
    global load_mode_text
    load_mode_text = 'Loading...'
    global load_mode_action
    def a():
        global mode
        mode = 'game'
    load_mode_action = a



def phym(monster):
    if True:
        m = monster
    else:
        m = Monster() # for code completion
    (tx, ty, t) = game.level.get_tx_ty_tile_at(m.x, m.y)
    (belowtx, belowty, belowt) = game.level.get_tx_ty_tile_at(m.x, m.y - 12)

    global roadsign_text
    global hintsign_text
    in_magma = False
    if t and t.solid in (MAGMA,):
        in_magma = True
    if belowt and belowt.solid in (MAGMA,):
        in_magma = True

    if in_magma:
        m.hp -= 3
    if m.hp <= 0:
        m.y -= 20
        return

    if m is game.player:
        for p in game.level.places:
            if p.kind in (Place.LABEL,):
                if (p.x - m.x) ** 2 + (p.y - m.y) ** 2 < 48 ** 2:
                    roadsign_text = p.label
            if p.kind in (Place.TRAVEL,):
                if (p.x - m.x) ** 2 + (p.y - m.y) ** 2 < 48 ** 2:
                    roadsign_text = "%s"  % p.label
                    hintsign_text = "Press E to travel to %s (%s)" % (p.label, p.entry)
            if p.kind in (Place.CHAT,):
                if (p.x - m.x) ** 2 + (p.y - m.y) ** 2 < 48 ** 2:
                    hintsign_text = p.label
                    if p.item:
                        if m.right_hand:
                            if m.right_hand.itemtype.name == p.item:
                                roadsign_text = 'Press E to win!'
                                if m.in_use:
                                    global mode
                                    mode = 'end'
                                    global end_text
                                    end_text = 'Victory!'

                                    global end_text2
                                    end_text2 = p.responce

                                    global startsky
                                    skyname = ''

                                    if p.item == 'axe':
                                        skyname = 'sky/forest.png'
                                    else:
                                        skyname = 'sky/tower.png'
                                    startsky = pyglet.sprite.Sprite(pyglet.image.load(data.filepath(skyname)), x=0, y=0)

                                    global end_bottom_text
                                    end_bottom_text = 'Press Esc to exit.'
                                    return

    for i in game.level.items:
        if (i.x - m.x) ** 2 + (i.y - m.y) ** 2 < 48 ** 2:
            hintsign_text = "Press E to pick up %s" % (i.itemtype.name.replace('_', ' '))
    if m.in_use:
        # pickup items, chat, change level
        for p in game.level.places:
            if (p.x - m.x) ** 2 + (p.y - m.y) ** 2 < 48 ** 2:
                pass
            else:
                continue
            if p.kind == Place.TRAVEL:
                #print 'change level!!', p.value, p.entry
                if p.value:
                    change_level(p.value, p.entry)
                    return
        if m.weapon_anim.time_left == 0:
            for i in game.level.items:
                if (i.x - m.x) ** 2 + (i.y - m.y) ** 2 < 48 ** 2:
                    if i.itemtype.health_potion:
                        m.maxhp += 10
                        m.hp = min(m.maxhp, m.hp + 50)
                    else:
                        new_weapon = i
                        old_weapon = m.right_hand
                        m.inventory.insert(0, old_weapon)
                        m.right_hand = new_weapon
                    game.level.items.remove(i)
                    break

    have_ground = False
    on_stairs = False

    if t and t.solid in (LADDER,):
        on_stairs = True
        m.refill_jump()
    if belowt and belowt.solid in (LADDER,):
        on_stairs = True
        m.refill_jump()
    #(1024 + m.y) % 64 < 16 and
    if belowt and belowt.solid in (LADDER, PLATFORM, SOLID):
        m.refill_jump()
        have_ground = True


    if m.in_s:
        if on_stairs:
            m.vy = -m.jump_speed
        # jump down
        elif m.in_jump and belowt and belowt.solid in (LADDER, PLATFORM):
            m.vy = -m.jump_speed
        else:
            m.jump_left = 0
            m.vy = max(m.vy, 0) if have_ground else max(-15, m.vy - 3)
    else:
        if m.in_w and on_stairs:
            m.vy = m.jump_speed
        # jump up
        elif m.in_jump and m.jump_left > 0:
            m.vy = m.jump_speed
            m.jump_left -= 1
        else:
            m.jump_left = 0
            m.vy = max(m.vy, 0) if have_ground else max(-15, m.vy - 3)

    if m.in_a:
        if m.weapon_anim.time_left == 0:
            m.facing = -1
        m.vx = max(m.vx - 2, -m.speed)
    elif m.in_d:
        if m.weapon_anim.time_left == 0:
            m.facing = 1
        m.vx = min(m.vx + 2, m.speed)
    else:
        if m.vx > 2:
            m.vx = m.vx - 2
        elif m.vx < - 2:
            m.vx = m.vx + 2
        else:
            m.vx = 0

    m.weapon_anim.update(m)
    if m.in_swing:
        if m.right_hand:
            m.weapon_anim.start_attack1(m, m.right_hand.itemtype.attack1)

    if m.in_thrust:
        if m.right_hand:
            m.weapon_anim.start_attack1(m, m.right_hand.itemtype.attack2)

    if m.in_drop:
        if m.right_hand:
            m.weapon_anim.start_attack1(m, 'drop')

    if m.in_change:
        m.weapon_anim.start_attack1(m, 'change')

    (newx, newy, newt) = game.level.get_tx_ty_tile_at(m.x + m.vx,
                                                      m.y + m.vy)
    if newt:
        #print 'newt.solid', newt.solid, 'hg=', have_ground
        if newt.solid in (MAGMA, AIR, PLATFORM, LADDER):
            m.x = m.x + m.vx
            m.y = m.y + m.vy
            return

    (newx, newy, newt) = game.level.get_tx_ty_tile_at(m.x,
                                                      m.y + m.vy)
    if newt:
        #print 'newt.solid', newt.solid, 'hg=', have_ground
        if newt.solid in (MAGMA, AIR, PLATFORM, LADDER):
            m.x = m.x
            m.vx = 0
            m.y = m.y + m.vy
            return
        m.vy /= 2


def aim(m):
    m.reset_input()
    if m.friendly:
        return
    player_sdist_sq = (game.player.x - m.x) ** 2 + (game.player.y - m.y) ** 2

    if player_sdist_sq > (64 * 5) ** 2:
        return

    closing_dist = 100
    if m.right_hand:
        if m.right_hand.itemtype.name == 'dagger':
            closing_dist = 10
        if m.right_hand.itemtype.name == 'fire_wand':
            closing_dist = 200
        if m.right_hand.itemtype.name == 'force_wand':
            closing_dist = 300

    good_facing = True
    if game.player.x * m.facing < m.x * m.facing:
        good_facing = False

    if game.player.x + closing_dist < m.x:
        m.in_a = True

    if game.player.x - closing_dist > m.x:
        m.in_d = True

    if good_facing and player_sdist_sq < (closing_dist * 2) ** 2:
        m.in_thrust = True
    if not good_facing:
        if m.facing == 1:
            m.in_a = True
        else:
            m.in_d = True


def phyp(projectile):
    (tx, ty, t) = game.level.get_tx_ty_tile_at(projectile.x, projectile.y)
    projectile.ttl -= 1
    if t and t.solid in (SOLID, MAGMA):
        projectile.ttl = 0
    if projectile.ttl <= 0:
        return
    projectile.x += projectile.vx
    projectile.y += projectile.vy

    for mm in game.level.enum_monsters():
        if mm.nodam: continue
        hit = False
        ydist = 32
        xdist = abs(projectile.vx) * 2
        facing = 1 if projectile.vx > 0 else -1
        if projectile.y - ydist <= mm.y + 32 <= projectile.y+ydist:
            if facing == 1:
                if projectile.x <= mm.x <= projectile.x + xdist:
                    hit = True
            else:
                if projectile.x - xdist <= mm.x <= projectile.x:
                    hit = True
        if hit:
            projectile.ttl = 0
            mm.vy += 5
            mm.vx += facing * 10
            damage_monster(mm, projectile.ptype.damage)


accdt = 0.0
def on_timer(dt):
    global accdt
    accdt += dt
    if accdt > 0.02:
        dt = accdt
        accdt = 0.0
    else:
        return
    global mode
    if mode == 'game':
        return phy(dt)
    if mode == 'start':
        return start_phy()
    if mode == 'end':
        return end_phy()
    if mode == 'controls':
        return controls_phy()

def start_phy():
    global mode
    if keys[key.O]:
        mode = 'game'
        start_game('orc')
    if keys[key.G]:
        mode = 'game'
        start_game('goblin')
    if keys[key.T]:
        mode = 'game'
        start_game('troll')
    if keys[key.F1]:
        game.player.in_use = True

def end_phy():
    global mode
    if keys[key.SPACE]:
        mode = 'game'
        Stats.restarts += 1
        change_level(last_level, last_entry)

def controls_phy():
    global mode
    if keys[key.SPACE]:
        mode = 'game'

dead_time = 0
def phy(dt):
    global roadsign_text
    roadsign_text = ''
    global hintsign_text
    hintsign_text = ''

    process_input()
    phym(game.player)
    for m in game.level.monsters:
        aim(m)
        phym(m)
    for p in game.level.projectiles:
        phyp(p)

    game.level.projectiles = [p for p in game.level.projectiles if p.ttl >0]

    global dead_time
    global mode
    if game.player.hp <= 0:
        dead_time += 1
        if dead_time > 60:
            mode = 'end'
            dead_time = 0

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

        if m is game.player:
            return
        weapon = m.right_hand
        m.right_hand = None
        if weapon:
            game.level.items.append(weapon)
            weapon.x = m.x
            weapon.y = m.y
        for i in m.inventory:
            game.level.items.append(i)
            i.x = m.x
            i.y = m.y
        m.inventory = []

def game_mode_draw():
    global frameno
    frameno += 1
    window.clear()
    game.level.sky.draw()
    glPushMatrix(GL_MODELVIEW)
    glTranslatef(window.width/2-game.player.x,
                 window.height/2-game.player.y,0)
    game.level.draw()
    for m in game.level.monsters:
        if  (abs(m.x - game.player.x) < window.width // 2 + 64 and
             abs(m.y - game.player.y) < window.height // 2 + 64):
            m.draw()
    game.player.draw()
    for p in game.level.projectiles:
        if  (abs(p.x - game.player.x) < window.width // 2 + 64 and
             abs(p.y - game.player.y) < window.height // 2 + 64):
            p.draw()

    for i in game.level.items:
        if  (abs(i.x - game.player.x) < window.width // 2 + 64 and
             abs(i.y - game.player.y) < window.height // 2 + 64):
                i.draw(i.x, i.y, 90)

    glPopMatrix(GL_MODELVIEW)
    label.text = "%d HP, %d fps" % (game.player.hp, pyglet.clock.get_fps())
    label.draw()
    roadsign.text = roadsign_text
    roadsign.draw()
    hintsign.text = hintsign_text
    hintsign.draw()


def init_item_types():
    sword=ItemType('sword', 'pics/sword.png',       10, 47)
    spear=ItemType('spear', 'pics/spear.png',       10, 59)
    polearm=ItemType('polearm', 'pics/polearm.png', 25, 59)
    staff=ItemType('staff', 'pics/staff.png',        5, 60)
    dagger=ItemType('dagger', 'pics/dagger.png',    30, 16)

    fire_wand=ItemType('fire_wand', 'pics/fire_wand.png', 5, 45)
    fire_wand.attack2 = 'fire'

    ice_wand=ItemType('ice_wand', 'pics/ice_wand.png', 5, 45)
    ice_wand.attack2 = 'ice'

    force_wand=ItemType('force_wand', 'pics/force_wand.png', 15, 60)
    force_wand.attack2 = 'force'

    axe=ItemType('axe', 'pics/axe.png',             50, 47)
    axe.attack1 = 'axe'
    axe.attack2 = 'axe'


    potion = ItemType('potion', 'pics/potion.png',  30, 47)
    potion.health_potion = True

def init_projectiles():
    fire = ProjectileType('fire', 'pics/fire.png',   damage=10, ttl=20,speed=18)
    ice = ProjectileType('ice', 'pics/ice.png',      damage=20, ttl=300,speed=3)
    force = ProjectileType('force', 'pics/force.png',damage=30, ttl=20,speed=10)

def give_weapon(m, desc):
    if not desc:
        return
    s = random.choice(desc.split())
    it = ItemType.alltypes.get(s) or ItemType['dagger']
    m.right_hand = Item(it)

def give_item(m, desc):
    #print 'give item', desc
    if not desc:
        return
    s = random.choice(desc.split())
    it = ItemType.alltypes.get(s) or ItemType['dagger']
    m.inventory.append(Item(it))

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
    'orc_guard':       ('pics/orc1.png', 5, 100, 'spear polearm axe'),
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
    for f in friends:
        if name.endswith(f):
            m.friendly = True
            m.nodam = True
    if game.player.race == 'goblin':
        if name.startswith('orc'):
            m.friendly = False
            m.nodam = False
    if game.player.race == 'orc':
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

def start_mode_draw():
    window.clear()
    startsky.draw()

    class T:
        pos = 150
        dpos = 50
    t = T()
    def d(text):
        pyglet.text.Label(text, font_name=font_name,
                          font_size=18, x=30, y=window.height - t.pos).draw()
        t.pos += t.dpos
    for s in ['Press O to start as an Orc',
              'Press G to start as a Goblin',
              'Press F1 to view controls',
              'Press Esc to exit']:
        d(s)

def end_mode_draw():
    window.clear()
    startsky.draw()
    pyglet.text.Label(end_text, font_name=font_name,
                      font_size=28, x=window.width //2, y=window.height - 50, anchor_x='center').draw()
    pyglet.text.Label(end_bottom_text, font_name=font_name,
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
              'restarts: %d' % Stats.restarts,]:
      d(s)


def controls_mode_draw():
    window.clear()
    startsky.draw()
    class T:
        pos = 120
        dpos = 30
    t = T()
    def d(text):
        pyglet.text.Label(text, font_name=font_name,
                          font_size=18, x=30, y=window.height - t.pos).draw()
        t.pos += t.dpos
    for s in ['WSAD, Arrows - move',
              'F,J - thrust weapon',
              'V,K - swing weapon',
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


def load_mode_draw():
    window.clear()
    startsky.draw()
    pyglet.text.Label(load_mode_text, font_name=font_name,
                      font_size=18, x=30, y=window.height // 2).draw()

    load_mode_action()

@window.event
def on_draw():
    global mode
    if mode == 'game':
        game_mode_draw()
    elif mode == 'start':
        start_mode_draw()
    elif mode == 'controls':
        controls_mode_draw()
    elif mode == 'end':
        end_mode_draw()
    elif mode == 'load':
        load_mode_draw()

def start_game(race='orc'):
    game.level = getmap('data/map1.json')
    if race == 'orc':
        game.player = Monster('pics/orc1.png')
        game.player.race = race
        game.player.right_hand = Item(ItemType.alltypes['sword'])
        change_level('data/orctown.json', 'startgame')
    elif race == 'goblin':
        game.player = Monster('pics/goblin1.png')
        game.player.race = race
        game.player.right_hand = Item(ItemType.alltypes['dagger'])
        change_level('data/goblintown.json', 'startgame')
    elif race == 'troll':
        game.player = Monster('pics/troll1.png')
        game.player.race = race
        game.player.right_hand = Item(ItemType.alltypes['staff'])
        change_level('data/swamp.json', 'startgame')

def main():
    pyglet.clock.schedule_interval(on_timer, 1/60.0)
    pyglet.clock.set_fps_limit(60)
    init_item_types()
    init_projectiles()
    random_sky=random.choice(['sky/clouds.png', 'sky/forest.png'])
    global startsky
    startsky = pyglet.sprite.Sprite(pyglet.image.load(data.filepath(random_sky)), x=0, y=0)
    pyglet.app.run()


