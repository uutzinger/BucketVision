import cv2
import time

from subprocess import call
from threading import Lock
from threading import Thread

from networktables import NetworkTables
from networktables.util import ChooserControl
import logging

from framerate import FrameRate

import argparse

from usbcapture import USBCapture
from csdisplay import CSDisplay

import msvcrt

# Create arg parser
parser = argparse.ArgumentParser()

# Add OPTIONAL IP Address argument
# Specify with "py bucketvision3.py -ip <your address>"
# '10.41.83.2' is the competition address (default)
# '10.38.14.2' is typical practice field
# '10.41.83.215' EXAMPLE Junior 2 radio to PC with OutlineViewer in Server Mode
# '192.168.0.103' EXAMPLE Home network  
parser.add_argument('-ip', '--ip-address', required=False, default='localhost', 
help='IP Address for NetworkTable Server')

# Parse the args
args = vars(parser.parse_args())
    
# Get the IP address as a string
networkTableServer = args['ip_address']
print("NETWORK TABLE SERVER: ",networkTableServer)


# General Setup
print("Starting BUCKET VISION!")

logging.basicConfig(level=logging.DEBUG)

try:
    NetworkTables.initialize(server=networkTableServer)
except ValueError as e:
    print(e)
    print("\n\n[WARNING]: BucketVision NetworkTable Not Connected!\n\n")

bvTable = NetworkTables.getTable("BucketVision")
bvTable.putString("BucketVisionState","Starting")


# Capture Setup
camera = USBCapture(camera_num=0, res=(320, 240), network_table=bvTable, exposure=-1)
camera.start()

print("Waiting for BucketCapture to start...")
while camera.stopped:
    time.sleep(0.001)
    

# Display Setup
display = CSDisplay(camera, 'frontCam', (320, 240))
display.start()

print("Waiting for BucketDisplay to start...")
while display.stopped:
    time.sleep(0.001)


print("Display appears online!")
bvTable.putString("BucketVisionState","ONLINE")
runTime = 0
bvTable.putNumber("BucketVisionTime",runTime)
nextTime = time.time() + 1

while (True):

    if (time.time() > nextTime):
        nextTime = nextTime + 1
        runTime = runTime + 1
        bvTable.putNumber("BucketVisionTime",runTime)
        #print("BucketVisiontime = %d" % runTime)

##    if (frontCamMode.value == 'gearLift'):
##        frontProcessor.updateSelection('gearLift')
##        frontCam.updateExposure(FRONT_CAM_GEAR_EXPOSURE)
##    elif (frontCamMode.value == 'Boiler'):
##        frontProcessor.updateSelection(alliance.value + "Boiler")
##        frontCam.updateExposure(FRONT_CAM_NORMAL_EXPOSURE)

    # Monitor network tables for commands to relay to processors and servers
    cv2.waitKey(1)
    key = ord(msvcrt.getch())
    cv2.waitKey(1)
    if key == 27:
        break;

##    if (frontCam.processUserCommand(key) == True):
##        break
        
# NOTE: NOTE: NOTE:
# Sometimes the exit gets messed up, but for now we just don't care

# Shut down threads
camera.stop()
print("Waiting for Capture to stop...")
while not camera.stopped:
    time.sleep(0.001)
print("Capture appear to have stopped.")

display.stop()
print("Waiting for Display to stop...")
while not display.stopped:
    time.sleep(0.001)
print("Display appears to have stopped.")

 
# do a bit of cleanup
cv2.destroyAllWindows()
print("Goodbye!")

