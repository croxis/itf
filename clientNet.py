import sandbox
from panda3d.core import QueuedConnectionManager, QueuedConnectionReader, ConnectionWriter, NetAddress, NetDatagram
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

import protocol
import universals
from universals import log


class NetworkSystem(sandbox.EntitySystem):
    def init(self, port=2000, server="127.0.0.1", serverPort=1999, backlog=1000, compress=False):
        self.packetCount = 0
        self.port = port
        self.serverPort = serverPort
        self.serverIP = server
        self.serverAddress = NetAddress()
        self.serverAddress.setHost(server, serverPort)
        self.cManager = QueuedConnectionManager()
        self.cReader = QueuedConnectionReader(self.cManager, 0)
        self.cWriter = ConnectionWriter(self.cManager, 0)

        self.udpSocket = self.cManager.openUDPConnection(self.port)
        self.cReader.addConnection(self.udpSocket)

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

                #Order of these will need to be optimized later
                #We now pull out the rest of our headers
                remotePacketCount = myIterator.getUint8()
                ack = myIterator.getUint8()
                acks = myIterator.getUint16()
                hashID = myIterator.getUint16()
                sourceOfMessage = datagram.getConnection()

                if msgID == protocol.LOGIN_ACCEPTED:
                    log.info("Login accepted")
                    universals.day = myIterator.getFloat32()
                    print "Day set to", universals.day
                elif msgID == protocol.LOGIN_DENIED:
                    log.info("Login failed")

    def genBasicData(self, proto):
        myPyDatagram = PyDatagram()
        myPyDatagram.addUint8(proto)
        myPyDatagram.addUint8(self.packetCount)
        myPyDatagram.addUint8(0)
        myPyDatagram.addUint16(0)
        myPyDatagram.addUint16(0)
        self.packetCount += 1
        return myPyDatagram

    def sendLogin(self, username, hashpassword):
        datagram = self.genBasicData(protocol.LOGIN)
        datagram.addString(username)
        datagram.addString(hashpassword)
        universals.log.debug("sending login")
        self.sendData(datagram)

    def sendData(self, datagram):
        sent = self.cWriter.send(datagram, self.udpSocket, self.serverAddress)
        while not sent:
            print "resending"
            sent = self.cWriter.send(datagram, self.udpSocket, self.serverAddress)
            