'''
Thread that wraps & runs a GRIP/OpenCV processing pipeline
'''

import cv2
from threading import Thread
from threading import Lock
from cubbyhole import Cubbyhole

from framerate import FrameRate

class Processor:
    def __init__(self, name, camera, pipeline):
        print("Creating Processor: camera=" + camera.name + " pipeline=" + pipeline.name)
        
        self.name = name
        self.camera = camera
        
        # Lock to protect access to pipeline member var
        self.lock = Lock()
        self.pipeline = pipeline
        
        self.cubby = Cubbyhole()
        self.fps = FrameRate()
        
        self.running = False

        
    def start(self):
        print("Processor " + self.name + " STARTING")
        t = Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return self

    def run(self):
        print("Processor " + self.name + " RUNNING")
        self.running = True
       
        while True:

            frame = self.camera.read(self)
            
            self.fps.start()

            self.lock.acquire()
            pipeline = self.pipeline
            self.lock.release()
            
            pipeline.process(frame)
            self.cubby.put(frame)

            self.fps.stop()
            
                

    def setPipeline(self, pipeline):
        if pipeline == self.pipeline:
            return
        
        self.lock.acquire()
        self.pipeline = pipeline
        self.lock.release()
        print( "Processor " + self.name + " pipeline now=" + pipeline.name)

    def read(self):
        return self.cubby.get()
          

    def isRunning(self):
        return self.running

