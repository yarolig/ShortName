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

class Tile:
    alltiles = {}
    def __init__(self, name, fpath):
        if fpath:
            self.image = pyglet.image.load(data.filepath(fpath))
        else:
            self.image = None
        Tile.alltiles[name]=self
    def draw(self, sx, sy, batch=None):
        if self.image is None:
            return
        s = pyglet.sprite.Sprite(self.image, x=sx, y=sy, batch=batch)
        if batch is not None:
            s.draw()
        return s
    @classmethod
    def get(cls, name):
        return cls.alltiles.get(name)

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
            return self.tiles[tx+self.th*ty]
        return None

    def set_tile(self,tx,ty,t):
        if 0 <= tx < self.tw and 0 <= ty < self.th:
            self.tiles[tx+self.th*ty] = t

    def draw(self):
        if self.b is not None and frameno > 1:
            #print 'cached', self.batch
            self.b.draw()
            return

        self.b = pyglet.graphics.Batch()
        self.bs = []
        for tx, ty in xyrange(self.tw, self.th):
            t = self.tile(tx,ty)
            self.bs.append(t.draw(sx=tx*64, sy=ty*64, batch=self.b))
        self.b.draw()
        #del batch

def loadmap(fn):
    js= json.load(open(fn))
    w=int(js['width'])
    h=int(js['height'])
    print 'wh:', w, h
    level = Level(300,300)
    data = js['layers'][0]['data']
    ts = js['tilesets'][0]['tiles']
    i=0
    for n, tt in ts.items():
        print tt
        Tile(tt['image'], tt['image'])

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

    def draw(self):
        s = pyglet.sprite.Sprite(self.img_still, x=self.x, y=self.y)
        s.draw()

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

    if keys[key.J]:
        game.player.in_thrust = True
    if keys[key.K]:
        game.player.in_swing = True
    if keys[key.L]:
        game.player.in_kick = True


def phym(m):
    assert isinstance(m, Monster)
    if m.in_a:
        m.x -= 15
    if m.in_d:
        m.x += 15
    if m.in_w:
        m.y += 15
    if m.in_s:
        m.y -= 15

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

def main():
    print "qwe"
    pyglet.clock.schedule_interval(phy, 1/60.0)
    #game.level = make_levelA()
    game.level = loadmap('data/map1.json')
    game.player = Monster('qwe')
    game.player.x = 100
    game.player.y = 100

    game.GTIEL = Tile('qwe','pics/orc1.png')
    game.bg = pyglet.sprite.Sprite(pyglet.image.load(data.filepath('backgrounds/village.png')), x=0, y=0)
    game.bg.scale = 8
    game.sky = pyglet.sprite.Sprite(pyglet.image.load(data.filepath('sky/clouds.png')), x=0, y=0)
    game.sky.scale = 8
    pyglet.app.run()
