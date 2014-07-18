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

def update(task=None):
        """ Main update task """
        import sandbox

        # Simulate 30 FPS
        # import time
        # time.sleep( max(0.0, 0.033))
        # time.sleep(-0.2)
        # return task.cont
        if True:
            animationTime = sandbox.base.taskMgr.globalClock.getFrameTime() * 0.6

            # displace every light every frame - performance test!
            for i, light in enumerate(lights):
                lightAngle = float(math.sin(i * 1253325.0)) * \
                    math.pi * 2.0 + animationTime * 1.0
                initialPos = initialLightPos[i]
                light.setPos(initialPos + Vec3(math.sin(lightAngle) * 0.0,
                                               math.cos(lightAngle) * 0.0,
                                               math.sin(animationTime) * 10.0 ) )
        if task is not None:
            return task.cont

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
    import gui_manager
    spacedrive.gui_system.setup_screen(gui_manager.MainMenu())
    # Just for now. We will do a formal main menu scene later
    import sandbox
    from panda3d.core import Vec3
    from spacedrive.renderpipeline import BetterShader, PointLight
    import math
    shuttle = sandbox.base.loader.loadModel("Ships/Shuttle MKI/shuttle")
    shuttle.reparent_to(sandbox.base.render)
    skybox = sandbox.base.loader.loadModel("Skybox/Skybox")
    skybox.setScale(100)
    skybox.reparentTo(sandbox.base.render)
    #shuttle.set_shader(BetterShader.load('Ships/Shuttle MKI/shuttle.vertex', 'Ships/Shuttle MKI/shuttle.fragment'))
    shuttle.set_shader(sandbox.base.render_pipeline.getDefaultObjectShader(False))
    sandbox.base.render_pipeline.reloadShaders()
    skybox.setShader(BetterShader.load(
            "Shader/DefaultObjectShader/vertex.glsl", "Shader/Skybox/fragment.glsl"))
    lights = []
    initialLightPos = []
    colors = [
            Vec3(1, 0, 0),
            Vec3(0, 1, 0),
            Vec3(0, 0, 1),
            Vec3(1, 1, 0),

            Vec3(1, 0, 1),
            Vec3(0, 1, 1),
            Vec3(1, 0.5, 0),
            Vec3(0, 0.5, 1.0),
        ]

    # Add some shadow casting lights
    for i in xrange(8):
        angle = float(i) / 8.0 * math.pi * 2.0

        pos = Vec3(math.sin(angle) * 10.0, math.cos(angle) * 10.0, 7)
        # pos = Vec3( (i-3.5)*15.0, 9, 5.0)
        light = PointLight()
        light.setRadius(30.0)
        # light.setColor(Vec3(2))
        light.setColor(colors[i]*2.0)
        light.setPos(pos)
        light.setShadowMapResolution(2048)
        light.setCastsShadows(True)

        # add light
        sandbox.base.render_pipeline.addLight(light)
        lights.append(light)
        initialLightPos.append(pos)

    # Add even more normal lights
    for x in xrange(4):
        for y in xrange(4):
            break
            angle = float(x + y * 4) / 16.0 * math.pi * 2.0
            light = PointLight()
            light.setRadius(20.0)
            light.setColor(
                Vec3(math.sin(angle) * 0.5 + 0.5,
                    math.cos(angle) * 0.5 + 0.5, 0.5) * 1.0)
            initialPos = Vec3(
                (float(x) - 2.0) * 10.0, (float(y) - 2.0) * 10.0, 10.0)
            light.setPos(initialPos)
            initialLightPos.append(initialPos)
            sandbox.base.render_pipeline.addLight(light)
            lights.append(light)

    ambient = PointLight()
    ambient.setRadius(300.0)
    ambient.setPos(Vec3(10, 10, 10))
    ambient.setColor(Vec3(1.0))
    sandbox.base.render_pipeline.addLight(ambient)
    sandbox.base.addTask(update, "update")






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
