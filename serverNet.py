import sys
sys.path.append('..')
import sandbox

from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", "notify-level-ITF-ServerNetwork debug")
from direct.directnotify.DirectNotify import DirectNotify
log = DirectNotify().newCategory("ITF-ServerNetwork")

import datetime

from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

from panda3d.core import ConnectionWriter, NetDatagram, QueuedConnectionManager, QueuedConnectionReader

import protocol
import ships
import universals

accountEntities = {} #{"name": id}


class AccountComponent(object):
    name = ""
    passwordHash = ""
    agentKeys = []
    address = None
    online = False
    admin = False
    mod = False
    owner = False


class NetworkSystem(sandbox.EntitySystem):
    def init(self, port=1999, backlog=1000, compress=False):
        log.debug("Initing Network System")
        self.accept("broadcastData", self.broadcastData)
        self.port = port
        self.backlog = backlog
        self.compress = compress

        self.cManager = QueuedConnectionManager()
        self.cReader = QueuedConnectionReader(self.cManager, 0)
        #self.cReader.setRawMode(True)
        self.cWriter = ConnectionWriter(self.cManager, 0)
        self.udpSocket = self.cManager.openUDPConnection(self.port)
        self.cReader.addConnection(self.udpSocket)

        self.activePlayers = []  # PlayerComponent
        self.activeConnections = {}  # {NetAddress : PlayerComponent}
        self.lastAck = {}  # {NetAddress: time}

        self.startPolling()
        self.accept("shipGenerated", self.shipGenerated)

    def startPolling(self):
        #taskMgr.add(self.tskReaderPolling, "serverListenTask", -40)
        taskMgr.doMethodLater(10, self.activeCheck, "activeCheck")

    #def tskReaderPolling(self, taskdata):
    def begin(self):
        if self.cReader.dataAvailable():
            datagram = NetDatagram()  # catch the incoming data in this instance
            # Check the return value; if we were threaded, someone else could have
            # snagged this data before we did
            if self.cReader.getData(datagram):
                myIterator = PyDatagramIterator(datagram)
                msgID = myIterator.getUint8()

                #If not in our protocol range then we just reject
                if msgID < 0 or msgID > 200:
                    return

                self.lastAck[datagram.getAddress()] = datetime.datetime.now()
                #TODO Switch to ip address and port

                #Order of these will need to be optimized later
                #We now pull out the rest of our headers
                remotePacketCount = myIterator.getUint8()
                ack = myIterator.getUint8()
                acks = myIterator.getUint16()
                hashID = myIterator.getUint16()

                if msgID == protocol.LOGIN:
                    username = myIterator.getString()
                    password = myIterator.getString()
                    if username not in accountEntities:
                        entity = sandbox.createEntity()
                        component = AccountComponent()
                        component.name = username
                        component.passwordHash = password
                        if not accountEntities:
                            component.owner = True
                        component.address = datagram.getAddress()
                        entity.addComponent(component)
                        accountEntities[username] = entity.id
                        log.info("New player " + username + " logged in.")
                        #
                        self.activePlayers.append(component)
                        self.activeConnections[component.address] = component

                        myPyDatagram = PyDatagram()
                        myPyDatagram.addUint8(protocol.LOGIN_ACCEPTED)
                        #myPyDatagram.addUint8(packetCount)
                        myPyDatagram.addUint8(0)
                        myPyDatagram.addUint8(0)
                        myPyDatagram.addUint16(0)
                        myPyDatagram.addUint16(0)
                        #
                        myPyDatagram.addFloat32(universals.day)
                        self.send(myPyDatagram, datagram.getAddress())
                        #TODO: Send initial states?
                        messenger.send("newPlayerShip", [component, entity])
                    else:
                        component = sandbox.entities[accountEntities[username]].getComponent(AccountComponent)
                        if component.passwordHash != password:
                            log.info("Player " + username + " has the wrong password.")
                        else:
                            component.connection = datagram.getConnection()
                            log.info("Player " + username + " logged in.")

    def activeCheck(self, task):
        """Checks for last ack from all known active conenctions."""
        for address, lastTime in self.lastAck.items():
            if (datetime.datetime.now() - lastTime).seconds > 30:
                component = self.activeConnections[address]
                #TODO: Disconnect
        return task.again

    def send(self, datagram, connection):
        self.cWriter.send(datagram, self.udpSocket, connection)

    def broadcastData(self, key, *args):
        # Broadcast data out to all activeConnections
        for accountID in accountEntities.items():
            sandbox.entities[accountID].getComponent()
        for con in self.activePlayers.keys():
            self.sendData(con, key, *args)

    def processData(self, netDatagram):
        myIterator = PyDatagramIterator(netDatagram)
        return self.decode(myIterator.getString())

    def shipGenerated(self, ship):
        datagram = protocol.newShip()
        datagram.addUint8(ship.getComponent(ships.PilotComponent).accountEntityID)
        datagram.addUint8(ship.id)
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getX())
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getY())
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getZ())
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getLinerVelocity().x)
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getLinerVelocity().y)
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getLinerVelocity().z)
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getH())
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getP())
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getR())
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getAngualVelocity().x)
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getAngualVelocity().y)
        datagram.addFloat32(ship.getComponent(ships.BulletPhysicsComponent).node.getAngualVelocity().z)
        print "Checking if new ship is valid for udp"
        print self.cWriter.isValidForUdp(datagram)

