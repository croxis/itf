# ## Python 3 look ahead imports ###
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from panda3d.core import loadPrcFileData

import datetime

from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

from panda3d.core import ConnectionWriter, NetDatagram, QueuedConnectionManager, QueuedConnectionReader

import protocol
import ships
import universals

from direct.directnotify.DirectNotify import DirectNotify

import sandbox
#import protocol_old
#import shipComponents
#import universals
#import shipSystem

loadPrcFileData("", "notify-level-ITF-ServerNetwork debug")
log = DirectNotify().newCategory("ITF-ServerNetwork")


class AccountComponent(object):
    address = None


class NetworkSystem(sandbox.UDPNetworkSystem):
    def init2(self):
        self.accept("broadcastData", self.broadcast_data)
        self.accept("confirmPlayerStations", self.confirmPlayerStations)
        self.accept('playerDisconnected', self.playerDisconnected)
        self.activePlayers = []  # PlayerComponent
        self.playerMap = {}  # {Address: Shipid}
        #self.shipMap = {} # {ShipID: {CONSOL: Netaddress}}
        #self.accept("shipGenerated", self.shipGenerated)
        #if universals.runServer and not universals.runClient:
        #    sandbox.base.taskMgr.doMethodLater(0.2, self.sendShipUpdates, 'shipUpdates')

    def process_packet(
        self, msgID, remotePacketCount,
        ack, acks, hashID, serialized, address
    ):
        #If not in our protocol range then we just reject
        if msgID < 0 or msgID > 200:
            return
        data = protocol_old.readProto(msgID, serialized)
        if data is None and msgID != protocol_old.LOGIN:
            log.warning("Package reading error: " + str(msgID) + " " + serialized)
            return

        #Order of these will need to be optimized later
        if msgID == protocol_old.LOGIN:
            #TODO, if connection previously existed, reconnect
            #TODO: send current mission status.
            #TODO: Move ship select to separate function
            ackDatagram = protocol_old.shipClasses(shipSystem.shipClasses)
            self.sendData(ackDatagram, address)
            ackDatagram = protocol_old.playerShipStations()
            self.sendData(ackDatagram, address)
            entity = sandbox.createEntity()
            component = AccountComponent()
            component.address = address
            entity.addComponent(component)
            self.activeConnections[component.address] = component
        elif msgID == protocol_old.REQUEST_CREATE_SHIP:
            sandbox.send('spawnShip', [data.name, data.className, True])
        elif msgID == protocol_old.REQUEST_STATIONS:
            entity = sandbox.entities[data.ship[0].id]
            #info = entity.get_component(shipComponents.InfoComponent)
            player = entity.get_component(shipComponents.PlayerComponent)
            stations = data.ship[0].stations
            for stationName in universals.playerStations:
                if getattr(player, stationName) != 0:
                    print "Resend ship select window"
            sandbox.send('setPlayerStations', [address, data.ship[0].id, stations])
        elif msgID == protocol_old.SET_THROTTLE:
            sandbox.send('setThrottle', [self.playerMap[address], data])
        elif msgID == protocol_old.SET_TARGET:
            sandbox.send('setTarget', [self.playerMap[address], data])
        '''if username not in accountEntities:
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
            ackDatagram = protocol.loginAccepted(entity.id)
            self.sendData(ackDatagram, datagram.getAddress())
            #TODO: Send initial states?
            #messenger.send("newPlayerShip", [component, entity])
        else:
            component = sandbox.entities[accountEntities[username]].get_component(AccountComponent)
            if component.passwordHash != password:
                log.info("Player " + username + " has the wrong password.")
            else:
                component.connection = datagram.getConnection()
                log.info("Player " + username + " logged in.")'''

    def broadcast_data(self, datagram):
        # Broadcast data out to all activeConnections
        #for accountID in accountEntities.items():
            #sandbox.entities[accountID].get_component()
        for addr in self.activeConnections.keys():
            self.sendData(datagram, addr)

    def sendShipUpdates(self, task):
        ships = sandbox.get_system(shipSystem.ShipSystem).getPlayerShipEntities()
        ships += sandbox.get_entities_by_component_type(shipComponents.AIPilotComponent)
        #self.broadcastData(protocol.sendShipUpdates(ships))
        for ship in ships:
            self.broadcastData(protocol_old.sendShipUpdates([ship]))
        return task.again

    def playerDisconnected(self, address):
        try:
            print "Removing", address, "from", self.playerMap
            del self.playerMap[address]
        except:
            print address, "not in", self.playerMap

    def confirmPlayerStations(self, netAddress, shipid, stations):
        self.playerMap[netAddress] = shipid
        datagram = protocol_old.confirmStations(shipid, stations)
        self.sendData(datagram, netAddress)



class ClientComponent:
    """Theoretical component that stores which clients are
    also tracking this entity as well as last update"""


accountEntities = {} # {"name": id}


class AccountComponent(object):
    name = ""
    passwordHash = ""
    agentKeys = []
    address = None
    online = False
    admin = False
    mod = False
    owner = False


class OldNetworkSystem(sandbox.EntitySystem):
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
                        ackDatagram = protocol.loginAccepted(entity.id)
                        self.sendData(ackDatagram, datagram.getAddress())
                        #TODO: Send initial states?
                        messenger.send("newPlayerShip", [component, entity])
                    else:
                        component = sandbox.entities[accountEntities[username]].get_component(AccountComponent)
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

    def sendData(self, datagram, address):
        self.cWriter.send(datagram, self.udpSocket, address)

    def broadcastData(self, datagram):
        # Broadcast data out to all activeConnections
        #for accountID in accountEntities.items():
            #sandbox.entities[accountID].get_component()
        for addr in self.activeConnections.keys():
            self.sendData(datagram, addr)

    def processData(self, netDatagram):
        myIterator = PyDatagramIterator(netDatagram)
        return self.decode(myIterator.getString())

    def shipGenerated(self, ship):
        datagram = protocol.newShip(ship)
        print "Checking if new ship is valid for udp:", self.cWriter.isValidForUdp(datagram)
        self.broadcastData(datagram)
        datagram = protocol.movedShip(ship)
        address = self.getAddress(ship.get_component(ships.PilotComponent).accountEntityID)
        self.sendData(datagram, address)

    def getAddress(self, entityID):
        return sandbox.components[entityID][AccountComponent].address


class ClientComponent:
    """Theoretical component that stores which clients are 
    also tracking this entity as well as last update"""