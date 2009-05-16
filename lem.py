#!/usr/bin/env python
# Copyright (C) 2009
#    Martin Heistermann, <mh at sponc dot de>
#
# lem.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lem.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with lem.py.  If not, see <http://www.gnu.org/licenses/>.

import os
import ConfigParser
from libavg import AVGApp, avg, Point2D
from libavg.AVGAppUtil import getMediaDir

g_player = avg.Player.get()

FINGERPOWER = 0.1

fingers = {}# AWGGGGH

class FingerController:
    def __init__(self, node):
        node.setEventHandler(avg.CURSORDOWN, avg.TOUCH|avg.MOUSE, self.__onDown)
        node.setEventHandler(avg.CURSORUP, avg.TOUCH|avg.MOUSE, self.__onUp)
        node.setEventHandler(avg.CURSORMOTION, avg.TOUCH|avg.MOUSE, self.__onMotion)

    def __onDown(self, event):
        fingers[event.cursorid] = event.pos

    def __onMotion(self, event):
        if event.cursorid in fingers.keys():
            fingers[event.cursorid] = event.pos

    def __onUp(self, event):
        if event.cursorid in fingers.keys():
            del fingers[event.cursorid]


def getAttraction(pos):
    direction = Point2D(0,0)
    for fingerPos in fingers.values():
        vec = fingerPos - pos
        dist = vec.getNorm()
        force = 10000.0 / (dist**2)
        #print "force", force
        direction += vec.getNormalized() * force
        #print "add", vec.getNormalized() * force
    print "==============", direction
    return direction

class LevelConfig:
    def __init__(self, levelName):
        self.__load(levelName)

    def __load(self, levelName):
        dirname = os.path.join('levels', levelName)
        confName = os.path.join(dirname, 'config.txt')
        mapName = os.path.join(dirname, 'map.png')
        gfxName = os.path.join(dirname, 'gfx.png')
        self.__loadConfigFile(confName)

    def __loadConfigFile(self, filename):
        config = ConfigParser.RawConfigParser()
        config.read(filename)
        if not config.has_section('basic'):
            print "error: level config '%s' lacks [basic] section.\n" % (filename)
            raise Exception
        for optionName in ['number','goal','interval','speed']:
            if not config.has_option('basic', optionName):
                print "error: level config '%s' lacks '%s' option." % (filename, optionName)
        self.numLemmings = config.getint('basic','number')
        self.goal        = config.getint('basic','goal')
        self.interval    = config.getint('basic','interval')
        self.speed       = config.getint('basic','speed')

class Lem:
    def __init__(self, parentNode, position, speed):
        print "lem init"
        self.__speed = speed
        self.__direction = self.__getInitialDirection()
        self.__node = g_player.createNode('image', {
            'href': 'lem.png',
            })
        parentNode.appendChild(self.__node)

        self.__goto(position)
        self.__lastMove = None
        self.__onFrameHandler = g_player.setOnFrameHandler(self.__step)

    def __getInitialDirection(self):
        return Point2D(1,0) # TODO

    def __goto(self, position):
        self.__node.pos = position - self.__node.size/2
        print "goto", self.__node.pos

    def __getPosition(self):
        return self.__node.pos + self.__node.size/2

    def __step(self):
        attractedDirection = getAttraction(self.__getPosition())
        self.__direction = (self.__direction + FINGERPOWER * attractedDirection).getNormalized()
        print "dir:", self.__direction
        self.__move()

    def __move(self):
        now = g_player.getFrameTime()
        if self.__lastMove is None:
            self.__lastMove = now
            return
        distance = self.__speed * (now - self.__lastMove)/1000.0
        self.__lastMove = now

        vec = self.__direction * distance
        # TODO: collision detection
        print "vec:", vec
        self.__node.pos += vec


class LemEmitter:
    def __init__(self, number, interval, callback, emptyCallback):
        self.__numLeft = number
        self.__interval = interval
        self.__callback = callback
        self.__emptyCallback = emptyCallback

    def start(self):
        self.__interval = g_player.setInterval(self.__interval, self.emit)

    def emit(self):
        self.__numLeft -= 1
        if self.__numLeft >= 0:
            self.__callback()
        else:
            g_player.clearInterval(self.__interval)
            self.__emptyCallback()

class Level:
    def __init__(self, levelConfig, parentNode):
        self.__lemmings = []
        def createLem():
            lem = Lem(parentNode=parentNode, position=Point2D(100,300), speed = levelConfig.speed)
            self.__lemmings.append(lem)
        self.__lemEmitter = LemEmitter(
                number = levelConfig.numLemmings,
                interval = levelConfig.interval,
                callback = createLem,
                emptyCallback = self.onEmitterEmpty)
    def onEmitterEmpty(self):
        pass

    def play(self, onExit):
        self.__lemEmitter.start()
        self.__onExit = onExit

class Game(AVGApp):
    multitouch = True
    def init(self):
        self._parentNode.mediadir = getMediaDir(__file__)
        self.__levels = []
        self.__loadLevel('easy')
        FingerController(self._parentNode) # ARRRGH FIXME

    def __loadLevel(self,name):
        levelConfig = LevelConfig('easy')
        self.__levels.append(levelConfig)

    def _enter(self):
        levelConfig = self.__levels[0]
        self.currentLevel = Level(levelConfig, self._parentNode)
        self.currentLevel.play(onExit=self.leave)

    def _leave(self):
        self.currentLevel.leave()

if __name__=='__main__':
    Game.start(resolution=(1280,720))

