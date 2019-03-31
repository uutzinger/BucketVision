'''
Created on Mar 27, 2017

@author: twilson
'''
import time

class StopWatch:
    def __init__(self):
        self._start = time.time()
    
    def start(self):
        self._start = time.time()
        
    def stop(self):
        return time.time() - self._start
        