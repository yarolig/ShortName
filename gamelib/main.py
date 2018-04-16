import data
import pyglet
from pyglet.window import key, mouse
import random

def xyrange(w,h):
    for x in xrange(w):
        for y in xrange(h):
            yield x, y

class Tile:
    alltiles = {}
    def __init__(self, name, fpath):
        if fpath:
            self.image = pyglet.image.load(data.filepath(fpath))
        else:
            self.image = None
        Tile.alltiles[name]=self
    def draw(self, x,y):
        if self.image is None:
            return
        s = pyglet.sprite.Sprite(self.image, x=x, y=y)
        s.draw()

    @classmethod
    def get(name):
        return alltiles.get(name)


class Level:
    def __init__(self, w,h):
        self.tiles = [None for i in xrange(w*h)]
        self.w=w
        self.h=h
        self.monsters=[]

    def tile(self,x,y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.tiles[x+self.h*y]
        return None

    def set_tile(self,x,y,t):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.tiles[x+self.h*y] = t
    def draw(self):
        for x, y in xyrange(self.w, self.h):
            self.tile(x,y).draw(x*32,y*32)

class Moster:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.hp = 100

class Game:
    level = Level(10,10)

window = pyglet.window.Window()
label = pyglet.text.Label('Hello, world',
                          font_name='Times New Roman',
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center')
                          
game = Game()
window.push_handlers(pyglet.window.event.WindowEventLogger())

def make_levelA():
    w=100
    h=100
    grass = Tile('grass','pics/grass.png')
    stone = Tile('stone','pics/wall.png')
    air = Tile('air', '')
    level = Level(w, h)

    for x, y in xyrange(w, h):
        level.set_tile(x,y, grass)

    return level
    for platform in xrange(20):
        px=random.randint(1,w-1)
        py=random.randint(1,h-1)
        pl=random.randint(2,20)
        for l in xrange(pl):
            level.set_tile(px+l,py, stone)
    return level

@window.event
def on_draw():
    window.clear()
    label.draw()
    #game.level.draw()
    game.GTIEL.draw(0,0)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.A:
        print('The "A" key was pressed.')
    elif symbol == key.LEFT:
        print('The left arrow key was pressed.')
    elif symbol == key.ENTER:
        print('The enter key was pressed.')


@window.event
def on_mouse_press(x, y, button, modifiers):
    if button == mouse.LEFT:
        print('The left mouse button was pressed.')



def main():
    print "qwe"
    game.level = make_levelA()

    game.GTIEL = Tile('qwe','pics/grass.png')
    pyglet.app.run()
