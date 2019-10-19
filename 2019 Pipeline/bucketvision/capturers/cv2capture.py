# Multi Threading
from   threading import Thread
from   threading import Lock
#
import logging
import time
import os
import cv2

from   bucketvision.configs   import configs

try:
    import networktables
except ImportError:
    pass

class Cv2Capture(Thread):
    """
    This thread continually captures frames from a USB camera
    """
    def __init__(self, camera_num=0, res=None, network_table=None, exposure=None):
        self.logger = logging.getLogger("Cv2Capture2Capture{}".format(camera_num))
        self.camera_num = camera_num
        self.net_table = network_table

        # Threading Locks
        self.capture_lock = Lock()
        self.frame_lock = Lock()

        if exposure is not None:
            self._exposure = exposure
        else:
            self._exposure = configs['exposure']
                
        if res is not None:
            self.camera_res = res
        else:
            self.camera_res = (configs['res'])

        if os.name == 'nt':
            self.cap = cv2.VideoCapture(self.camera_num, apiPreference = cv2.CAP_DSHOW )
        else:
            self.cap = cv2.VideoCapture(self.camera_num, apiPreference = cv2.CAP_V4L2 )

        self.cap_open = self.cap.isOpened()
        if self.cap_open is False:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to open camera {}!".format(self.camera_num),
                                    level=logging.CRITICAL)

        self.fourcc     =     configs['fourcc']
        self.fps        =     configs['fps'] 
        self.buffersize = int(configs['buffersize'])

        # Init Frame and Thread   
        self._frame = None
        self._new_frame = False
        self.stopped = True
        Thread.__init__(self)

    #
    # Frame routines ##################################################
    #
    @property
    # reads more recentframe
    def new_frame(self):
        with self.frame_lock:
            out = self._new_frame
        return out

    @new_frame.setter
    # check if new frame available
    def new_frame(self, val):
        with self.frame_lock:
            self._new_frame = val

    @property
    # sets wether new frame is available
    def frame(self):
        with self.frame_lock:
            self._new_frame = False
        return self._frame



    @property
    def width(self):
        if self.cap_open:
            with self.capture_lock:
                return self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        else:
            return float("NaN")

    @width.setter
    def width(self, val):
        if val is None:
            return
        if self.cap_open:
            with self.capture_lock:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(val))
            self.write_table_value("Width", int(val))
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set width to {}!".format(val),
                                    level=logging.CRITICAL)
    @property
    def height(self):
        if self.cap_open:
            with self.capture_lock:
                return self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        else:
            return float("NaN")

    @height.setter
    def height(self, val):
        if val is None:
            return
        if self.cap_open:
            with self.capture_lock:
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(val))
            self.write_table_value("Height", int(val))
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set height to {}!".format(val),
                                    level=logging.CRITICAL)

    @property
    def exposure(self):
        return self._exposure

    @exposure.setter
    def exposure(self, val):
        if val is None:
            return
        val = int(val)
        self._exposure = val
        if self.cap_open:
            with self.capture_lock:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # must disable auto exposure explicitly on some platforms
                self.cap.set(cv2.CAP_PROP_EXPOSURE, val)
            self.write_table_value("Exposure", val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set exposure to {}!".format(val),
                                    level=logging.CRITICAL)

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, val):
        if val is None:
            return
        self._fps = val
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_FPS, self._fps):
                    self._fps = self.cap.get(cv2.CAP_PROP_FPS)
                    self.write_table_value("FPS", self._fps)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set FPS to {}!".format(val),
                            level=logging.CRITICAL)

    @property
    def fourcc(self):
        return self._fourcc

    @fourcc.setter
    def fourcc(self, val):
        if val is None:
            return
        self._fourcc = val
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(self._fourcc[0],self._fourcc[1],self._fourcc[2],self._fourcc[3])):
                    self.write_table_value("FOURCC", self._fourcc)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set FOURCC to {}!".format(val),
                            level=logging.CRITICAL)

    @property
    def buffersize(self):
        return self._buffersize

    @buffersize.setter
    def buffersize(self, val):
        if val is None:
            return
        self._buffersize = val
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self._buffersize):
                    self.write_table_value("Buffersize", self._buffersize)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set Buffer Size to {}!".format(val),
                            level=logging.CRITICAL)

    #
    # Network Table routines ##########################################
    #

    def write_table_value(self, name, value, level=logging.DEBUG):
        self.logger.log(level, "{}:{}".format(name, value))
        if self.net_table is None:
            self.net_table = dict()
        if type(self.net_table) is dict:
            self.net_table[name] = value
        else:
            self.net_table.putValue(name, value)

    #
    # Thread routines #################################################
    #

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        self.width = self.camera_res[0]
        self.height = self.camera_res[1]
        if self._exposure is None:
            self.exposure = self.exposure
        else:
            self.exposure = self._exposure
        Thread.start(self)

    def run(self):
        first_frame = True
        start_time = time.time()
        num_frames = 0
        while not self.stopped:
            current_time = time.time()
            if (current_time - start_time) >= 5.0:
                self.write_table_value("CaptureFPS", num_frames/5.0)
                # print("Capture{}: {}fps".format(self.camera_num, num_frames/5.0))
                num_frames = 0
                start_time = current_time
            
            try:
                if self._exposure != self.net_table.getEntry("Exposure").value:
                    self.exposure = self.net_table.getEntry("Exposure").value
                pass
            except: 
                pass
            
            with self.capture_lock:
                _, img = self.cap.read()
                with self.frame_lock:
                    self._frame = img
                    if first_frame:
                        first_frame = False
                        print(img.shape, self._frame.shape)
                    self._new_frame = True
                num_frames = num_frames + 1

if __name__ == '__main__':
    import os
    from networktables import NetworkTables
    logging.basicConfig(level=logging.DEBUG)

    NetworkTables.initialize(server='localhost')

    VisionTable = NetworkTables.getTable("BucketVision")
    VisionTable.putString("BucketVisionState", "Starting")
    FrontCameraTable = VisionTable.getSubTable('FrontCamera')

    print("Starting Capture")
    camera = Cv2Capture(camera_num=0, res=(320,240), network_table=FrontCameraTable)
    camera.start()

    print("Getting Frames")
    while True:
        if camera.new_frame:
            cv2.imshow('my webcam', camera.frame)
        if cv2.waitKey(1) == 27:
            break  # esc to quit
    camera.stop()
