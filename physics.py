from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape, BulletWorld
from panda3d.core import Point3, Vec3

import sandbox

import ships
import solarSystem
import universals


def getPhysics():
    return sandbox.getSystem(PhysicsSystem)


def getPhysicsWorld():
    return sandbox.getSystem(PhysicsSystem).world


def addBody(body):
    getPhysicsWorld().attachRigidBody(body)


class PhysicsSystem(sandbox.EntitySystem):
    """System that interacts with the Bullet physics world"""
    def init(self):
        self.accept("addSpaceship", self.addSpaceship)
        self.world = BulletWorld()

    def begin(self):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        #world.doPhysics(dt, 10, 1.0/180.0)

    def process(self, entity):
        pass

    def addSpaceship(self, component, accountName, position, linearVelcocity):
        component.bulletShape = BulletSphereShape(5)
        component.node = BulletRigidBodyNode(accountName)
        component.node.setMass(1.0)
        component.node.addShape(component.bulletShape)
        component.nodePath = universals.solarSystemRoot.attachNewNode(component.node)
        addBody(component.node)
        position = sandbox.getSystem(solarSystem.SolarSystemSystem).solarSystemRoot.find("**/Earth").getPos()
        #component.nodePath.setPos(position + Point3(6671, 0, 0))
        component.nodePath.setPos(position)
        #component.node.setLinearVelocity(Vec3(0, 7.72983, 0))
        component.node.setLinearVelocity(linearVelcocity)
