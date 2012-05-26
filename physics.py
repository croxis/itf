from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape, BulletWorld
from panda3d.core import Point3, Vec3

import sandbox

def getPhysics():
    return sandbox.getSystem(PhysicsSystem)

def getPhysicsWorld():
    return sandbox.getSystem(PhysicsSystem).world

def addBody(body):
    getPhysicsWorld().attachRigidBody(body)

class PhysicsSystem(sandbox.EntitySystem):
    def init(self):
        self.world = BulletWorld()

    def begin(self):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        #world.doPhysics(dt, 10, 1.0/180.0)

    def process(self, entity):
        pass