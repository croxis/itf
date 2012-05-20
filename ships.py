'''Ship components'''

class BulletPhysicsComponent(object):
    '''Contains reference to bullet shape and node'''
    bulletShape = None
    node = None    

class AIPilotComponent(object):
    ai = None

class PilotComponent(object):
    pass

class ThrustComponent(object):
    '''Maximum thrust values, in newtons'''
    forward = 1
    backwars = 1
    lateral = 1
    pitch = 1
    yaw = 1
    roll = 1

class HealthComponent(object):
    health = 100