###############################################################################
#                                                                             #
# file:    .py                                                                #
#                                                                             #
# authors: BitBuckets FRC 4183                                                #
#                                                                             #
# date:    April 1st 2019                                                     #
#                                                                             #
# brief:                                                                      #
#                                                                             #
###############################################################################

###############################################################################
# Imports
###############################################################################
# Execution
from threading import Thread
import logging
import time
# Computer Vision
import cv2
# FIRST
from networktables import NetworkTables
# 4183
from configs import configs

###############################################################################
# Video Display
###############################################################################
class Cv2Display(Thread):
    def __init__(self, source=None, window_name="Camera0", network_table=None):
        self.logger = logging.getLogger("Cv2Display")
        self.window_name = window_name
        self.source = source
        self.fps = configs['serverfps']          # max fps for video server
        self._frame = None                       # clear frame storage
        self._new_frame = False                  # no new images yet
        self.net_table = network_table
        self.stopped = True                      # prepapre for continues running
        Thread.__init__(self)

###############################################################################
# Setting
# fps, frame
###############################################################################

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, img):
        self._frame = img
        self._new_frame = True

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, fps):
        self._fps = fps

###############################################################################

    def write_table_value(self, name, value, level=logging.DEBUG):
        self.logger.log(level, "{}:{}".format(name, value))
        if self.net_table is None:
            self.net_table = dict()
        if type(self.net_table) is dict:
            self.net_table[name] = value
        else:
            self.net_table.putValue(name, value)

###############################################################################
# Thread Establishing and Running
###############################################################################

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        Thread.start(self)

    def run(self):
        start_time = time.time()        # limit display fps
        last_fps_time = start_time      # keep time for fps measurement
        num_frames = 0                  # number of frames displayed
        while not self.stopped:
            if self.source is not None:
                if self.source.new_frame:
                   self.frame = self.source.frame # get pictre from grabbed frame
                    
            if self._new_frame:
                current_time = time.time()
                if (current_time - start_time) >= (1.0/(self.fps+0.5)):         # limit display fps
                    cv2.imshow(self.window_name, self._frame)
                    start_time =  current_time
                    num_frames += 1
                    self._new_frame = False
                
            current_time = time.time()
            if (current_time - last_fps_time) >= 5.0:                          # compute fps every 5 secs
                self.write_table_value("DisplayFPS", (num_frames/5.0))
                num_frames = 0
                last_fps_time = current_time

            cv2.waitKey(1)
        cv2.destroyAllWindows()

###############################################################################
# Testing
###############################################################################

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    sink = Cv2Display()
    sink.start()

    cam = cv2.VideoCapture(0)
    while True:
        ret_val, img = cam.read()
        sink.frame = img
        # Esc to quit
        if cv2.waitKey(1) == 27:
            break
