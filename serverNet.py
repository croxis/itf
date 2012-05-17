import sys
sys.path.append('..')
import SandBox

from pandac.PandaModules import loadPrcFileData
#loadPrcFileData("", "notify-level-ITF-Network debug")
from direct.directnotify.DirectNotify import DirectNotify
log = DirectNotify().newCategory("ITF-Network")

from direct.directnotify.DirectNotify import DirectNotify
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.fsm import FSM
from direct.showbase.DirectObject import DirectObject
from direct.task import Task

from panda3d.core import ConnectionWriter, NetAddress, NetDatagram, PointerToConnection, QueuedConnectionListener, QueuedConnectionManager, QueuedConnectionReader

class AccountComponent(object):
    name = ""
    passwordHash = ""
    agentKeys = []
    connection = None
    online = False
    admin = False
    mod = False
    owner = False

class NetworkSystem(SandBox.EntitySystem):
    def init(self, port=1999, backlog=1000, compress=False):
        log.debug("Initing Network System")
        self.accept("broadcastData", self.broadcastData)
        self.port = port
        self.backlog = backlog
        self.compress = compress
        
        self.cManager = QueuedConnectionManager()
        self.cListener = QueuedConnectionListener(self.cManager, 0)
        self.cReader = QueuedConnectionReader(self.cManager, 0)
        self.cWriter = ConnectionWriter(self.cManager,0)
        
        self.activeConnections = {} # {connection: player}
        self.activePlayers = {} # {player: connection}
        
        self.connect(self.port, self.backlog)
        self.startPolling()

    def connect(self, port, backlog=1000):
        # Bind to our socket
        tcpSocket = self.cManager.openTCPServerRendezvous(port, backlog)
        self.cListener.addConnection(tcpSocket)

    def startPolling(self):
        taskMgr.add(self.tskListenerPolling, "serverListenTask", -40)
        taskMgr.add(self.tskDisconnectPolling, "serverDisconnectTask", -39)
        taskMgr.add(self.getData, "serverPollReader", -38)
        
    def tskListenerPolling(self, task):
        if self.cListener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()
        
            if self.cListener.getNewConnection(rendezvous, netAddress, newConnection):
                newConnection = newConnection.p()
                #self.activeConnections.append(newConnection) # Remember connection
                self.cReader.addConnection(newConnection)     # Begin reading connection
                #key = "requestLogin"
                #self.sendData(newConnection, key)
                print "New connection"
        return Task.cont
    
    def tskDisconnectPolling(self, task):
        while self.cManager.resetConnectionAvailable() == True:
            connPointer = PointerToConnection()
            self.cManager.getResetConnection(connPointer)
            connection = connPointer.p()
            
            # Remove the connection we just found to be "reset" or "disconnected"
            self.cReader.removeConnection(connection)
            
            # Loop through the activeConnections till we find the connection we just deleted
            # and remove it from our activeConnections list
            #for c in range(0, len(self.activeConnections)):
                #if self.activeConnections[c] == connection:
                    #del self.activeConnections[c]
                    #break
            #player = self.activeConnections
            del self.activePlayers[self.activeConnections[connection]]
            del self.activeConnections[connection]
                    
        return Task.cont
    
    def broadcastData(self, key, *args):
        # Broadcast data out to all activeConnections
        for con in self.activePlayers.keys():
            self.sendData(con, key, *args)
        
    def processData(self, netDatagram):
        myIterator = PyDatagramIterator(netDatagram)
        return self.decode(myIterator.getString())
        
    def getClients(self):
        # return a list of all activeConnections
        return self.activeConnections
        
    def encode(self, data, compress=False):
        # encode(and possibly compress) the data with rencode
        return rencode.dumps(data)
        
    def decode(self, data):
        # decode(and possibly decompress) the data with rencode
        return rencode.loads(data)
        
    def sendData(self, player, key, *args):
        print "Server sends:", key, args
        myPyDatagram = PyDatagram()
        myPyDatagram.addString(self.encode([key, args]))
        self.cWriter.send(myPyDatagram, self.activePlayers[player])
        
    def lowSendData(self, connection, key, *args):
        """For cases, such as login and packet filtering, where the player/connection mapping may not exist."""
        print "Server low sends:", key, args
        myPyDatagram = PyDatagram()
        myPyDatagram.addString(self.encode([key, args]))
        self.cWriter.send(myPyDatagram, connection)
    
    def getData(self, task=None):
        data = []
        while self.cReader.dataAvailable():
            datagram = NetDatagram()  # catch the incoming data in this instance
            # Check the return value; if we were threaded, someone else could have
            # snagged this data before we did
            if self.cReader.getData(datagram):
                #con = PointerToConnection()
                #con = datagram.getConnection()
                datum=self.processData(datagram)
                #me = {}
                #me["test"] = "got" + datum["test"]
                #self.sendData(me, con)
                data.append(datum) 
        #return data
        #print "Server getdata", data
        if data:
            #messenger.send("gotData", data)
            #TODO: This is an expensive check. Need to think of a better way to structure this
            print "Server gets:", data[0][0], data[0][1]
            if data[0][0] == "login":
                self.loginManager(datagram.getConnection(), data[0][1][0], data[0][1][1])
            #print "got some data!", data[0][0], data[0][1]
            messenger.send(data[0][0], [self.activeConnections[datagram.getConnection()], data[0][1]])
        return Task.cont
    
    def loginManager(self, connection, username, password):
        playerEntity = None
        playerList = []
        owner = False
        for id in SandBox.systems[PlayerSystem].entities.keys():
            player = SandBox.components[id][PlayerComponent]
            log.debug("Login detected: Checking player " + player.name)
            playerList.append({"name": player.name}) #This is a dict in case we expand functionality later
            if player.name == username and player.password == password:
                playerEntity = player
            elif player.name == username and player.password != password:
                self.lowSendData(connection, "loginResponse", False, "Incorrect password")
                return
        if not playerEntity and not NEWPLAYERS:
            self.lowSendData(connection, "loginResponse", False, "Not Accepting new players")
            return
        elif not playerEntity and NEWPLAYERS:
            if not self.entities:
                owner = True
            playerEntity = SandBox.createEntity()
            playerComponent = PlayerComponent()
            playerEntity.addComponent(playerComponent)
            playerComponent.name = username
            playerComponent.password = password
            playerComponent.owner = owner

        self.activeConnections[connection] = playerEntity
        self.activePlayers[playerEntity] = connection
        
        self.sendData(playerEntity, "loginResponse", True, state.state)
        self.sendData(playerEntity, "playerList", playerList)
        self.broadcastData("playerJoined", username)