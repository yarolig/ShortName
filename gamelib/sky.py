#!/usr/bin/env python
# coding: utf-8


startsky_ = None


def startsky():
    return  startsky_


def set_startsky(s):
    global startsky_
    startsky_ = s
