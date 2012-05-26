import sandbox

from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape
from panda3d.core import Point3, Vec3

import physics
import ships
import solarSystem
import universals


class PlayerShipsSystem(sandbox.EntitySystem):
    #TODO: Add client --> network request
    #TODO: Add automatic update
    def init(self):
        self.accept("newPlayerShip", self.newPlayerShip)

    def process(self, entity):
        pass

    def newPlayerShip(self, account, accountEntity):
        ship = sandbox.createEntity()
        component = ships.PilotComponent()
        component.account = account
        ship.addComponent(component)
        component = ships.BulletPhysicsComponent()
        component.bulletShape = BulletSphereShape(5)
        component.node = BulletRigidBodyNode(account.name)
        component.node.setMass(1.0)
        component.node.addShape(component.bulletShape)
        component.nodePath = universals.solarSystemRoot.attachNewNode(component.node)
        physics.addBody(component.node)
        position = sandbox.getSystem(solarSystem.SolarSystemSystem).solarSystemRoot.find("**/Earth").getPos()
        component.nodePath.setPos(position + Point3(6671, 0, 0))
        component.node.setLinearVelocity(Vec3(0, 7.72983, 0))
        ship.addComponent(component)
        component = ships.ThrustComponent()
        ship.addComponent(component)
        component = ships.InfoComponent()
        ship.addComponent(component)
        messenger.send("shipGenerated", [ship])
        #TODO Transmit player's ship data
        #TODO Broadcast new ship data
        #TODO Prioritize updating new client of surroundings