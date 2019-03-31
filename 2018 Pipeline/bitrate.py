'''
Created on Apr 2, 2017

@author: twilson
'''
from stopwatch import StopWatch

class BitRate:
    def __init__(self):
        self._stopwatch = StopWatch()
        self._totBytes = 0
        self._numFrames = 0
        self._bitrate = 0.0
            
    def update(self, bytecnt):
        self._numFrames += 1
        self._totBytes += bytecnt
    
    # Returns bitrate in MBit/sec
    def get(self):
        if self._numFrames > 10 :
            totTime = self._stopwatch.stop()
            self._bitrate = (8*self._totBytes/totTime)/1.0e6
            
            self._numFrames = 0
            self._totBytes = 0
            self._stopwatch.start()
        
        return self._bitrate
            
        