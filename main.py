usageText = """
Usage:

  %(prog)s [opts]

Options:

  -s Run a server
  -c Run a client

  -t Don't run threaded network

  -p [server:][port]
     game server and/or port number to contact

  -l output.log
     optional log filename

If no options are specified, the default is to run a solo client-server."""

import getopt
import sys
from pandac.PandaModules import loadPrcFileData
#import Globals


def usage(code, msg=''):
    print >> sys.stderr, usageText % {'prog': os.path.split(sys.argv[0])[1]}
    print >> sys.stderr, msg
    sys.exit(code)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'sacr:tp:l:h')
except getopt.error, msg:
    usage(1, msg)

runServer = False
runClient = False
logFilename = None
threadedNet = False

for opt, arg in opts:
    if opt == '-s':
        runServer = True
        print "Server Flag"
    elif opt == '-c':
        runClient = True
        print "Client Flag"
    elif opt == '-t':
        threadedNet = True
    elif opt == '-p':
        if ':' in arg:
            Globals.ServerHost, arg = arg.split(':', 1)
        if arg:
            Globals.ServerPort = int(arg)
    elif opt == '-l':
        logFilename = Filename.fromOsSpecific(arg)
        
    elif opt == '-h':
        usage(0)
    else:
        print 'illegal option: ' + flag
        sys.exit(1)

if logFilename:
    # Set up Panda's notify output to write to the indicated file.
    mstream = MultiplexStream()
    mstream.addFile(logFilename)
    mstream.addStandardOutput()
    Notify.ptr().setOstreamPtr(mstream, False)

    # Also make Python output go to the same place.
    sw = StreamWriter(mstream, False)
    sys.stdout = sw
    sys.stderr = sw

    # Since we're writing to a log file, turn on timestamping.
    loadPrcFileData('', 'notify-timestamp 1')

if not runClient:
    # Don't open a graphics window on the server.  (Open a window only
    # if we're running a normal client, not one of the server
    # processes.)
    loadPrcFileData('', 'window-type none\naudio-library-name null')
else:
    loadPrcFileData( '', 'frame-rate-meter-scale 0.035' )
    loadPrcFileData( '', 'frame-rate-meter-side-margin 0.1' )
    loadPrcFileData( '', 'show-frame-rate-meter 1' )
    loadPrcFileData( '', 'window-title '+ "ITF" )
    loadPrcFileData( '', "sync-video 0")

if runClient and not runServer:
    base.setSleep(0.001)
if not runClient and runServer:
    base.setSleep(0.001)

"""Server Code"""
from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", "notify-level-ITF debug")
from direct.directnotify.DirectNotify import DirectNotify
log = DirectNotify().newCategory("ITF")

log.debug("Loading sandbox")

import sandbox

from direct.stdpy.file import *

from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape, BulletWorld
from panda3d.core import Point3, Vec3

log.debug("Making room for globals")
import serverNet
import ships
import solarSystem
import universals

log.info("Setting up Solar System Body Simulator")
sandbox.addSystem(solarSystem.SolarSystemSystem(solarSystem.BaryCenter, solarSystem.Body, solarSystem.Star))

def planetPositionDebug(task):
    log.debug("===== Day: " + str(universals.day) + " =====")
    for bod in sandbox.getSystem(solarSystem.SolarSystemSystem).bodies:
        log.debug(bod.getName() + ": " + str(bod.getPos()))
    return task.again

taskMgr.doMethodLater(10, planetPositionDebug, "Position Debug")

log.info("Setting up dynamic physics")


class PhysicsSystem(sandbox.EntitySystem):
    def init(self):
        self.world = BulletWorld()

    def begin(self):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        #world.doPhysics(dt, 10, 1.0/180.0)

sandbox.addSystem(PhysicsSystem(ships.BulletPhysicsComponent))

log.info("Setting up network")
sandbox.addSystem(serverNet.NetworkSystem())

log.info("Setting up player-ship interface system")


class PlayerShipsSystem(sandbox.EntitySystem):
    #TODO: Add client --> network request
    #TODO: Add automatic update
    def newPlayerShip(account):
        ship = sandbox.createEntity()
        ship.addComponent(ships.PilotComponent())
        component = ships.BulletPhysicsComponent()
        component.bulletShape = BulletSphereShape(5)
        component.node = BulletRigidBodyNode(account.name)
        component.node.setMass(1.0)
        component.node.addShape(component.bulletShape)
        sandbox.getSystem(PhysicsSystem).world.attachRigidBody(component.node)
        position = sandbox.getSystem(solarSystem.SolarSystemSystem).solarSystemRoot.find("Sol/Sol/Earth").getPos()
        component.node.setPos(position + Point3(6671, 0, 0))
        component.node.setLinearVelocity(Vec3(0, 7.72983, 0))
        ship.addComponent(component)
        component = ships.ThrustComponent()
        ship.addComponent(component)
        component = ships.HealthComponent()
        ship.addComponent(component)

        #TODO Transmit player's ship data
        #TODO Broadcast new ship data
        #TODO Prioritize updating new client of surroundings

sandbox.addSystem(PlayerShipsSystem(ships.PilotComponent))


sandbox.run()
