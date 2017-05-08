# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 20:46:25 2017

@author: mtkes
"""

from stopwatch import StopWatch

class FrameRate:
    def __init__(self):
        self._totalWatch = StopWatch()
        self._busyWatch = StopWatch()
        self._busyTime = 0.0
        self._numFrames = 0
        self._fps = 0.0
        self._util = 0.0

    def start(self):
        self._busyWatch.start()

        
    def stop(self):
        self._busyTime += self._busyWatch.stop()
        self._numFrames += 1


    def get(self):
        if (self._numFrames > 10):
            
            totalTime = self._totalWatch.stop()
            self._fps = self._numFrames/totalTime
            self._util = self._busyTime/totalTime
            
            self._totalWatch.start()
            self._numFrames = 0
            self._busyTime = 0.0           
            
        return self._fps, self._util


