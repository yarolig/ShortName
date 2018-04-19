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

class Item:
    def __init__(self, itemtype):
        self.x = 0
        self.y = 0
        self.itemtype = itemtype

    def draw(self, sx, sy, angle, batch=None):
        self.itemtype.draw(sx, sy, angle, batch)

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
    print 'wh:', w, h
    level = Level(w,h)

    dat = js['layers'][0]['data']
    tsf = json.load(open('data/tileset.json'))
    ts = tsf['tiles'] #js['tilesets'][0]['tiles']
    tp = tsf['tileproperties'] #js['tilesets'][0]['tileproperties']

    lp = js['layers'][0].get("properties")# or {}
    sky_file = lp.get('sky')
    if sky_file:
        level.sky = pyglet.sprite.Sprite(pyglet.image.load(data.filepath(sky_file)), x=0, y=0)
    #else:
    #    level.sky = pyglet.sprite.Sprite(pyglet.image.load(data.filepath('sky/clouds.png')), x=0, y=0)
    i=0
    for n, tt in ts.items():
        print tt, tp[n]
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
        print "o=", o
        if o['type'] == 'monster':
            create_monster(level, o['name'],
                           int(o['x']), h*64-int(o['y']))
    return level

class MonsterImage:
    def __init__(self, image_name='pics/orc%s.png'):
        pass


