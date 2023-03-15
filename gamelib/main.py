import gamelib.common
import gamelib.ui
import gamelib
from . import data
import pyglet
import random
from pyglet.gl import *

from .common import game
from .game import phy
from .item import init_item_types
from .mode_controls import controls_mode_draw, controls_phy
from .mode_end import end_mode_draw, end_phy
from .mode_load import load_mode_draw
from .mode_start import start_phy, start_mode_draw
from .sky import set_startsky
from .ui import window, label, roadsign, hintsign
from .weapon import init_projectiles

# coord systems:
# t - tile (1 = 1 tile)
# s - screen (1 = 1 pixel, origin is bottom left corner of window)
# m - map (1 = 1 pixel, origin is bottom left corner of map)
gamelib.game.Game()


game().mode = 'start'
game().previous_mode = 'start'
game().end_text = 'You are defeated.'
game().end_text2 = ''
game().end_bottom_text = 'Press Space to continue.'

accdt = 0.0
def on_timer(dt):
    global accdt
    accdt += dt
    if accdt > 0.02:
        dt = accdt
        accdt = 0.0
    else:
        return
    if game().mode == 'game':
        return phy(dt)
    if game().mode == 'start':
        return start_phy()
    if game().mode == 'end':
        return end_phy()
    if game().mode == 'controls':
        return controls_phy()

@window.event
def on_draw():
    if game().mode == 'game':
        game_mode_draw()
    elif game().mode == 'start':
        start_mode_draw()
    elif game().mode == 'controls':
        controls_mode_draw()
    elif game().mode == 'end':
        end_mode_draw()
    elif game().mode == 'load':
        load_mode_draw()


def game_mode_draw():
    gamelib.common.frameno += 1
    window.clear()
    game().level.sky.draw()
    glPushMatrix()
    glTranslatef(window.width / 2 - game().player.x,
                 window.height / 2 - game().player.y, 0)
    game().level.draw()
    for m in game().level.monsters:
        if  (abs(m.x - game().player.x) < window.width // 2 + 64 and
             abs(m.y - game().player.y) < window.height // 2 + 64):
            m.draw()
    game().player.draw()
    for p in game().level.projectiles:
        if  (abs(p.x - game().player.x) < window.width // 2 + 64 and
             abs(p.y - game().player.y) < window.height // 2 + 64):
            p.draw()

    for i in game().level.items:
        if  (abs(i.x - game().player.x) < window.width // 2 + 64 and
             abs(i.y - game().player.y) < window.height // 2 + 64):
                i.draw(i.x, i.y, 90)

    glPopMatrix()
    #label.text = "%d HP, %d fps" % (game().player.hp, pyglet.clock.get_fps())
    label.text = "%d HP" % (game().player.hp)
    label.draw()
    roadsign.text = game().roadsign_text
    roadsign.draw()
    hintsign.text = game().hintsign_text
    hintsign.draw()

def main():
    pyglet.clock.schedule_interval(on_timer, 1/72.0)
    #pyglet.clock.set_fps_limit(60)
    init_item_types()
    init_projectiles()
    random_sky=random.choice(['sky/clouds.png', 'sky/forest.png'])

    set_startsky(pyglet.sprite.Sprite(pyglet.image.load(data.filepath(random_sky)), x=0, y=0))
    pyglet.app.run()


