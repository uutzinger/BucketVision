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
from   threading import Thread
from   threading import Lock
import logging
import time
import os
# Vision
import cv2
# FIRST
import networktables
# 4183
from   configs import configs

###############################################################################
# Video Capture
###############################################################################
class Cv2Capture(Thread):
    def __init__(self, camera_num=0, res=None, network_table=None, exposure=None):
        self.logger     = logging.getLogger("Cv2Capture{}".format(camera_num))
        self.camera_num = camera_num
        self.net_table  = network_table

        # Threading Locks
        self.capture_lock = Lock()      # To lock the capure device
        self.frame_lock = Lock()        # To lock the measured frame

        # Realtime Changing Variables
        if exposure is not None: self._exposure = exposure
        else:                    self._exposure = configs['exposure']

        # Configure at Boot
        if res is not None: self.camera_res = res
        else:               self.camera_res = (configs['res'])

        self.crop_top = int(self.camera_res[1]*(configs['crop_top']))
        self.crop_bot = int(self.camera_res[1]*(configs['crop_bot']))

        # apiPreferneces are:
        # CAP_ANY, CAP_VFW (video for windows) Windows counterpart for quicktime, 1991-1995
        # CAP_V4L, CAP_V4L2 (video for linux), 2002-2016
        # CAP_FIREWIRE (firewire)
        # CAP_QT (Quicktime), 1991-2016 no longer supported on windows
        # CAP_DSHOW (direct show) most commonly used windows media interface, repalced by MSMF
        # CAP_OPENNI (Kinect), now openni2
        # CAP_MSMF (Microsoft Media Foundation) most recent MS effort for media interfacing 
        # CAP_GSTREAMER (Gstreamer) 2001-current
        # CAP_FFMPEG, 
        # CAP_OPENCV_MJPEG
        # https://docs.opencv.org/4.1.0/d4/d15/group__videoio__flags__base.html

        if os.name == 'nt': self.cap = cv2.VideoCapture(self.camera_num, apiPreference = cv2.CAP_MSMF )
        else:               self.cap = cv2.VideoCapture(self.camera_num, apiPreference = cv2.CAP_V4L2 )

        self.cap_open = self.cap.isOpened()
        if self.cap_open is False:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to open camera {}!".format(self.camera_num),
                                    level=logging.CRITICAL)

        try: self.fourcc       =   str(configs['fourcc'])
        except: pass
        try: self.fps          = float(configs['fps']) 
        except: pass
        try: self.buffersize   =   int(configs['buffersize'])
        except: pass
        try: self.autoexposure =   int(configs['autoexposure'])
        except: pass
        try: self.autowhite    =   int(configs['autowhite'])
        except: pass
        try: self.whitetemp    =   int(configs['whitetemp'])
        except: pass
        try: self.autofocus    =   int(configs['autofocus'])
        except: pass
            
        self._frame = None
        self._new_frame = False

        self.stopped = True
        Thread.__init__(self)

