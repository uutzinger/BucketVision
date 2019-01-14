# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 20:46:25 2017

@author: mtkes
"""
## NOTE: OpenCV interface to camera controls is sketchy
## use v4l2-ctl directly for explicit control
## example for dark picture: v4l2-ctl -c exposure_auto=1 -c exposure_absolute=10

# import the necessary packages

import cv2

from cscore import CameraServer
from cscore import VideoMode

from subprocess import call
from threading import Lock
from threading import Thread
from threading import Condition

import numpy as np

import platform

# import our classes

from framerate import FrameRate
from frameduration import FrameDuration

class BucketCapture:
    def __init__(self,name,src,width,height,exposure):

        print("Creating BucketCapture for " + name)
        
        self._lock = Lock()
        self._condition = Condition()
        self.fps = FrameRate()
        self.duration = FrameDuration()
        self.name = name
        self.exposure = exposure
        self.src = src
        self.width = width
        self.height = height
            
        # initialize the variable used to indicate if the thread should
        # be stopped
        self._stop = False
        self.stopped = True

        self.grabbed = False
        self.frame = None
        self.outFrame = None
        self.count = 0
        self.outCount = self.count

        print("BucketCapture created for " + self.name)

    def start(self):

        
        # start the thread to read frames from the video stream
        print("STARTING BucketCapture for " + self.name)
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        print("BucketCapture for " + self.name + " RUNNING")

        # keep looping infinitely until the thread is stopped
        self.stopped = False
        self.fps.start()

        lastExposure = self.exposure

        cs = CameraServer.getInstance()
        cs.enableLogging()

        self.camera = cs.startAutomaticCapture(dev=self.src)

        self.camera.setResolution(self.width, self.height)
        self.camera.setPixelFormat(VideoMode.PixelFormat.kYUYV)
        self.camera.setFPS(150)
        self.camera.setExposureManual(self.exposure);
        p = self.camera.enumerateVideoModes()
        for pi in p:
            print(pi.fps, pi.height, pi.width, pi.pixelFormat)
            
        #self.camera.setExposureManual(0)
        #self.camera.setBrightness(100)

        # Get a CvSink. This will capture images from the camera
        cvSink = cs.getVideo()

        # (optional) Setup a CvSource. This will send images back to the Dashboard
        self.outstream = cs.putVideo(self.name, self.width, self.height)

        # Allocating new images is very expensive, always try to preallocate
        img = np.zeros(shape=(self.height, self.width, 3), dtype=np.uint8)    

        while True:
            # if the thread indicator variable is set, stop the thread
            if (self._stop == True):
                self._stop = False
                self.stopped = True
                return
            
            if (lastExposure != self.exposure):
                self.setExposure()
                lastExposure = self.exposure
                
            # Tell the CvSink to grab a frame from the camera and put it
            # in the source image.  If there is an error notify the output.
            time, img = cvSink.grabFrame(img)
            if time == 0:
                self._grabbed = False
                # Send the output the error.
                self.outstream.notifyError(cvSink.getError());
                # skip the rest of the current iteration
                continue

            self._grabbed = True                
            
            self.duration.start()
            self.fps.update()
            
            
            # if something was grabbed and retreived then lock
            # the outboundw buffer for the update
            # This limits the blocking to just the copy operations
            # later we may consider a queue or double buffer to
            # minimize blocking
            if (self._grabbed == True):
                self._condition.acquire()
                self._lock.acquire()
                self.count = self.count + 1
                self.grabbed = self._grabbed
                self.frame = img.copy()
                self._lock.release()
                self._condition.notifyAll()
                self._condition.release()

            self.duration.update()

                
        print("BucketCapture for " + self.name + " STOPPING")

    def read(self):
        # return the frame most recently read if the frame
        # is not being updated at this exact moment
        self._condition.acquire()
        self._condition.wait()
        self._condition.release()
        if (self._lock.acquire() == True):
            self.outFrame = self.frame
            self.outCount = self.count
            self._lock.release()
            return (self.outFrame, self.outCount, True)
        else:
            return (self.outFrame, self.outCount, False)

##    def processUserCommand(self, key):
##        if key == ord('x'):
##            return True
##        elif key == ord('w'):
##            self.brightness+=1
##            self.stream.set(cv2.CAP_PROP_BRIGHTNESS,self.brightness)
##            print("BRIGHT = " + str(self.brightness))
##        elif key == ord('s'):
##            self.brightness-=1
##            self.stream.set(cv2.CAP_PROP_BRIGHTNESS,self.brightness)
##            print("BRIGHT = " + str(self.brightness))
##        elif key == ord('d'):
##            self.contrast+=1
##            self.stream.set(cv2.CAP_PROP_CONTRAST,self.contrast)
##            print("CONTRAST = " + str(self.contrast))
##        elif key == ord('a'):
##            self.contrast-=1
##            self.stream.set(cv2.CAP_PROP_CONTRAST,self.contrast)
##            print("CONTRAST = " + str(self.contrast))
##        elif key == ord('e'):
##            self.saturation+=1
##            self.stream.set(cv2.CAP_PROP_SATURATION,self.saturation)
##            print("SATURATION = " + str(self.saturation))
##        elif key == ord('q'):
##            self.saturation-=1
##            self.stream.set(cv2.CAP_PROP_SATURATION,self.saturation)
##            print("SATURATION = " + str(self.saturation))
##        elif key == ord('z'):
##            self.exposure+=1
##            setExposure(self.exposure)
##            print("EXPOSURE = " + str(self.exposure))
##        elif key == ord('c'):
##            self.exposure-=1
##            setExposure(self.exposure)
##            print("EXPOSURE = " + str(self.exposure))
####        elif key == ord('p'):
####            self.iso +=1
####            self.stream.set(cv2.CAP_PROP_ISO_SPEED, self.iso)
####        elif key == ord('i'):
####            self.iso -=1
####            self.stream.set(cv2.CAP_PROP_ISO_SPEED, self.iso)
##
##        return False

    def updateExposure(self, exposure):
        self.exposure = exposure
        
    def setExposure(self):
        self.camera.setExposureManual(self.exposure);
        pass
    
    def stop(self):
        # indicate that the thread should be stopped
        self._stop = True
        self._condition.acquire()
        self._condition.notifyAll()
        self._condition.release()

    def isStopped(self):
        return self.stopped

