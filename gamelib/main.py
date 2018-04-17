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


fps_display = pyglet.clock.ClockDisplay()
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
    def __init__(self, name, fpath):
        if fpath:
            self.image = pyglet.image.load(data.filepath(fpath))
        else:
            self.image = None
        ItemType.alltypes[name]=self
        self.name = name
        self.damage = 0
        self.reach = 0

    def draw(self, sx, sy, batch=None):
        if self.image is None:
            return
        s = pyglet.sprite.Sprite(self.image, x=sx, y=sy, batch=batch)
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
    def draw(self, sx, sy, batch=None):
        self.itemtype.draw(sx, sy, batch)

class Level:
    def __init__(self, tw, th):
        self.tiles = [Tile('air','') for i in xrange(tw*th)]
        self.tw=tw
        self.th=th
        self.monsters=[]
        self.b = None
        self.bs = []

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
            #print 'cached', self.batch
            self.b.draw()
            return

        self.b = pyglet.graphics.Batch()
        self.bs = []
        for tx, ty in xyrange(min(self.tw, 128), self.th):
            t = self.tile(tx,ty)
            self.bs.append(t.draw(sx=tx*64, sy=ty*64, batch=self.b))
        self.b.draw()
        #del batch

def loadmap(fn):
    js= json.load(open(fn))
    w=int(js['width'])
    h=int(js['height'])
    print 'wh:', w, h
    level = Level(w,h)

    data = js['layers'][0]['data']
    ts = js['tilesets'][0]['tiles']
    tp = js['tilesets'][0]['tileproperties']
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
        if x==0: print
        try:
            s=data[i]
            if s == 0:
                pass
            else:
                level.set_tile(x,y, Tile.get(ts[str(s-1)]['image']))
            #print data[i],
        except:
            pass
        i += 1

    print
    return level

class MonsterImage:
    def __init__(self, image_name='pics/orc%s.png'):
        pass
class Monster:
    def __init__(self, image_prefix):
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0

        self.right_hand = None
        self.left_hand = None
        self.armor = None
        self.hat = None

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
        self.img_still =  pyglet.image.load(data.filepath('pics/orc1.png'))
    def reset_input(self):
        self.in_s = False
        self.in_w = False
        self.in_a = False
        self.in_d = False
        self.in_thrust = False
        self.in_swing = False
        self.in_kick = False
        self.in_jump = False

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
        l = pyglet.text.Label('X',
                              font_name='Times New Roman',
                              font_size=4,
                              x=self.x,y=self.y,
                              anchor_x='center', anchor_y='center')
        l.draw()
        if self.right_hand:
            #                                   hand_pos
            self.right_hand.draw(sx=self.x - 32 + 25 * self.facing,
                                 sy=self.y      + 32)


class Game:
    level = Level(2,2)
    keys = {}
    player = Monster('player')

window = pyglet.window.Window()
label = pyglet.text.Label('Hello, world',
                          font_name='Times New Roman',
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center')

game = Game()
window.push_handlers(keys)

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


def phym(monster):
    if True:
        m = monster
    else:
        m = Monster() # for code completion
    (tx, ty, t) = game.level.get_tx_ty_tile_at(m.x, m.y)
    (belowtx, belowty, belowt) = game.level.get_tx_ty_tile_at(m.x, m.y - 12)

    have_ground = False
    on_stairs = False
    if belowt and belowt.solid in (LADDER,):
        on_stairs = True
    #(1024 + m.y) % 64 < 16 and
    if belowt and belowt.solid in (LADDER, PLATFORM, SOLID):
        m.refill_jump()
        have_ground = True


    if m.in_s:
        if on_stairs:
            m.vy = -15
        # jump down
        elif m.in_jump and belowt and belowt.solid in (LADDER, PLATFORM):
            m.vy = -15
    else:
        if m.in_w and on_stairs:
            m.vy = 15
        # jump up
        elif m.in_jump and m.jump_left > 0:
            m.vy = 15
            m.jump_left -= 1
        else:
            m.jump_left = 0
            m.vy = 0 if have_ground else max(-15, m.vy - 3)

    if m.in_a:
        m.facing = -1
        m.vx = max(m.vx - 2, -15)
    elif m.in_d:
        m.facing = 1
        m.vx = min(m.vx + 2, 15)
    else:
        if m.vx > 2:
            m.vx = m.vx - 2
        elif m.vx < - 2:
            m.vx = m.vx + 2
        else:
            m.vx = 0

    (newx, newy, newt) = game.level.get_tx_ty_tile_at(m.x + m.vx,
                                                      m.y + m.vy)
    if newt:
        print 'newt.solid', newt.solid, 'hg=', have_ground
        if newt.solid in (AIR, PLATFORM, LADDER):
            m.x = m.x + m.vx
            m.y = m.y + m.vy


def phy(dt):
    process_input()
    phym(game.player)

@window.event
def on_draw():
    global frameno
    frameno += 1
    window.clear()
    game.sky.draw()
    #game.bg.draw()
    glPushMatrix(GL_MODELVIEW)
    glTranslatef(window.width/2-game.player.x,
                 window.height/2-game.player.y,0)
    game.level.draw()
    game.player.draw()
    glPopMatrix(GL_MODELVIEW)

    fps_display.draw()

def init_item_types():
    sword=ItemType('sword', 'pics/sword.png')
    spear=ItemType('spear', 'pics/spear.png')
    staff=ItemType('staff', 'pics/staff.png')
    dagger=ItemType('dagger', 'pics/dagger.png')


def main():
    print "qwe"
    pyglet.clock.schedule_interval(phy, 1/60.0)
    #game.level = make_levelA()
    init_item_types()
    game.level = loadmap('data/map1.json')
    game.player = Monster('qwe')
    game.player.x = 300
    game.player.y = 2200
    game.player.right_hand = Item(ItemType.alltypes['sword'])

    game.GTIEL = Tile('qwe','pics/orc1.png')
    #game.bg = pyglet.sprite.Sprite(pyglet.image.load(data.filepath('backgrounds/village.png')), x=0, y=0)
    #game.bg.scale = 8
    game.sky = pyglet.sprite.Sprite(pyglet.image.load(data.filepath('sky/clouds.png')), x=0, y=0)
    game.sky.scale = 1
    pyglet.app.run()
