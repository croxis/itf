"""
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
# ## Python 3 look ahead imports ###
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--client", action="store_true", help="run as a multiplayer client")
parser.add_argument("-s", "--server", action="store_true", help="run as a multiplayer server")
args = parser.parse_args()

run_server = args.server
run_client = args.client
local_only = False
if run_client:
    #We must import this before panda due to talmoc issues
    from cefpython3 import cefpython

from direct.directnotify.DirectNotify import DirectNotify
from panda3d.core import loadPrcFileData
import spacedrive

from networking import server_net, client_net

loadPrcFileData("", "notify-level-ITF debug")
log = DirectNotify().newCategory("ITF")


if not run_client and not run_server:
    run_client = True
    run_server = True
    local_only = True


# After initial setup we can now start sandbox
log.debug("Loading space drive")
spacedrive.init(run_server=run_server,
                run_client=run_client,
                local_only=local_only,
                log_level='debug',
                window_title='Into The Fire')

import solarSystem


if run_server:
    log.info("Setting up server network")
    spacedrive.init_server_net(server_net.NetworkSystem)
if run_client:
    log.info("Setting up client network")
    spacedrive.init_client_net(client_net.NetworkSystem)
    log.info("TODO: Setting up graphics translators")
    #sandbox.add_system(graphics.GraphicsSystem(solarSystem.PlanetRender, solarSystem.StarRender))
    log.info("Setting up client gui")
    spacedrive.init_gui()
    spacedrive.gui_system.load_page('GUI/main_menu.html')


log.info("Setting up Solar System Body Simulator")
spacedrive.init_orbits()

log.info("TODO: Setting up dynamic physics")
#sandbox.add_system(physics.PhysicsSystem(ships.BulletPhysicsComponent))

log.info("TODO: Setting up player-ship interface system")
#sandbox.add_system(playerShipSystem.PlayerShipsSystem(ships.PilotComponent))


def planetPositionDebug(task):
    log.debug("===== Day: " + str(universals.day) + " =====")
    for bod in sandbox.getSystem(solarSystem.SolarSystemSystem).bodies:
        log.debug(bod.getName() + ": " + str(bod.getPos()))
    return task.again

def loginDebug(task):
    sandbox.getSystem(client_net.NetworkSystem).sendLogin(universals.username, "Hash Password")

#taskMgr.doMethodLater(10, planetPositionDebug, "Position Debug")
#if universals.runClient:
#    taskMgr.doMethodLater(1, loginDebug, "Login Debug")
#log.info("Setup complete.")
spacedrive.run()
