import sandbox
import solarSystem


class CameraComponent(object):
    pass


class RenderComponent(object):
    mesh = None


class GraphicsSystem(sandbox.EntitySystem):
    def process(self, entity):
        if entity.hasComponent(solarSystem.PlanetRender):
            """difference = self.getPos() - Globals.position
        if difference.length() < 10000:
            self.mesh.setPos(difference)
            self.mesh.setScale(self.radius)
            #if self.atmo:
            #    self.atmo.setScale(self.radius + 60)
        else:
            bodyPosition = difference/(difference.length()/10000) + difference/100000
            self.mesh.setPos(bodyPosition)
            scale = difference.length()/(10000 ) + difference.length()/100000
            self.mesh.setScale(self.radius/scale)
            #if self.atmo:
            #    self.atmo.setScale((self.radius+60)/scale)
        try:
            lightv = starlights[0].getPos() 
            lightdir = lightv / lightv.length()
            self.atmo.setShaderInput("v3LightPos", lightdir[0], lightdir[1], lightdir[2]) 
        except:
            print "ummm"
        cameraPos = base.camera.getPos() - self.mesh.getPos()
        self.atmo.setShaderInput("v3CameraPos", cameraPos.getX(),
            cameraPos.getY(), cameraPos.getZ())
        cameraHeight = (base.camera.getPos()-self.mesh.getPos()).length()
        self.atmo.setShaderInput("fCameraHeight", cameraHeight)
        self.atmo.setShaderInput("fCameraHeight2", cameraHeight*cameraHeight)"""