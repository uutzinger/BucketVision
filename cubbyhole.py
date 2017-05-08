'''
Created on Apr 3, 2017

@author: twilson

Thread-safe dropbox for passing frames between processing threads
'''

from threading import Condition


class Cubbyhole:
    def __init__(self):
        self.cond = Condition()
        self.avail = False
        self.frame = None
        
    def put(self, frame):
        self.cond.acquire()
        self.frame = frame
        self.avail = True
        self.cond.notify()
        self.cond.release()
        
    def get(self):
        self.cond.acquire()
        while not self.avail:
            self.cond.wait()
        frame = self.frame
        self.avail = False
        self.cond.release()
        return frame
    