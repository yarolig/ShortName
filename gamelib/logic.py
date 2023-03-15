#!/usr/bin/env python
# coding: utf-8
import pyglet

from gamelib import data
from gamelib.common import game, MAGMA, LADDER, PLATFORM, SOLID, AIR
from gamelib.level import getmap, Place
from gamelib.monster import Monster
from gamelib.sky import set_startsky
from gamelib.weapon import damage_monster


def change_level(name, entryname=None):
    #print 'change level to', name, entryname
    if not entryname:
        entryname = 'entry'

    game().last_level = name
    game().last_entry = entryname
    level = getmap(name)
    game().level = level
    game().player.hp = max(game().player.hp, game().player.maxhp)
    for o in level.places:
        if o.kind == Place.ENTRY:
            #print 'trying entries "%s" "%s"' % (o.value, entryname)
            if o.value == entryname:
                game().player.x = o.x
                game().player.y = o.y
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
    (tx, ty, t) = game().level.get_tx_ty_tile_at(m.x, m.y)
    (belowtx, belowty, belowt) = game().level.get_tx_ty_tile_at(m.x, m.y - 12)

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

    if m is game().player:
        for p in game().level.places:
            if p.kind in (Place.LABEL,):
                if (p.x - m.x) ** 2 + (p.y - m.y) ** 2 < 48 ** 2:
                    game().roadsign_text = p.label
            if p.kind in (Place.TRAVEL,):
                if (p.x - m.x) ** 2 + (p.y - m.y) ** 2 < 48 ** 2:
                    game().roadsign_text = "%s" % p.label
                    game().hintsign_text = "Press E to travel to %s (%s)" % (p.label, p.entry)
            if p.kind in (Place.CHAT,):
                if (p.x - m.x) ** 2 + (p.y - m.y) ** 2 < 48 ** 2:
                    game().hintsign_text = p.label
                    if p.item:
                        if m.right_hand:
                            if m.right_hand.itemtype.name == p.item:
                                game().roadsign_text = 'Press E to win!'
                                if m.in_use:
                                    game().mode = 'end'
                                    game().end_text = 'Victory!'

                                    game().end_text2 = p.responce
                                    skyname = ''

                                    if p.item == 'axe':
                                        skyname = 'sky/forest.png'
                                    else:
                                        skyname = 'sky/tower.png'
                                    set_startsky(pyglet.sprite.Sprite(pyglet.image.load(data.filepath(skyname)), x=0, y=0))

                                    game().end_bottom_text = 'Press Esc to exit.'
                                    return

    for i in game().level.items:
        if (i.x - m.x) ** 2 + (i.y - m.y) ** 2 < 48 ** 2:
            game().hintsign_text = "Press E to pick up %s" % (i.itemtype.name.replace('_', ' '))
    if m.in_use:
        # pickup items, chat, change level
        for p in game().level.places:
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
            for i in game().level.items:
                if (i.x - m.x) ** 2 + (i.y - m.y) ** 2 < 48 ** 2:
                    if i.itemtype.health_potion:
                        m.maxhp += 10
                        m.hp = min(m.maxhp, m.hp + 50)
                    else:
                        new_weapon = i
                        old_weapon = m.right_hand
                        m.inventory.insert(0, old_weapon)
                        m.right_hand = new_weapon
                    game().level.items.remove(i)
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

    (newx, newy, newt) = game().level.get_tx_ty_tile_at(m.x + m.vx,
                                                        m.y + m.vy)
    if newt:
        #print 'newt.solid', newt.solid, 'hg=', have_ground
        if newt.solid in (MAGMA, AIR, PLATFORM, LADDER):
            m.x = m.x + m.vx
            m.y = m.y + m.vy
            return

    (newx, newy, newt) = game().level.get_tx_ty_tile_at(m.x,
                                                        m.y + m.vy)
    if newt:
        #print 'newt.solid', newt.solid, 'hg=', have_ground
        if newt.solid in (MAGMA, AIR, PLATFORM, LADDER):
            m.x = m.x
            m.vx = 0
            m.y = m.y + m.vy
            return
        m.vy //= 2


def phyp(projectile):
    (tx, ty, t) = game().level.get_tx_ty_tile_at(projectile.x, projectile.y)
    projectile.ttl -= 1
    if t and t.solid in (SOLID, MAGMA):
        projectile.ttl = 0
    if projectile.ttl <= 0:
        return
    projectile.x += projectile.vx
    projectile.y += projectile.vy

    for mm in game().enum_monsters():
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
