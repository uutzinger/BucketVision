# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 20:46:25 2017

Thread that gets frames from a camera
It *is* OK to use one Camera in multiple Processors
"""
## NOTE: OpenCV interface to camera controls is sketchy
## use v4l2-ctl directly for explicit control
## example for dark picture: v4l2-ctl -c exposure_auto=1 -c exposure_absolute=10


import cv2
from subprocess import call
from threading import Thread
from threading import Lock
from framerate import FrameRate
from cubbyhole import Cubbyhole
import platform


        
class Camera:
    def __init__(self, name, src, width, height, exposure):

        print("Creating Camera " + name)
        
        self.name = name
        self.src = src
                
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH,width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT,height)

        self.exposure = None
        self.setExposure(exposure)
        
        self.fps = FrameRate()
        self.running = False
        
        # Dict maps user (client) to the Cubbyhole instance used to pass it frames
        self.userDict = {}
        self.userDictLock = Lock() # Protects shared access to userDict
        

        self.rate = self.stream.get(cv2.CAP_PROP_FPS)
        print("RATE = " + str(self.rate))
        self.brightness = self.stream.get(cv2.CAP_PROP_BRIGHTNESS)
        print("BRIGHT = " + str(self.brightness))
        self.contrast = self.stream.get(cv2.CAP_PROP_CONTRAST)
        print("CONTRAST = " + str(self.contrast))
        self.saturation = self.stream.get(cv2.CAP_PROP_SATURATION)
        print("SATURATION = " + str(self.saturation))
        print("EXPOSURE = " + str(self.exposure))
        


    def start(self):
        print("Camera  " + self.name + " STARTING")
        t = Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return self

    def run(self):
        print("Camera " + self.name + " RUNNING")
        self.running = True
        
        
        while True:

            (grabbed, frame) = self.stream.read()
            
            self.fps.start()
                    
            # grabbed will be false if camera has been disconnected.
            # How to deal with that??
            # Should probably try to reconnect somehow? Don't know how...
                
            if grabbed:
                # Pass a copy of the frame to each user in userDict
                self.userDictLock.acquire()
                values = self.userDict.values()
                self.userDictLock.release()
                for mb in values:
                    mb.put(frame.copy())
            
            self.fps.stop()

                
    def read(self, user):
        # See if this user already registered in userDict.
        # If not, create a new Cubbyhole instance to pass frames to user.
        # If so, just get the user's Cubbyhole instance.
        # Then get the frame from the Cubbyhole & return it.
        self.userDictLock.acquire()
        if not user in self.userDict:
            self.userDict[user] = Cubbyhole()
        mb = self.userDict[user]
        self.userDictLock.release()
        
        return mb.get()     

    def processUserCommand(self, key):
        if key == ord('w'):
            self.brightness+=1
            self.stream.set(cv2.CAP_PROP_BRIGHTNESS,self.brightness)
            print("BRIGHT = " + str(self.brightness))
        elif key == ord('s'):
            self.brightness-=1
            self.stream.set(cv2.CAP_PROP_BRIGHTNESS,self.brightness)
            print("BRIGHT = " + str(self.brightness))
        elif key == ord('d'):
            self.contrast+=1
            self.stream.set(cv2.CAP_PROP_CONTRAST,self.contrast)
            print("CONTRAST = " + str(self.contrast))
        elif key == ord('a'):
            self.contrast-=1
            self.stream.set(cv2.CAP_PROP_CONTRAST,self.contrast)
            print("CONTRAST = " + str(self.contrast))
        elif key == ord('e'):
            self.saturation+=1
            self.stream.set(cv2.CAP_PROP_SATURATION,self.saturation)
            print("SATURATION = " + str(self.saturation))
        elif key == ord('q'):
            self.saturation-=1
            self.stream.set(cv2.CAP_PROP_SATURATION,self.saturation)
            print("SATURATION = " + str(self.saturation))
        elif key == ord('z'):
            self.setExposure(self.exposure+1)
            print("EXPOSURE = " + str(self.exposure))
        elif key == ord('c'):
            self.setExposure(self.exposure-1)
            print("EXPOSURE = " + str(self.exposure))
            
##        elif key == ord('p'):
##            self.iso +=1
##            self.stream.set(cv2.CAP_PROP_ISO_SPEED, self.iso)
##        elif key == ord('i'):
##            self.iso -=1
##            self.stream.set(cv2.CAP_PROP_ISO_SPEED, self.iso)


    def setExposure(self, exposure):
                    
        if self.exposure == exposure :
            return
        
        self.exposure = exposure
        
        # cv2 exposure control DOES NOT WORK ON PI
        if (platform.system() == 'Windows' or platform.system() == 'Darwin'):
            self.stream.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
        else:
            cmd = ['v4l2-ctl --device=' + str(self.src) + ' -c exposure_auto=1 -c exposure_absolute=' + str(self.exposure)]
            call(cmd,shell=True)
                
        return
    
    
    def isRunning(self):
        return self.running

