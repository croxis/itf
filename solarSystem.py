"""Stuff needed for running a solar system"""
import math
from math import sin, cos, radians, degrees, sqrt, atan2

import sandbox
import yaml

from direct.stdpy.file import *
from panda3d.core import NodePath, Point3, PointLight, Shader

import shapeGenerator
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


class PlanetRender(object):
    body = None
    atmosphere = None


class StarRender(object):
    body = None
    atmosphere = None
    light = None


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
        '''Gets the xyz position of the body, relative to its parent, on the
        given day before/after the date of element. Units will be in AU'''
        universals.day += globalClock.getDt() / 86400 * universals.TIMEFACTOR
        component = 0
        '''print entity
        try:
            component = entity.getComponent(BaryCenter)
            print 1
        except:
            try:
                component = entity.getComponent(Body)
                print 2
            except:
                component = entity.getComponent(Star)
                print 3
        finally:
            if component.hasOrbit:
                component.setPos(self.getBodyPosition(component, universals.day))'''
        component = entity.getComponent(BaryCenter)
        if component is None:
            component = entity.getComponent(Body)
            if component is None:
                component = entity.getComponent(Star)
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

        if universals.runClient and DB['type'] == 'star':
            component = PlanetRender()
            component.body = shapeGenerator.Sphere(1, 128)
            component.body.reparentTo(render)
            component.light = render.attachNewNode(PointLight("sunPointLight"))
            render.setLight(component.light)

        if universals.runClient and (DB['type'] == 'solid' or DB['type'] == 'moon'):
            component = PlanetRender()
            component.body = shapeGenerator.Sphere(1, 128)
            component.body.setScale(body.radius)
            component.body.reparentTo(render)
            if "atmosphere" in DB:
                component.atmosphere = shapeGenerator.Sphere(-1, 128)
                component.atmosphere.reparentTo(render)
                component.atmosphere.setScale(body.radius * 1.025)
                outerRadius = component.atmosphere.getScale().getX()
                scale = 1 / (outerRadius - component.body.getScale().getX())
                component.atmosphere.setShaderInput("fOuterRadius", outerRadius)
                component.atmosphere.setShaderInput("fInnerRadius", component.body.getScale().getX())
                component.atmosphere.setShaderInput("fOuterRadius2", outerRadius * outerRadius)
                component.atmosphere.setShaderInput("fInnerRadius2",
                    component.body.getScale().getX()
                    * component.body.getScale().getX())

                component.atmosphere.setShaderInput("fKr4PI",
                    0.000055 * 4 * 3.14159)
                component.atmosphere.setShaderInput("fKm4PI",
                    0.000015 * 4 * 3.14159)

                component.atmosphere.setShaderInput("fScale", scale)
                component.atmosphere.setShaderInput("fScaleDepth", 0.25)
                component.atmosphere.setShaderInput("fScaleOverScaleDepth", scale / 0.25)

                # Currently hard coded in shader
                component.atmosphere.setShaderInput("fSamples", 10.0)
                component.atmosphere.setShaderInput("nSamples", 10)
                # These do sunsets and sky colors
                # Brightness of sun
                ESun = 15
                # Reyleight Scattering (Main sky colors)
                component.atmosphere.setShaderInput("fKrESun", 0.000055 * ESun)
                # Mie Scattering -- Haze and sun halos
                component.atmosphere.setShaderInput("fKmESun", 0.000015 * ESun)
                # Color of sun
                component.atmosphere.setShaderInput("v3InvWavelength", 1.0 / math.pow(0.650, 4),
                                                  1.0 / math.pow(0.570, 4),
                                                  1.0 / math.pow(0.465, 4))
                #component.atmosphere.setShader(Shader.load("atmo.cg"))
            bodyEntity.addComponent(component)

        self.bodies.append(body)
        #bods.append(body)
        log.info(name + " set Up")

        if 'bodies' in DB:
            for bodyName, bodyDB in DB['bodies'].items():
                self.generateNode(bodyName, bodyDB, body)
