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
loadPrcFileData("", "notify-level-ITF debug")
import universals
from universals import log

def usage(code, msg=''):
    print >> sys.stderr, usageText % {'prog': os.path.split(sys.argv[0])[1]}
    print >> sys.stderr, msg
    sys.exit(code)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'sacr:tp:l:h')
except getopt.error, msg:
    usage(1, msg)

logFilename = None
threadedNet = False

for opt, arg in opts:
    if opt == '-s':
        universals.runServer = True
        print "Server Flag"
    elif opt == '-c':
        universals.runClient = True
        print "Client Flag"
    elif opt == '-t':
        threadedNet = True
    elif opt == '-p':
        if ':' in arg:
            universals.ServerHost, arg = arg.split(':', 1)
        if arg:
            universals.ServerPort = int(arg)
    elif opt == '-l':
        logFilename = Filename.fromOsSpecific(arg)
    elif opt == '-h':
        usage(0)
    else:
        print 'illegal option: ' + opt
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



if not universals.runClient:
    # Don't open a graphics window on the server.  (Open a window only
    # if we're running a normal client, not one of the server
    # processes.)
    print "Boo"
    loadPrcFileData('', 'window-type none\naudio-library-name null')
else:
    print "Test"
    loadPrcFileData( '', 'frame-rate-meter-scale 0.035' )
    loadPrcFileData( '', 'frame-rate-meter-side-margin 0.1' )
    loadPrcFileData( '', 'show-frame-rate-meter 1' )
    loadPrcFileData( '', 'window-title '+ "ITF" )
    loadPrcFileData( '', "sync-video 0")

# After initial setup we can now start sandbox
log.debug("Loading sandbox")
import sandbox

if universals.runClient and not universals.runServer:
    base.setSleep(0.001)
if not universals.runClient and universals.runServer:
    base.setSleep(0.001)

base.disableMouse()

import physics
import playerShipSystem
import ships
import solarSystem
if universals.runClient:
    import clientNet
    log.info("Setting up client network")
    sandbox.addSystem(clientNet.NetworkSystem())
if universals.runServer:
    import serverNet
    log.info("Setting up server Pathnetwork")
    sandbox.addSystem(serverNet.NetworkSystem())

log.info("Setting up Solar System Body Simulator")
sandbox.addSystem(solarSystem.SolarSystemSystem(solarSystem.BaryCenter, solarSystem.Body, solarSystem.Star))

log.info("Setting up dynamic physics")
sandbox.addSystem(physics.PhysicsSystem(ships.BulletPhysicsComponent))

log.info("Setting up player-ship interface system")
sandbox.addSystem(playerShipSystem.PlayerShipsSystem(ships.PilotComponent))


def planetPositionDebug(task):
    log.debug("===== Day: " + str(universals.day) + " =====")
    for bod in sandbox.getSystem(solarSystem.SolarSystemSystem).bodies:
        log.debug(bod.getName() + ": " + str(bod.getPos()))
    return task.again

def loginDebug(task):
    sandbox.getSystem(clientNet.NetworkSystem).sendLogin(universals.username, "Hash Password")

taskMgr.doMethodLater(10, planetPositionDebug, "Position Debug")
if universals.runClient:
    taskMgr.doMethodLater(1, loginDebug, "Login Debug")
log.info("Setup complete.")
sandbox.run()

##TODO: FIX BULLET PHYSICS AND SOLAR SYSTE RENDER TO PROPERLY USE ROOT SOLAR SYSTEM NODE
