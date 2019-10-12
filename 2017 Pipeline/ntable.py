import sys
import time
from networktables import NetworkTable

# To see messages from networktables, you must setup logging
import logging
logging.basicConfig(level=logging.DEBUG)

if len(sys.argv) != 2:
    print("Error: specify an IP to connect to!")
    exit(0)

ip = sys.argv[1]

NetworkTable.setIPAddress(ip)
NetworkTable.setClientMode()
NetworkTable.initialize()

sd = NetworkTable.getTable("SmartDashboard")

i = 0
while True:
    try:
        print('robotTime:', sd.getNumber('robotTime'))
    except KeyError:
        print('robotTime: N/A')

    sd.putNumber('dsTime', i)
    time.sleep(1)
    i += 1