###############################################################################
# Setting
# fourcc, fps, buffersize, width, height, exposure
###############################################################################

   # read if new frame available
    @property
    def new_frame(self):
        with self.frame_lock:
            return self._new_frame

    # set new frame indicator to true or false 
    @new_frame.setter
    def new_frame(self, val):
        with self.frame_lock:
            self._new_frame = val

    # read latest frame
    @property
    def frame(self):
        with self.frame_lock:
            self._new_frame = False     # The _frame is read and therefore not new anymore
        return self._frame

    # write to latest frame
    @frame.setter
    def frame(self, val):
        with self.frame_lock:
            self._frame = val
            self._new_frame = True

    # capture frame width
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
    # capture frame height
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
    def exposure(self): return self._exposure

    @exposure.setter
    def exposure(self, val):
        if val is None:
            return
        val = int(val)
        self._exposure = int(val)
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
    def fps(self): return self._fps

    @fps.setter
    def fps(self, val):
        if val is None:
            return
        self._fps = float(val)
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
    def fourcc(self): return self._fourcc

    @fourcc.setter
    def fourcc(self, val):
        if val is None:
            return
        self._fourcc = str(val)
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(self._fourcc[0],self._fourcc[1],self._fourcc[2],self._fourcc[3])):
                    self.write_table_value("FOURCC", self._fourcc)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set FOURCC to {}!".format(val),
                            level=logging.CRITICAL)

    @property
    def buffersize(self): return self._buffersize

    @buffersize.setter
    def buffersize(self, val):
        if val is None:
            return
        self._buffersize = int(val)
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self._buffersize):
                    self.write_table_value("Buffersize", self._buffersize)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set Buffer Size to {}!".format(val),
                            level=logging.CRITICAL)

    @property
    def autoexposure(self): return self._autoexposure

    @autoexposure.setter
    def autoexposure(self, val):
        if val is None:
            return
        self._autoexposure = int(val)
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, self._autoexposure):
                    self.write_table_value("Autoexposure", self._autoexposure)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set Auto Exposure to {}!".format(val),
                            level=logging.CRITICAL)

    @property
    def autowhite(self): return self._autowhite

    @autowhite.setter
    def autowhite(self, val):
        if val is None:
            return
        self._autowhite = bool(val)
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_AUTO_WB, self._autowhite):
                    self.write_table_value("AutoWB", self._autowhite)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set Auto White Balance to {}!".format(val),
                            level=logging.CRITICAL)

    @property
    def whitetemp(self): return self._whitetemp

    @whitetemp.setter
    def whitetemp(self, val):
        if val is None:
            return
        self._whitetemp = int(val)
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, self._whitetemp):
                    self.write_table_value("WBtemperature", self._whitetemp)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set White Balance Temperature to {}!".format(val),
                            level=logging.CRITICAL)

    @property
    def autofocus(self): return self._autofocus

    @autofocus.setter
    def autofocus(self, val):
        if val is None:
            return
        self._autofocus = bool(val)
        if self.cap_open:
            with self.capture_lock:
                if self.cap.set(cv2.CAP_PROP_AUTOFOCUS, self._autofocus):
                    self.write_table_value("AutoFocus", self._autofocus)
                else:
                    self.write_table_value("Camera{}Status".format(self.camera_num),
                            "Failed to set Auto Focus to {}!".format(val),
                            level=logging.CRITICAL)

###############################################################################

    def write_table_value(self, name, value, level=logging.DEBUG):
        self.logger.log(level, "{}:{}".format(name, value))
        if self.net_table is None:        self.net_table = dict()
        if type(self.net_table) is dict:  self.net_table[name] = value
        else:                             self.net_table.putValue(name, value)

###############################################################################
# Thread Establishing and Running
###############################################################################

    def stop(self): self.stopped = True

    def start(self):
        self.stopped  = False
        self.width    = self.camera_res[0]
        self.height   = self.camera_res[1]
        self.exposure = self._exposure
        Thread.start(self)

    def run(self):
        start_time = time.time()
        num_frames = 0
        img = None
        while not self.stopped:
            with self.capture_lock: _, img = self.cap.read()
            self.frame = img[self.crop_top:self.crop_bot, :, :]
            num_frames += 1
            if (time.time() - start_time) >= 5.0:
                self.write_table_value("CaptureFPS" + str(self.camera_num), num_frames/5.0)
                num_frames = 0
                start_time = time.time()

            try:
                if self.exposure != self.net_table.getEntry("Exposure").value:
                    self.exposure = self.net_table.getEntry("Exposure").value
            except: pass

###############################################################################
# Testing
###############################################################################

if __name__ == '__main__':
    import os
    from networktables import NetworkTables
    logging.basicConfig(level=logging.DEBUG)

    print("Network Tables")
    NetworkTables.initialize(server='localhost')
    VisionTable = NetworkTables.getTable("BucketVision")
    VisionTable.putString("BucketVisionState", "Starting")
    FrontCameraTable = VisionTable.getSubTable('FrontCamera')

    print("Starting Capture")
    camera = Cv2Capture(camera_num=0, res=(320,240), network_table=FrontCameraTable)
    camera.start()

    print("Getting Frames")
    while True:
        if camera.new_frame:      cv2.imshow('my webcam', camera.frame) #
        if cv2.waitKey(1) == 27:  break                                 # esc to quit
    camera.stop()