class WeaponEffect:
    NONE = 0
    HIT = 1
    CHANGE_WEAPON = 2
    FIREBALL = 3
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
    states = {
    #           x*f y   angle  time effect next
    'default': [25, 32, 0,      12, 0,                  []],
    'thrust':  [15, 32, 105,    8,  WeaponEffect(1,20), ['thrust2']],
    'thrust2': [45, 32, 90,     4,  0,                  ['default']],
    'chop':    [35, 32, 100,    2,  WeaponEffect(1,10), ['chop2']],
    'chop2':   [15, 32, 190,    2,  0,                  ['default']],
    'change':  [0, 22,  220,    8,  WeaponEffect(2),    []],
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
            if effect and effect.kind == 2:
                if m.inventory:
                    new_weapon = m.inventory.pop()
                    old_weapon = m.right_hand
                    m.inventory.insert(0, old_weapon)
                    m.right_hand = new_weapon

            if effect and effect.kind == 1:
                for mm in game.level.enum_monsters():
                    if mm is m: continue
                    #if mm.friendly: continue
                    hit = False
                    ydist = 16
                    rhr = 0
                    hand_offset = 22
                    belly_offset = 18
                    if m.right_hand:
                        rhr = m.right_hand.itemtype.reach
                    xdist = hand_offset + belly_offset + rhr + effect.reach
                    print 'xdist=', xdist, hand_offset, rhr, effect.reach
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
                        damage_monster(mm, 10)


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
        self.hp = 100
        self.maxhp = 100
        self.friendly = False
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
label = pyglet.text.Label('100 hp',
                          font_name='Times New Roman',
                          font_size=36,
                          x=10, y=10)




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
    if keys[key.J]:
        game.player.in_thrust = True
    if keys[key.K]:
        game.player.in_swing = True
    if keys[key.L]:
        game.player.in_kick = True
    if keys[key.X]:
         game.player.in_change = True
    if keys[key.E]:
        game.player.in_use = True
    if keys[key.G]:
        game.player.in_drop = True

def phym(monster):
    if True:
        m = monster
    else:
        m = Monster() # for code completion
    (tx, ty, t) = game.level.get_tx_ty_tile_at(m.x, m.y)
    (belowtx, belowty, belowt) = game.level.get_tx_ty_tile_at(m.x, m.y - 12)

    if m.hp <= 0:
        m.y -= 20
        return

    if m.in_use:
        # pickup items, chat, change level
        pass
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
        m.weapon_anim.start_attack1(m, 'chop')

    if m.in_thrust:
        m.weapon_anim.start_attack1(m, 'thrust')
    if m.in_change:
        m.weapon_anim.start_attack1(m, 'change')

    (newx, newy, newt) = game.level.get_tx_ty_tile_at(m.x + m.vx,
                                                      m.y + m.vy)
    if newt:
        #print 'newt.solid', newt.solid, 'hg=', have_ground
        if newt.solid in (AIR, PLATFORM, LADDER):
            m.x = m.x + m.vx
            m.y = m.y + m.vy
            return

    (newx, newy, newt) = game.level.get_tx_ty_tile_at(m.x,
                                                      m.y + m.vy)
    if newt:
        #print 'newt.solid', newt.solid, 'hg=', have_ground
        if newt.solid in (AIR, PLATFORM, LADDER):
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

def phy(dt):
    process_input()
    phym(game.player)
    for m in game.level.monsters:
        aim(m)
        phym(m)

def damage_monster(m, amount):
    #if m.friendly: return
    m.hp -= amount


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
        m.draw()
    game.player.draw()
    glPopMatrix(GL_MODELVIEW)
    label.text = "%d HP, %d fps" % (game.player.hp, pyglet.clock.get_fps())
    label.draw()


def init_item_types():
    sword=ItemType('sword', 'pics/sword.png', 10, 47)
    spear=ItemType('spear', 'pics/spear.png', 10, 59)
    polearm=ItemType('polearm', 'pics/polearm.png', 10, 59)
    staff=ItemType('staff', 'pics/staff.png', 5, 60)
    dagger=ItemType('dagger', 'pics/dagger.png', 30, 16)

    fire_wand=ItemType('fire_wand', 'pics/fire_wand.png', 5, 45)
    ice_wand=ItemType('ice_wand', 'pics/ice_wand.png', 5, 45)
    axe=ItemType('axe', 'pics/axe.png', 30, 47)

    '''
goblin
goblin_citizen
goblin_guard
goblin_king
goblin_trader
goblin_robber
goblin_shaman
goblin_necromancer

orc
orc_citizen
orc_guard
orc_king
orc_trader
orc_bandit
orc_shaman
orc_necromancer

troll
troll_citizen
troll_guard
troll_king
troll_trader
troll_shaman
troll_necromancer

'''

def give_weapon(m, desc):
    if not desc:
        return
    m.right_hand = Item(ItemType.alltypes[random.choice(desc.split())])

def create_monster(level, name, x, y):
    monsters= {
    'goblin':         ('pics/goblin1.png', 5, 30, 'staff'),
    'goblin_citizen': ('pics/goblin1.png', 5, 30, ''),
    'goblin_guard':   ('pics/goblin1.png', 5, 30, 'spear polearm'),
    'goblin_king':    ('pics/goblin1.png', 5, 30, ''),
    'goblin_trader':  ('pics/goblin1.png', 5, 30, ''),
    'goblin_robber':  ('pics/goblin1.png', 5, 30, 'sword'),
    'goblin_shaman':  ('pics/goblin1.png', 5, 30, 'staff'),
    'goblin_necromancer': ('pics/goblin1.png', 5, 30, 'dagger'),
    'orc':             ('pics/orc1.png', 5, 30, ''),
    'orc_citizen':     ('pics/orc1.png', 5, 30, ''),
    'orc_guard':       ('pics/orc1.png', 5, 30, 'spear polearm'),
    'orc_king':        ('pics/orc1.png', 5, 30, ''),
    'orc_trader':      ('pics/orc1.png', 5, 30, ''),
    'orc_bandit':      ('pics/orc1.png', 5, 30, ''),
    'orc_shaman':      ('pics/orc1.png', 5, 30, ''),
    'orc_necromancer': ('pics/orc1.png', 5, 30, ''),
    'troll':             ('pics/troll1.png', 5, 30, ''),
    'troll_citizen':     ('pics/troll1.png', 5, 30, ''),
    'troll_guard':       ('pics/troll1.png', 5, 30, ''),
    'troll_king':        ('pics/troll1.png', 5, 30, ''),
    'troll_trader':      ('pics/troll1.png', 5, 30, ''),
    'troll_shaman':      ('pics/troll1.png', 5, 30, ''),
    'troll_necromancer': ('pics/troll1.png', 5, 30, ''),
    'sack':              ('pics/sack.png', 0, 50, ''),
    'barrel':            ('pics/barrel.png', 0, 500, ''),
    }

    mm = monsters[name]
    pic = mm[0]
    m = Monster(pic)
    m.x = x
    m.y = y

    friends = 'citizen guard trader king shaman necromancer sack'.split()
    for f in friends:
        if name.endswith(f):
            m.friendly = True
    give_weapon(m, mm[3])
    m.speed = mm[1]
    m.hp = mm[2]
    m.facing = -1

    level.monsters.append(m)
    return m

@window.event
def on_draw():
    game_mode_draw()


def main():
    pyglet.clock.schedule_interval(phy, 1/60.0)
    pyglet.clock.set_fps_limit(60)
    init_item_types()
    game.level = getmap('data/map1.json')
    #game.level = loadmap('data/rogues.json')
    game.player = Monster('pics/orc1.png')
    game.player.x = 300
    game.player.y = 2200
    game.player.right_hand = Item(ItemType.alltypes['sword'])
    game.player.inventory.append(Item(ItemType.alltypes['staff']))
    game.player.inventory.append(Item(ItemType.alltypes['dagger']))
    game.player.inventory.append(Item(ItemType.alltypes['polearm']))
    game.player.inventory.append(Item(ItemType.alltypes['spear']))
    game.GTIEL = Tile('qwe','pics/orc1.png')
    pyglet.app.run()
