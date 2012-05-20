#Client to server even
#Server to client odd
#If both will probably be even

# Packet structure
# msgID = myIterator.getUint8()
# remotePacketCount = myIterator.getUint8()
# ack = myIterator.getUint8()
# acks = myIterator.getUint16()
# hashID = myIterator.getUint16()

#Protocol space
#0-99 common game elements
#100-199 login and server handshaking and admin stuff

ACK = 0
POS_UPDATE = 1  # Position update for a given ship.  1 - 10 times a second
THRUST_REQ = 2
POS_PHYS_UPDATE = 3   # Full physics update for a given ship.
# 1 per second unless a non predictive force (ie non gravity) is applied
DATE_UPDATE = 5  # 1 per 5 seconds
CHAT = 6

NEW_SHIP = 9  # A ship has entered sensor range. All data is sent in this packet
NEW_STATION = 11  # A station has entered sensor range.

LOGIN = 100
LOGIN_DENIED = 101
LOGIN_ACCEPTED = 103

CHAT = 104

def genericPacket(key, packetCount=0):
    myPyDatagram = PyDatagram()
    myPyDatagram.addUint8(key)
    myPyDatagram.addUint8(packetCount)
    myPyDatagram.addUint8(0)
    myPyDatagram.addUint16(0)
    myPyDatagram.addUint16(0)
    return myPyDatagram

#Client to server datagram generators

#Server to client datagram generators
def loginAccepted():
    datagram = genericPacket(LOGIN_ACCEPTED)
    datagram.addString()