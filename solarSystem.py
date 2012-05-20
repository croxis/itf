"""Stuff needed for running a solar system"""
from math import sin, cos, radians, degrees, sqrt, atan2

import sandbox
import yaml

from panda3d.core import NodePath, Point3

import universals

#from pandac.PandaModules import loadPrcFileData
#loadPrcFileData("", "notify-level-ITF debug")
from direct.directnotify.DirectNotify import DirectNotify
log = DirectNotify().newCategory("ITF-SolarSystem")


class BaryCenter(NodePath):
    pass


class Body(BaryCenter):
    period = 0
    mass = 1
    radius = 1
    kind = "solid"
    orbit = {}


class Star(Body):
    kind = "star"
    absoluteM = 1
    spectralType = ""


class SolarSystemSystem(sandbox.EntitySystem):
    """Generates celestial bodies and moves them in orbit"""
    def getBodyPosition(self, entity, time):
        """Returns celestial position relative to the parent"""
        # Convert to radians
        M = radians(eval(entity.orbit['M'])(time))
        w = radians(eval(entity.orbit['w'])(time))
        i = radians(eval(entity.orbit['i'])(time))
        N = radians(eval(entity.orbit['N'])(time))
        a = entity.orbit['a']
        e = eval(entity.orbit['e'])(time)
        # Compute eccentric anomaly
        E = M + e * sin(M) * (1.0 + e * cos(M))
        if degrees(E) > 0.05:
            E = self.computeE(E, M, e)
        # http:#stjarnhimlen.se/comp/tutorial.html
        # Compute distance and true anomaly
        xv = a * (cos(E) - e)
        yv = a * (sqrt(1.0 - e * e) * sin(E))
        v = atan2(yv, xv)
        r = sqrt(xv * xv + yv * yv)
        xh = r * (cos(N) * cos(v + w) - sin(N) * sin(v + w) * cos(i))
        yh = r * (sin(N) * cos(v + w) + cos(N) * sin(v + w) * cos(i))
        zh = r * (sin(v + w) * sin(i))
        position = Point3(xh, yh, zh)
        # If we are not a moon then our orbits are done in au.
        # We need to convert to km
        # FIXME: Add moon body type
        if entity.type != 'moon':
            position = position * 149598000
        return position

    def computeE(self, E0, M, e):
        '''Iterative function for a higher accuracy of E'''
        E1 = E0 - (E0 - e * sin(E0) - M) / (1 - e * cos(E0))
        if abs(abs(degrees(E1)) - abs(degrees(E0))) > 0.001:
            E1 = self.computeE(E1, M, e)
        return E1

    def process(self, entity):
        '''Gets the xyz position of the body, relative to its parent, on the given day before/after the date of element. Units will be in AU'''
        universals.day += globalClock.getDt() / 86400 * universals.TIMEFACTOR
        component = 0
        try:
            component = entity.getComponent(BaryCenter)
        except:
            try:
                component = entity.getComponent(Body)
            except:
                component = entity.getComponent(Star)
        finally:
            if component.hasOrbit:
                component.setPos(self.getBodyPosition(component, universals.day))

    def init(self, name='Sol'):
        log.debug("Loading Solar System Bodies")
        stream = file("solarsystem.yaml", "r")
        solarDB = yaml.load(stream)
        stream.close()
        self.bodies = []
        self.solarSystemRoot = NodePath(name)
        for bodyName, bodyDB in solarDB[name].items():
            self.generateNode(bodyName, bodyDB, self.solarSystemRoot)

    def generateNode(self, name, DB, parentNode):
        log.debug("Setting up " + name)
        bodyEntity = sandbox.createEntity()
        if DB['type'] == 'solid':
            body = Body(name)
        elif DB['type'] == 'moon':
            body = Body(name)
            body.kind = "moon"
        elif DB['type'] == 'star':
            body = Star(name)
            body.absoluteM = DB['absolute magnitude']
            body.spectral = DB['spectral']
        elif DB['type'] == 'barycenter':
            body = BaryCenter(name)

        if DB['type'] != "barycenter":
            body.mass = DB['mass']
            body.radius = DB['radius']
            body.rotation = DB['rotation']

        if 'orbit' in DB:
            body.hasOrbit = True
            body.orbit = DB['orbit']
            body.period = DB['period']
        else:
            body.hasOrbit = False

        body.type = DB['type']
        body.reparentTo(parentNode)
        bodyEntity.addComponent(body)

        self.bodies.append(body)
        #bods.append(body)
        log.info(name + " set Up")

        if 'bodies' in DB:
            for bodyName, bodyDB in DB['bodies'].items():
                self.generateNode(bodyName, bodyDB, body)
