
from threading import Lock
from threading import Thread
from threading import Condition

from framerate import FrameRate
from frameduration import FrameDuration

class ImageProcessor:
    def __init__(self,stream,ip):
        print("Creating ImageProcessor for " + stream.name)
        self._lock = Lock()
        self._condition = Condition()
        self.fps = FrameRate()
        self.duration = FrameDuration()
        self.stream = stream
        self.ip = ip

        (self._frame, self.count, self.isNew) = self.stream.read()

        if (self.isNew == True):
            self.count = 1
            self.frame = self._frame
        else:
            self.frame = None
            self.count = 0
        
        # initialize the variable used to indicate if the thread should
        # be stopped
        self._stop = False
        self.stopped = True

        print("ImageProcessor created for " + self.stream.name)
        
    def start(self):
        print("STARTING ImageProcessor for " + self.stream.name)
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        print("ImageProcessor for " + self.stream.name + " RUNNING")
        # keep looping infinitely until the thread is stopped
        self.stopped = False
        self.fps.start()
        
        while True:
            # if the thread indicator variable is set, stop the thread
            if (self._stop == True):
                self._stop = False
                self.stopped = True
                return

            # otherwise, read the next frame from the stream
            # grab the frame from the threaded video stream
            (self._frame, count, isNew) = self.stream.read()
            self.duration.start()
            self.fps.update()

            if (isNew == True):
                # TODO: Insert processing code then forward display changes
                self.ip.process(self._frame)
                
                # Now that image processing is complete, place results
                # into an outgoing buffer to be grabbed at the convenience
                # of the reader
                self._condition.acquire()
                self._lock.acquire()
                self.count = self.count + 1
                self.isNew = isNew
                self.frame = self._frame
                self._lock.release()
                self._condition.notifyAll()
                self._condition.release()

            self.duration.update()
                
        print("ImageProcessor for " + self.stream.name + " STOPPING")

    def read(self):
        # return the frame most recently processed if the frame
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
          
    def stop(self):
        # indicate that the thread should be stopped
        self._stop = True
        self._condition.acquire()
        self._condition.notifyAll()
        self._condition.release()

    def isStopped(self):
        return self.stopped
		
