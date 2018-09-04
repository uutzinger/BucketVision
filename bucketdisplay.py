import cv2
from threading import Thread

from framerate import FrameRate
from frameduration import FrameDuration

class BucketDisplay:
    def __init__(self, mode, cams, procs):
        print("Creating BucketDisplay")
        self.fps = FrameRate()
        self.duration = FrameDuration()
        self.mode = mode
        self.cams = cams
        self.procs = procs

        self._frame = None
        self.frame = None
        self.count = 0
        self.isNew = False
        
        # initialize the variable used to indicate if the thread should
        # be stopped
        self._stop = False
        self.stopped = True

        print("BucketDisplay created")
        
    def start(self):
        print("STARTING BucketDisplay")
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        print("BucketDisplay RUNNING")
        # keep looping infinitely until the thread is stopped
        self.stopped = False
        self.fps.start()
        
        while True:
            # if the thread indicator variable is set, stop the thread
            if (self._stop == True):
                self._stop = False
                self.stopped = True
                return

            try:
                camModeValue = mode.value
                cameraSelection = self.cams[camModeValue]
                processorSelection = self.procs[camModeValue]
            except:
                camModeValue = 'Default'
                cameraSelection = self.cams[list(self.cams.keys())[0]]
                processorSelection = self.procs[list(self.procs.keys())[0]]

            # otherwise, read the next frame from the stream
            # grab the frame from the threaded video stream
            
            (img, count, isNew) = processorSelection.read()
            self.duration.start()
            self.fps.update()

            if (isNew == True):

                camFps = cameraSelection.fps.fps()
                procFps = processorSelection.fps.fps()
                procDuration = processorSelection.duration.duration()

                cv2.putText(img,"{:.1f}".format(camFps),(0,20),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)
                if (procFps != 0.0):
                    cv2.putText(img,"{:.1f}".format(procFps) + " : {:.0f}".format(100 * procDuration * procFps) + "%",(0,40),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)
                cv2.putText(img,"{:.1f}".format(self.fps.fps()),(0,60),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)

                cv2.putText(img,camModeValue,(0, 80),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)
                cv2.putText(img,processorSelection.ipselection,(0,100),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),1)                

                cameraSelection.outstream.putFrame(img)
              
            self.duration.update()
                
        print("BucketDisplay for " + self.name + " STOPPING")
          
    def stop(self):
        # indicate that the thread should be stopped
        self._stop = True

    def isStopped(self):
        return self.stopped
		
