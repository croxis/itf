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
parser.add_argument("-c", "--client", action="store_true",
                    help="run as a multiplayer client")
parser.add_argument("-s", "--server", action="store_true",
                    help="run as a multiplayer server")
args = parser.parse_args()

run_server = args.server
run_client = args.client
run_menu = False
if not run_server and not run_client:
    run_menu = True

if run_client:
    # We must import this before panda due to talmoc issues in linux
    from cefpython3 import cefpython

from direct.directnotify.DirectNotify import DirectNotify
from panda3d.core import loadPrcFileData
import spacedrive

from networking import server_net, client_net

loadPrcFileData("", "notify-level-ITF debug")
log = DirectNotify().newCategory("ITF")


# After initial setup we can now start sandbox
log.debug("Loading space drive")
spacedrive.init(run_server=run_server,
                run_client=(run_client or run_menu),
                log_level='debug',
                window_title='Into The Fire')

import solarSystem


def main_menu():
    """Main menu management."""
    import sandbox
    from panda3d.core import Vec3
    from spacedrive.renderpipeline import BetterShader, DirectionalLight, \
        PointLight
    import math
    import gui_manager

    spacedrive.gui_system.setup_screen(gui_manager.MainMenu())

    solar_system_db = {'Sol': {
        'Sol': {'spectral': 'G2V', 'absolute magnitude': 4.83,
                'texture': 'sun_1k_tex.jpg', 'mass': 2e+30,
                'radius': 695500000.0,
                'rotation': 25.38, 'temperature': 5778, 'type': 'star',
                'bodies': {
                    'Earth': {'atmosphere': 1,
                              'semimajor': 149598261, 'period': 365.256363004,
                              'textures': {
                                  'diffuse': 'Planets/Earth/textures/earth_#.png',
                                  'specular': 'Planets/Earth/textures/earth_spec_#.png',
                                  'night': 'Planets/Earth/textures/earth_night_#.png'},
                              'orbit': {'a': 1.00000018,
                                        'e': 'lambda d: 0.01673163 - 3.661e-07 * d',
                                        'w': 'lambda d: 108.04266274 + 0.0031795260 * d',
                                        'i': 'lambda d: -0.00054346 + -0.0001337178 * d',
                                        'M': 'lambda d: -2.4631431299999917',
                                        'N': 'lambda d: -5.11260389 + -0.0024123856 * d'},
                              'mass': 5.9742e+24, 'radius': 6371000.0,
                              'rotation': 1,
                              'type': 'solid'}}}}}

    def update(task=None):
        """ Main update task """
        if True:
            animationTime = sandbox.base.taskMgr.globalClock.getFrameTime() * 0.6

            # displace every light every frame - performance test!
            for i, light in enumerate(lights):
                lightAngle = float(math.sin(i * 1253325.0)) * \
                             math.pi * 2.0 + animationTime * 1.0
                initialPos = initialLightPos[i]
                light.setPos(initialPos + Vec3(math.sin(lightAngle) * 0.0,
                                               math.cos(lightAngle) * 0.0,
                                               math.sin(animationTime) * 10.0))
        if task is not None:
            return task.cont

    shuttle = sandbox.base.loader.loadModel("Ships/Shuttle MKI/shuttle")
    shuttle.reparent_to(sandbox.base.render)
    #shuttle.set_pos(-25, -25, 0)
    shuttle.set_pos(10, 50, 10)
    shuttle.set_hpr(-110, -30, 0)
    '''from direct.interval.LerpInterval import LerpHprInterval
    l = LerpHprInterval(shuttle, 10, Vec3(-110, -30, 360))
    l.loop()'''

    skybox = sandbox.base.loader.loadModel("Skybox/Skybox")
    skybox.setScale(sandbox.base.camLens.get_far()*0.8)
    skybox.reparentTo(sandbox.base.render)
    shuttle.set_shader(
        sandbox.base.render_pipeline.getDefaultObjectShader(False))
    sandbox.base.render_pipeline.reloadShaders()
    skybox.setShader(BetterShader.load(
        "Shader/DefaultObjectShader/vertex.glsl",
        "Shader/Skybox/fragment.glsl"))
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
    '''for i in xrange(4):
        angle = float(i) / 8.0 * math.pi * 2.0

        pos = Vec3(math.sin(angle) * 10.0, math.cos(angle) * 10.0 + 50, 7)
        light = PointLight()
        light.setRadius(10.0)
        light.setColor(colors[i] * 2.0)
        light.setPos(pos)
        light.setShadowMapResolution(1024)
        light.setCastsShadows(True)

        # add light
        sandbox.base.render_pipeline.addLight(light)
        lights.append(light)
        initialLightPos.append(pos)'''

    import spacedrive.utils.texture as texture_utils
    #texture_utils.prepare_srgb(sandbox.base.render)

    sandbox.base.addTask(update, "update")

    from spacedrive import orbit_system

    key = 'Sol'
    orbit_system.create_solar_system(name=key, database=solar_system_db)
    import sandbox
    from spacedrive.celestial_components import CelestialComponent
    for component in sandbox.get_components(CelestialComponent):
        if component.name.lower() == 'earth':
            from panda3d.core import Point3D
            spawn = Point3D(component.true_pos)
            spawn.set_y(spawn.get_y() - (6471000*1.5))
            #spawn.set_x(spawn.get_x() - (6471000*1.5))
            #spawn.set_x(spawn.get_x() + 6471000)
            system = sandbox.get_system(spacedrive.GraphicsSystem)
            system.current_pos = spawn
            print("Spawn point:", spawn)
            print("Spawn delta:", spawn - component.true_pos)
    from spacedrive.renderpipeline.Code.MovementController import MovementController

    controller = MovementController(base)
    controller.setup()
    base.accept('new game screen', start_sp_game)
    #base.camera.set_hpr(180, 0, 0)


