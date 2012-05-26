'''Ship components'''

class BulletPhysicsComponent(object):
    '''Contains reference to bullet shape and node'''
    bulletShape = None
    node = None
    nodePath = None

class AIPilotComponent(object):
    ai = None

class PilotComponent(object):
    account = None
    accountEntityID = 0

class ThrustComponent(object):
    '''Maximum thrust values, in newtons'''
    forward = 1
    backwars = 1
    lateral = 1
    pitch = 1
    yaw = 1
    roll = 1

class InfoComponent(object):
    health = 100
    name = "A ship"