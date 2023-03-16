#!/usr/bin/env python
# coding: utf-8
from gamelib.common import game
from gamelib.monster import Monster

def aim(m : Monster):
    m.reset_input()
    if m.friendly:
        return
    player_sdist_sq = (game().player.x - m.x) ** 2 + (game().player.y - m.y) ** 2

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
    if game().player.x * m.facing < m.x * m.facing:
        good_facing = False

    if game().player.x + closing_dist < m.x:
        m.in_a = True

    if game().player.x - closing_dist > m.x:
        m.in_d = True

    if game().player.y > m.y + 32 and player_sdist_sq > 64 ** 2:
        m.in_jump = True

    if good_facing and player_sdist_sq < (closing_dist * 2) ** 2 and game().player.y + 64 > m.y:
        m.in_thrust = True

    if not good_facing:
        if m.facing == 1:
            m.in_a = True
        else:
            m.in_d = True
