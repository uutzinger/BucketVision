# -*- coding: utf-8 -*-
"""
bucketvision

Many hands make light work!
A multi-threaded vision pipeline example for Bit Buckets Robotics that
looks like a bucket brigade

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

import time

# import our classes

from framerate import FrameRate

from bucketcapture import BucketCapture     # Camera capture threads... may rename this
from imageprocessor import ImageProcessor   # Image processing threads... has same basic structure (may merge classes)

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

from faces import Faces             # Useful for basic testing of driverCam/Processor pipeline

# And so it begins
print("Starting BUCKET VISION!")

# NOTE: NOTE: NOTE:
#
# YOUR MILEAGE WILL VARY
# The exposure values are camera/driver dependent and have no well defined standard (i.e., non-portable)
# Our implementation is forced to use v4l2-ctl (Linux) to make the exposure control work because our OpenCV
# port does not seem to play well with the exposure settings (produces either no answer or causes errors depending
# on the camera used)
bucketCam = BucketCapture(name="bucketCam",src=0,width=320,height=240,exposure=100).start()

print("Waiting for BucketCapture to start...")
while (bucketCam.isStopped() == True):
    time.sleep(0.001)

print("BucketCapture appears online!")

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

faces = Faces()

# NOTE: NOTE: NOTE
#
# Reminder that each image processor should process exactly one vision pipeline
# at a time (it can be selectable in the future) and that the same vision
# pipeline should NOT be sent to different image processors as this is simply
# confusing and can cause some comingling of data (depending on how the vision
# pipeline was defined... we can't control the use of object-specific internals
# being run from multiple threads... so don't do it!)

bucketProcessor = ImageProcessor(bucketCam,faces).start()

print("Waiting for ImageProcessors to start...")
while (bucketProcessor.isStopped() == True):
    time.sleep(0.001)

print("ImageProcessors appear online!")

# Continue feeding display or streams in foreground told to stop
fps = FrameRate()   # Keep track of display rate  TODO: Thread that too!
fps.start()

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
while (True):
    # grab the frame from the image processor
    (bucketFrame, count, isNew) = bucketProcessor.read()

    # check to see if the frame should be displayed to our screen
    # For now, just show every new frame
    if (isNew == True):
         camFps = bucketCam.fps.fps()
         procFps = bucketProcessor.fps.fps()
         procDuration = bucketProcessor.duration.duration()

         cv2.putText(bucketFrame,"{:.1f}".format(camFps),(0,40),cv2.FONT_HERSHEY_PLAIN,2,(0,255,0),2)
         if (procFps != 0.0):
             cv2.putText(bucketFrame,"{:.1f}".format(procFps) + " : {:.0f}".format(100 * procDuration * procFps) + "%",(0,80),cv2.FONT_HERSHEY_PLAIN,2,(0,255,0),2)
         cv2.putText(bucketFrame,"{:.1f}".format(fps.fps()),(0,120),cv2.FONT_HERSHEY_PLAIN,2,(0,255,0),2)

         cv2.imshow("bucketCam", bucketFrame)

         key = cv2.waitKey(1) & 0xFF
         
         if (bucketCam.processUserCommand(key) == True):
             break
            
    # update the display FPS counter (in this case it will be roughly the rate of the slowest pipeline because
    # we are displaying both pipelines in the same thread (again because I just don't feel like messing
    # with the extra steps to make X11 behave
    fps.update()


# NOTE: NOTE: NOTE:
# Sometimes the exit gets messed up, but for now we just don't care

#stop the image processors
bucketProcessor.stop()

print("Waiting for ImageProcessors to stop...")
while (bucketProcessor.isStopped() == False):
    time.sleep(0.001)

#stop the camera capture
bucketCam.stop()

print("Waiting for BucketCapture to stop...")
while (bucketCam.isStopped() == False):
    time.sleep(0.001)
 
# do a bit of cleanup
cv2.destroyAllWindows()

print("Goodbye!")

