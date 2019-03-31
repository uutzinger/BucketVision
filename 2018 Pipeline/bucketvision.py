# -*- coding: utf-8 -*-
"""
bucketvision

Many hands make light work!
A multi-threaded vision pipeline example for Bit Buckets Robotics that
looks like a bucket brigade

Thanks to Igor Maculan for an mjpg steaming solution!
https://gist.github.com/n3wtron/4624820

Copyright (c) 2017 - RocketRedNeck.com RocketRedNeck.net 

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
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
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
from bucketserver import BucketServer       # Run the HTTP service

import platform

if (platform.system() == 'Windows'):
    roboRioAddress = '127.0.0.1'
else:
    #roboRioAddress = '10.38.14.2' # On practice field
    roboRioAddress = '192.168.0.103' # On competition field

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

from rope import Rope

from blueboiler import BlueBoiler
from redboiler import RedBoiler
from boiler import Boiler
from gearlift import GearLift
from smokestack import SmokeStack

# And so it begins
print("Starting BUCKET VISION!")

# To see messages from networktables, you must setup logging
logging.basicConfig(level=logging.DEBUG)

try:
    NetworkTables.setIPAddress(roboRioAddress)
    NetworkTables.setClientMode()
    NetworkTables.initialize()
    
except ValueError as e:
    print(e)
    print("\n\n[WARNING]: BucketVision NetworkTable Not Connected!\n\n")

bvTable = NetworkTables.getTable("BucketVision")
bvTable.putString("BucketVisionState","Starting")

# Auto updating listener should be good for avoiding the need to poll for value explicitly
# A ChooserControl is also another option

# Make the cameraMode an auto updating listener from the network table
camMode = bvTable.getAutoUpdateValue('CurrentCam','frontCam') # 'frontcam' or 'rearcam'
frontCamMode = bvTable.getAutoUpdateValue('FrontCamMode', 'gearLift') # 'gearLift' or 'Boiler'
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

redBoiler = RedBoiler()
blueBoiler = BlueBoiler()
boiler = Boiler()
gearLift = GearLift(bvTable)

rope = Rope()

nada = Nada()

# NOTE: NOTE: NOTE:
#
# YOUR MILEAGE WILL VARY
# The exposure values are camera/driver dependent and have no well defined standard (i.e., non-portable)
# Our implementation is forced to use v4l2-ctl (Linux) to make the exposure control work because our OpenCV
# port does not seem to play well with the exposure settings (produces either no answer or causes errors depending
# on the camera used)
FRONT_CAM_GEAR_EXPOSURE = 0
FRONT_CAM_NORMAL_EXPOSURE = -1   # Camera default

frontCam = BucketCapture(name="FrontCam",src=0,width=320,height=240,exposure=FRONT_CAM_GEAR_EXPOSURE).start()    # start low for gears

print("Waiting for BucketCapture to start...")
while ((frontCam.isStopped() == True)):
    time.sleep(0.001)

print("BucketCapture appears online!")

# NOTE: NOTE: NOTE
#
# Reminder that each image processor should process exactly one vision pipeline
# at a time (it can be selectable in the future) and that the same vision
# pipeline should NOT be sent to different image processors as this is simply
# confusing and can cause some comingling of data (depending on how the vision
# pipeline was defined... we can't control the use of object-specific internals
# being run from multiple threads... so don't do it!)

frontPipes = {'redBoiler' : nada, #boiler, #redBoiler,
              'blueBoiler' : nada, #boiler, #blueBoiler,
              'gearLift' : gearLift}

frontProcessor = BucketProcessor(frontCam,frontPipes,'gearLift').start()


print("Waiting for BucketProcessors to start...")
while ((frontProcessor.isStopped() == True)):
    time.sleep(0.001)

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
processor = {'frontCam' : frontProcessor}

class CamHTTPHandler(BaseHTTPRequestHandler):
    _stop = False
    fps = FrameRate()

    def stop(self):
        self._self = True
        
    def do_GET(self):
        print(self.path)
        self.fps.start()
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            
            while (frontProcessor.isStopped() == False):
                try:

                    
                    try:
                        camModeValue = camMode.value
                        cameraSelection = camera[camModeValue]
                        processorSelection = processor[camModeValue]
                    except:
                        camModeValue = 'frontCam'
                        cameraSelection = camera[camModeValue]
                        processorSelection = processor[camModeValue]
                        
                    
                    (img, count, isNew) = processorSelection.read()
                    
                    if (isNew == False):
                            continue
                    camFps = cameraSelection.fps.fps()
                    procFps = processorSelection.fps.fps()
                    procDuration = processorSelection.duration.duration()

                    cv2.putText(img,"{:.1f}".format(camFps),(0,20),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)
                    if (procFps != 0.0):
                        cv2.putText(img,"{:.1f}".format(procFps) + " : {:.0f}".format(100 * procDuration * procFps) + "%",(0,40),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)
                    cv2.putText(img,"{:.1f}".format(self.fps.fps()),(0,60),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)

                    cv2.putText(img,camModeValue,(0, 80),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)
                    cv2.putText(img,processorSelection.ipselection,(0,100),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)

                    r, buf = cv2.imencode(".jpg",img)
                    self.wfile.write("--jpgboundary\r\n")
                    self.send_header('Content-type','image/jpeg')
                    self.send_header('Content-length',str(len(buf)))
                    self.end_headers()
                    self.wfile.write(bytearray(buf))
                    self.wfile.write('\r\n')

                    self.fps.update()
                    
                except KeyboardInterrupt:
                    break
            return

        if self.path.endswith('.html') or self.path=="/":
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('<img src="http://127.0.0.1:8080/cam.mjpg"/>')
            self.wfile.write('</body></html>')
            return

# Two steps to starting the HTTP service
# first instantiate the sevice with a handler for the HTTP GET
# then place the serve_forever call into a thread so we don't block here
print("Waiting for CamServer to start...")

# Redirect port 80 to 8080
# keeping us legal on the field (i.e., requires 80)
# AND eliminating the need to start this script as root
cmd = ['sudo iptables -t nat -D PREROUTING 1']
call(cmd,shell=True)
cmd = ['sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8080']
call(cmd,shell=True)
cmd = ['sudo iptables -t nat -D PREROUTING 2']
call(cmd,shell=True)
cmd = ['sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port 8080']
call(cmd,shell=True)

camHttpServer = HTTPServer(('',8080),CamHTTPHandler)
camServer = BucketServer("CamServer", camHttpServer).start()

while (camServer.isStopped() == True):
    time.sleep(0.001)

print("CamServer appears online!")
bvTable.putString("BucketVisionState","ONLINE")

runTime = 0
bvTable.putNumber("BucketVisionTime",runTime)
nextTime = time.time() + 1

while (True):

    if (time.time() > nextTime):
        nextTime = nextTime + 1
        runTime = runTime + 1
        bvTable.putNumber("BucketVisionTime",runTime)

    if (frontCamMode.value == 'gearLift'):
        frontProcessor.updateSelection('gearLift')
        frontCam.updateExposure(FRONT_CAM_GEAR_EXPOSURE)
    elif (frontCamMode.value == 'Boiler'):
        frontProcessor.updateSelection(alliance.value + "Boiler")
        frontCam.updateExposure(FRONT_CAM_NORMAL_EXPOSURE)

    # Monitor network tables for commands to relay to processors and servers
    key = cv2.waitKey(100)

    if (frontCam.processUserCommand(key) == True):
        break
        
# NOTE: NOTE: NOTE:
# Sometimes the exit gets messed up, but for now we just don't care

#stop the bucket server and processors

frontProcessor.stop()      # stop this first to make the server exit


print("Waiting for BucketProcessors to stop...")
while ((frontProcessor.isStopped() == False)):
    time.sleep(0.001)
print("BucketProcessors appear to have stopped.")

camServer.stop()
print("Waiting for CamServer to stop...")
while (camServer.isStopped() == False):
    time.sleep(0.001)
print("CamServer appears to have stopped.")


#stop the camera capture
frontCam.stop()

print("Waiting for BucketCaptures to stop...")
while ((frontCam.isStopped() == False)):
    time.sleep(0.001)
print("BucketCaptures appears to have stopped.")
 
# do a bit of cleanup
cv2.destroyAllWindows()

print("Goodbye!")

