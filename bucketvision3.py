#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bucketvision

Many hands make light work!
A multi-threaded vision pipeline example for Bit Buckets Robotics that
looks like a bucket brigade

Makes use of CScore for streaming the image

Copyright (c) 2017 - the.RocketRedNeck@gmail.com

RocketRedNeck and MIT Licenses 

RocketRedNeck hereby grants license for others to copy and modify this source code for 
whatever purpose other's deem worthy as long as RocketRedNeck is given credit where 
where credit is due and you leave RocketRedNeck out of it for all other nefarious purposes. 

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal 
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions: 

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software. 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE. 
**************************************************************************************************** 
"""

# import the necessary packages

import cv2
import time

from subprocess import call
from threading import Lock
from threading import Thread

from networktables import NetworkTables
from networktables.util import ChooserControl
import logging      # Needed if we want to see debug messages from NetworkTables

# import our classes

from framerate import FrameRate

from bucketcapture import BucketCapture     # Camera capture threads... may rename this
from bucketprocessor import BucketProcessor   # Image processing threads... has same basic structure (may merge classes)
from bucketdisplay import BucketDisplay

import argparse

# Create arg parser
parser = argparse.ArgumentParser()

# Add OPTIONAL IP Address argument
# Specify with "py bucketvision3.py -ip <your address>"
# '10.41.83.2' is the competition address (default)
# '10.38.14.2' is typical practice field
# '10.41.83.215' EXAMPLE Junior 2 radio to PC with OutlineViewer in Server Mode
# '192.168.0.103' EXAMPLE Home network  
parser.add_argument('-ip', '--ip-address', required=False, default='10.41.83.2', 
help='IP Address for NetworkTable Server')

# Parse args early so that it responds to --help
args = vars(parser.parse_args())
    
# Get the IP address as a string
networkTableServer = args['ip_address']


# Instances of GRIP created pipelines (they usually require some manual manipulation
# but basically we would pass one or more of these into one or more image processors (threads)
# to have their respective process(frame) functions called.
#
# NOTE: NOTE: NOTE:
#
# Still need to work on how unique information from each pipeline is passed around... suspect that it
# will be some context dependent read that is then streamed out for anonymous consumption...
#
#
# NOTE: NOTE: NOTE:
#
# The same pipeline instance should NOT be passed to more than one image processor
# as the results can be confused and comingled and simply does not make sense.

from nada import Nada
from cubes import Cubes
from faces import Faces
from gearlift import GearLift
from findballs import FindBalls

# And so it begins
print("Starting BUCKET VISION!")

# To see messages from networktables, you must setup logging
logging.basicConfig(level=logging.DEBUG)

try:
    NetworkTables.initialize(server=networkTableServer)
    
except ValueError as e:
    print(e)
    print("\n\n[WARNING]: BucketVision NetworkTable Not Connected!\n\n")

bvTable = NetworkTables.getTable("BucketVision")
bvTable.putString("BucketVisionState","Starting")

# Auto updating listener should be good for avoiding the need to poll for value explicitly
# A ChooserControl is also another option

# Make the cameraMode an auto updating listener from the network table
camMode = bvTable.getAutoUpdateValue('CurrentCam','frontCam') # 'frontcam' or 'rearcam'
frontCamMode = bvTable.getAutoUpdateValue('FrontCamMode', 'gears')
alliance = bvTable.getAutoUpdateValue('allianceColor','red')   # default until chooser returns a value
location = bvTable.getAutoUpdateValue('allianceLocation',1)

# NOTE: NOTE: NOTE
#
# For now just create one image pipeline to share with each image processor
# LATER we will modify this to allow for a dictionary (switch-like) interface
# to be injected into the image processors; this will allow the image processors
# to have a selector for exclusion processor of different pipelines
#
# I.e., the idea is to create separate image processors when concurrent pipelines
# are desired (e.g., look for faces AND pink elephants at the same time), and place
# the exclusive options into a single processor (e.g., look for faces OR pink elephants)

nada = Nada()
cubes = Cubes()
faces = Faces()
balls = FindBalls()
gears = GearLift(bvTable)

# NOTE: NOTE: NOTE:
#
# YOUR MILEAGE WILL VARY
# The exposure values are camera/driver dependent and have no well defined standard (i.e., non-portable)
# Our implementation is forced to use v4l2-ctl (Linux) to make the exposure control work because our OpenCV
# port does not seem to play well with the exposure settings (produces either no answer or causes errors depending
# on the camera used)
FRONT_CAM_GEAR_EXPOSURE = 0
FRONT_CAM_NORMAL_EXPOSURE = -1   # Camera default

# Declare fps to 30 because explicit is good
frontCam = BucketCapture(name="FrontCam",src=0,width=320,height=240,exposure=FRONT_CAM_GEAR_EXPOSURE, set_fps=30).start()    # start low for gears
#backCam = BucketCapture(name="BackCam",src=1,width=320,height=240,exposure=FRONT_CAM_GEAR_EXPOSURE, set_fps=30).start()    # start low for gears

print("Waiting for BucketCapture to start...")
while ((frontCam.isStopped() == True)):
    time.sleep(0.001)
#while ((backCam.isStopped() == True)):
#    time.sleep(0.001)
    
print("BucketCapture appears online!")

# NOTE: NOTE: NOTE
#
# Reminder that each image processor should process exactly one vision pipeline
# at a time (it can be selectable in the future) and that the same vision
# pipeline should NOT be sent to different image processors as this is simply
# confusing and can cause some comingling of data (depending on how the vision
# pipeline was defined... we can't control the use of object-specific internals
# being run from multiple threads... so don't do it!)

pipes = {'nada'  : nada,
         'cubes' : cubes,
         'faces' : faces,
         'balls' : balls,
         'gears'  : gears}

frontProcessor = BucketProcessor(frontCam,pipes,'gears').start()
#backProcessor = BucketProcessor(backCam,pipes,'nada').start()


print("Waiting for BucketProcessors to start...")
while ((frontProcessor.isStopped() == True)):
    time.sleep(0.001)
#while ((backProcessor.isStopped() == True)):
#    time.sleep(0.001)
print("BucketProcessors appear online!")

# Continue feeding display or streams in foreground told to stop
#fps = FrameRate()   # Keep track of display rate  TODO: Thread that too!
#fps.start()

# Loop forever displaying the images for initial testing
#
# NOTE: NOTE: NOTE: NOTE:
# cv2.imshow in Linux relies upon X11 binding under the hood. These binding are NOT inherently thread
# safe unless you jump through some hoops to tell the interfaces to operate in a multi-threaded
# environment (i.e., within the same process).
#
# For most purposes, here, we don't need to jump through those hoops or create separate processes and
# can just show the images at the rate of the slowest pipeline plus the speed of the remaining pipelines.
#
# LATER we will create display threads that stream the images as requested at their separate rates.
#

camera = {'frontCam' : frontCam}
          #'backCam'  : backCam}
processor = {'frontCam' : frontProcessor}
             #'backCam'  : backProcessor}


        
# Start the display loop
print("Waiting for BucketDisplay to start...")
display = BucketDisplay('frontCam', camera, processor).start()
#backDisplay = BucketDisplay('backCam', camera, processor).start()

while (display.isStopped() == True):
    time.sleep(0.001)
#while (backDisplay.isStopped() == True):
    #time.sleep(0.001)

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
    key = cv2.waitKey(100)

##    if (frontCam.processUserCommand(key) == True):
##        break
        
# NOTE: NOTE: NOTE:
# Sometimes the exit gets messed up, but for now we just don't care

#stop the bucket server and processors

frontProcessor.stop()      # stop this first to make the server exit


print("Waiting for BucketProcessors to stop...")
while ((frontProcessor.isStopped() == False)):
    time.sleep(0.001)
print("BucketProcessors appear to have stopped.")

display.stop()
print("Waiting for Display to stop...")
while (display.isStopped() == False):
    time.sleep(0.001)
print("Display appears to have stopped.")


#stop the camera capture
frontCam.stop()

print("Waiting for BucketCaptures to stop...")
while ((frontCam.isStopped() == False)):
    time.sleep(0.001)
print("BucketCaptures appears to have stopped.")
 
# do a bit of cleanup
cv2.destroyAllWindows()

print("Goodbye!")

