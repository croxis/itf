from direct.directnotify.DirectNotify import DirectNotify
log = DirectNotify().newCategory("ITF")

from panda3d.core import NodePath

runClient = False
runServer = False

solarSystemRoot = NodePath("SystemCenter")
# Connivance constant, number of seconds in an Earth day
SECONDSINDAY = 86400

# Time acceleration factor
# Default is 31,536,000 (365.25*24*60), or the earth orbits the sun in one minute
#TIMEFACTOR = 525969.162726
# Factor where it orbits once every 5 minutes
#TIMEFACTOR = 105193.832545
# Once an hour
#TIMEFACTOR = 8766.1527121
# Once a day
#TIMEFACTOR = 365.256363004
# Realtime
#TIMEFACTOR = 1
TIMEFACTOR = 100.0

# Julian day based on J2000.
day = 9131.25

# Keeps track of the user name of the client
username = "Moofoo"
