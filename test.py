from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from panda3d.core import Vec3
import os
import sandbox
import spacedrive
__author__ = 'croxis'

spacedrive.init(log_level='debug', run_client=True)
shuttle = sandbox.base.loader.loadModel("Ships/Shuttle MKI/shuttle")
shuttle.reparent_to(sandbox.base.render)
shuttle.set_pos(00, 100, 0)
shuttle.set_hpr(-110, -30, 0)
#spacedrive.init_graphics(debug_mouse=False)
from spacedrive.renderpipeline.Code.RenderingPipeline import RenderingPipeline
render_pipeline = RenderingPipeline(sandbox.base)
cache_dir = sandbox.appdirs.user_cache_dir('spacedrive', 'croxis')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
render_pipeline.getMountManager().setBasePath(
    os.path.join(os.path.dirname(spacedrive.__file__), 'renderpipeline'))
render_pipeline.getMountManager().setWritePath(
    os.path.join(cache_dir, 'Shaders'))
render_pipeline.loadSettings('pipeline.ini')

from spacedrive.renderpipeline.Code.DirectionalLight import DirectionalLight
render_pipeline.create()
dPos = Vec3(40, 40, 40)
dirLight = DirectionalLight()
dirLight.setDirection(dPos)
dirLight.setShadowMapResolution(2048)
dirLight.setCastsShadows(True)
dirLight.setPos(dPos)
dirLight.setColor(Vec3(6))
render_pipeline.addLight(dirLight)


def toggleSceneWireframe():
    sandbox.base.wireframe = not sandbox.base.wireframe
    if sandbox.base.wireframe:
        sandbox.base.render.setRenderModeWireframe()
    else:
        sandbox.base.render.clearRenderMode()

sandbox.base.accept("f3", toggleSceneWireframe)
sandbox.base.wireframe = False

render_pipeline.onSceneInitialized()
skybox = render_pipeline.getDefaultSkybox()
skybox.reparentTo(render)

spacedrive.run()
