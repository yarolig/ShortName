#!/usr/bin/env python
# coding: utf-8
from gamelib.ai import aim
from gamelib.input import process_input
from gamelib.item import Item, ItemType
from gamelib.logic import change_level, phym, phyp

from gamelib.monster import Monster
from gamelib.level import Level, getmap
from gamelib.common import set_game, game


class Game:
    level = Level(2,2)
    keys = {}
    player = Monster('pics/orc1.png')
    last_level = ''
    last_entry = ''

    roadsign_text = ''
    hintsign_text = ''

    mode = 'start'
    previous_mode = 'start'
    end_text = 'You are defeated.'
    end_text2 = ''
    end_bottom_text = 'Press Space to continue.'


    def __init__(self):
        set_game(self)
    def enum_monsters(self):
        yield self.player
        for i in self.level.monsters:
            yield i


def start_game(race='orc'):
    game().level = getmap('data/map1.json')
    if race == 'orc':
        game().player = Monster('pics/orc1.png')
        game().player.race = race
        game().player.right_hand = Item(ItemType.alltypes['sword'])
        change_level('data/orctown.json', 'startgame')
    elif race == 'goblin':
        game().player = Monster('pics/goblin1.png')
        game().player.race = race
        game().player.right_hand = Item(ItemType.alltypes['dagger'])
        change_level('data/goblintown.json', 'startgame')
    elif race == 'troll':
        game().player = Monster('pics/troll1.png')
        game().player.race = race
        game().player.right_hand = Item(ItemType.alltypes['staff'])
        change_level('data/swamp.json', 'startgame')
    elif race == 'dragon':
        game().player = Monster('pics/dragon1.png')
        game().player.race = race
        game().player.right_hand = Item(ItemType.alltypes['fire_wand'])
        game().player.hp = 300
        game().player.maxhp = 300
        game().player.jump_speed = 18

        change_level('data/swamp.json', 'startgame')

dead_time = 0


def phy(dt):
    game().roadsign_text = ''
    game().hintsign_text = ''

    process_input()
    phym(game().player)
    for m in game().level.monsters:
        aim(m)
        phym(m)
    for p in game().level.projectiles:
        phyp(p)

    game().level.projectiles = [p for p in game().level.projectiles if p.ttl > 0]

    global dead_time
    if game().player.hp <= 0:
        dead_time += 1
        if dead_time > 60:
            game().mode = 'end'
            dead_time = 0
