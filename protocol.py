from direct.distributed.PyDatagram import PyDatagram

import ships
import universals
#Client to server even
#Server to client odd
#If both will probably be even

# Packet structure
# msgID = myIterator.getUint8()
# remotePacketCount = myIterator.getUint8()
# ack = myIterator.getUint8()
# acks = myIterator.getUint16()
# hashID = myIterator.getUint16()

#Protocol space
#0-99 common game elements
#100-199 login and server handshaking and admin stuff

ACK = 0
POS_UPDATE = 1  # Position update for a given ship.  1 - 10 times a second
THRUST_REQ = 2
POS_PHYS_UPDATE = 3   # Full physics update for a given ship.
# 1 per second unless a non predictive force (ie non gravity) is applied
DATE_UPDATE = 5  # 1 per 5 seconds
CHAT = 6

NEW_SHIP = 9  # A ship has entered sensor range. All data is sent in this packet
NEW_STATION = 11  # A station has entered sensor range.

PLAYER_MOVED_SHIP = 13 # When a player moves to a new ship

LOGIN = 100
LOGIN_DENIED = 101
LOGIN_ACCEPTED = 103

ACCOUNT_REC = 110  # Requests name of account for a given id entity id
ACCOUNT_ACK = 111

CHAT = 104


def genericPacket(key, packetCount=0):
    myPyDatagram = PyDatagram()
    myPyDatagram.addUint8(key)
    myPyDatagram.addUint8(packetCount)
    myPyDatagram.addUint8(0)
    myPyDatagram.addUint16(0)
    myPyDatagram.addUint16(0)
    return myPyDatagram

#Client to server datagram generators

#Server to client datagram generators


def loginAccepted(x):
    datagram = genericPacket(LOGIN_ACCEPTED)
    datagram.addUint8(x)  # entity id of user
    datagram.addFloat32(universals.day)
    return datagram


def newShip(ship):
    datagram = genericPacket(NEW_SHIP)
    datagram.addUint16(ship.getComponent(ships.PilotComponent).accountEntityID)
    datagram.addUint16(ship.id)
    datagram.addString(ship.getComponent(ships.InfoComponent).name)
    datagram.addUint8(ship.getComponent(ships.InfoComponent).health)
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).nodePath.getX())
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).nodePath.getY())
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).nodePath.getZ())
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getLinearVelocity().x)
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getLinearVelocity().y)
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getLinearVelocity().z)
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).nodePath.getH())
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).nodePath.getP())
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).nodePath.getR())
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getAngularVelocity().x)
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getAngularVelocity().y)
    datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getAngularVelocity().z)
    return datagram

def movedShip(ship):
    datagram = genericPacket(PLAYER_MOVED_SHIP)
    datagram.addUint16(ship.getComponent(ships.PilotComponent).accountEntityID)
    datagram.addUint16(ship.id)
    return datagram