def start_client():
    """This is not for main menu display but actual core game."""
    log.info("Setting up client network")
    spacedrive.init_client_net(client_net.NetworkSystem)


def start_server():
    log.info("Setting up server network")
    spacedrive.init_server_net(server_net.NetworkSystem)


def toggleSceneWireframe():
    base.wireframe = not base.wireframe
    if base.wireframe:
        base.render.setRenderModeWireframe()
    else:
        base.render.clearRenderMode()


def start_sp_game():
    log.info("Starting SP Game")
    start_server()
    start_client()


log.info("Setting up Solar System Body Simulator")
spacedrive.init_orbits()

log.info("TODO: Setting up dynamic physics")
# sandbox.add_system(physics.PhysicsSystem(ships.BulletPhysicsComponent))

log.info("TODO: Setting up player-ship interface system")
# sandbox.add_system(playerShipSystem.PlayerShipsSystem(ships.PilotComponent))


if run_server:
    start_server()

if run_client or run_menu:
    log.info("TODO: Setting up graphics translators")
    spacedrive.init_graphics(debug_mouse=False)
    # sandbox.add_system(graphics.GraphicsSystem(solarSystem.PlanetRender, solarSystem.StarRender))
    log.info("Setting up client gui")
    spacedrive.init_gui()
    base.wireframe = False
    base.accept("f3", toggleSceneWireframe)

if run_client:
    start_client()

if run_menu:
    main_menu()



def planetPositionDebug(task):
    #log.debug("===== Day: " + str(universals.day) + " =====")
    import sandbox
    from spacedrive.celestial_components import CelestialComponent
    from spacedrive.render_components import CelestialRenderComponent
    #graphics_system = sandbox.get_system(spacedrive.GraphicsSystem)
    for component in sandbox.get_components(CelestialComponent):
        log.debug("True Pos: " + component.name + ": " + str(component.true_pos))
    for component in sandbox.get_components(CelestialRenderComponent):
        print("Render Pos: " + component.mesh.get_name() + ": " + str(component.mesh.get_pos()))
        print("Render Scale: " + component.mesh.get_name() + ": " + str(component.mesh.get_scale()))
    return task.again


def loginDebug(task):
    sandbox.getSystem(client_net.NetworkSystem).sendLogin(universals.username,
                                                          "Hash Password")

taskMgr.doMethodLater(10, planetPositionDebug, "Position Debug")
# if universals.runClient:
# taskMgr.doMethodLater(1, loginDebug, "Login Debug")
# log.info("Setup complete.")
#base.bufferViewer.toggleEnable()
spacedrive.run()
