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

def usage(code, msg = ''):
    print >> sys.stderr, usageText % {'prog' : os.path.split(sys.argv[0])[1]}
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

log.debug("Loading SandBox")
import sys
sys.path.append("/home/croxis/src")
import SandBox

from direct.stdpy.file import *
from direct.task.Task import Task

from panda3d.core import NodePath, Point3

import math
from math import sin, cos, pi, radians, degrees, sqrt, atan2

import yaml

import serverNet

log.debug("Making room for globals")
solarSystemRoot = 0
# Connivance constant, number of seconds in an Earth day
SECONDSINDAY = 86400

# Time acceleration factor
# Default is 31,536,000 (365.25*24*60), or the earth orbits the sun in one minute
#TIMEFACTOR = 525969.162726
# Factor where it orbits once every 5 minutes
#TIMEFACTOR = 105193.832545
# Once an hour
#TIMEFACTOR = 8766.1527121
# Once a day
#TIMEFACTOR = 365.256363004
# Realtime
#TIMEFACTOR = 1
TIMEFACTOR = 100.0

# Julian day based on J2000.
day = 9131.25
bods = []


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

def getBodyPosition(entity, time):
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
            E = computeE(E, M, e)
        # http:#stjarnhimlen.se/comp/tutorial.html
        # Compute distance and true anomaly
        xv = a * (cos(E) - e)
        yv = a * (sqrt(1.0- e*e)* sin(E))
        
        v = atan2(yv, xv)
        r = sqrt(xv*xv + yv*yv)
        
        xh = r * ( cos(N) * cos(v+w) - sin(N) * sin(v+w) * cos(i) )
        yh = r * ( sin(N) * cos(v+w) + cos(N) * sin(v+w) * cos(i) )
        zh = r * ( sin(v+w) * sin(i) )
        position = Point3(xh, yh, zh)
        # If we are not a moon then our orbits are done in au. We need to convert to km
        # FIXME: Add moon body type
        if entity.type != 'moon':
            position = position*149598000
        return position


def computeE(E0, M, e):
        '''Iterative function for a higher accuracy of E'''
        E1 = E0 - (E0 - e * sin(E0) - M) / (1 - e * cos(E0))
        if abs(abs(degrees(E1)) - abs(degrees(E0))) > 0.001:
            E1 = computeE(E1, M, e)
        return E1

class SolarSystemSystem(SandBox.EntitySystem):
    def process(self, entity):
        '''Gets the xyz position of the body, relative to its parent, on the given day before/after the date of element. Units will be in AU'''
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
                component.setPos(getBodyPosition(component, day))    


def setupBodies(name):
    log.debug("Loading Solar System Bodies")
    stream = file("solarsystem.yaml", "r")
    solarDB = yaml.load(stream)
    stream.close()
    bodies = []
    solarSystemRoot = NodePath(name)
    for bodyName, bodyDB in solarDB[name].items():
        generateNode(bodies, bodyName, bodyDB, solarSystemRoot)


def generateNode(bodies, name, DB, parentNode):
    log.debug("Setting up " + name)
    bodyEntity = SandBox.createEntity()    
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

    bodies.append(body)
    bods.append(body)
    log.info(name + " set Up")

    if 'bodies' in DB:
        for bodyName, bodyDB in DB['bodies'].items():
            generateNode(bodies, bodyName, bodyDB, body)
    


log.info("Setting up Solar System Body Simulator")
SandBox.addSystem(SolarSystemSystem(BaryCenter, Body, Star))
setupBodies("Sol")

def simulationTask(task):
    global day 
    day += globalClock.getDt()/86400 * TIMEFACTOR
    return task.cont

def planetPositionDebug(task):
    log.debug("===== Day: " + str(day) + " =====")
    for bod in bods:
        log.debug(bod.getName() + ": " + str(bod.getPos()))
    return task.again

taskMgr.add(simulationTask, "Physics Simulation")
taskMgr.doMethodLater(10, planetPositionDebug, "Position Debug")

log.info("Setting up network")
SandBox.addSystem(serverNet.NetworkSystem())

SandBox.run()