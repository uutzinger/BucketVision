from   threading import Thread
from   threading import Lock
import logging
import time
import os
import cv2
import numpy as np
import v4l2capture
import select
from   configs import configs
try:
    import networktables
except ImportError:
    pass

###############################################################
# Video for Linux 2 METHODS
# device=Video_device('\dev\video0')
###############################################################
#set_format
#   Request the video device to set image size and format. 
#   The device may choose another size than requested and will return its choice. 
#   The image format will be RGB24 if yuv420 is zero (default) or YUV420 if yuv420 is 1, 
#   if fourcc keyword is set that will be the fourcc pixel format used.
# Exposure Time
#set_exposure_auto
#   Request the video device to set auto exposure to value. 
#   The device may choose another value than requested and will return its choice.
#get_exposure_auto
#   Request the video device to get auto exposure value.
#set_exposure_absolute
#   Request the video device to set exposure time to value. 
#   The device may choose another value than requested and will return its choice. 
#get_exposure_absolute
#   Request the video device to get exposure time value.
##############################################################
# OPEN CLOSE AND BUFFERS
#start
#   Start video capture.
#stop
#   top video capture.
#create_buffers
#   Create buffers used for capturing image data. Can only be 
#   called once for each video device object.
#queue_all_buffers
#   Let the video device fill all buffers created. 
#read 
#   Reads image data from a buffer that has 
#   been filled by the video device.  The image data is in RGB 
#   or YUV420 format as decided by 'set_format'. The buffer 
#   is removed from the queue. Fails if no buffer is filled. 
#   Use select.select to check for filled buffers.
#read_and_queue
#   Same as 'read', but adds the buffer back to the queue so 
#   the video device can fill it again."
#close
#   Close video device. Subsequent calls to other methods will fail.
##############################################################
#
# SETTINGS
#fileno
#   This enables video devices to be passed select.select for waiting
#   until a frame is available for reading.
#get_info
#   Returns three strings with information about the video device,
#   and one set containing strings identifying the capabilities of the video device.
#get_fourcc
#   Return the fourcc string encoded as int.
#get_format
#   Request the current video format.
#set_fps
#   Request the video device to set frame per seconds.
#   The device may choose another frame rate than requested and will return its choice.
#set_auto_white_balance
#   Request the video device to set auto white balance to value. 
#   The device may choose another value than requested and will return its choice.
#get_auto_white_balance
#   Request the video device to get auto white balance value.
#set_white_balance_temperature
#   Request the video device to set white balance tempature to value. 
#   The device may choose another value than requested and will return its choice.
#get_white_balance_temperature
#   equest the video device to get white balance temperature value.
#set_focus_auto
#   Request the video device to set auto focuse on or off. 
#   The device may choose another value than requested and will return its choice.
#get_focus_auto
#   Request the video device to get auto focus value.
##############################################################
#set_auto_white_balance
#set_white_balance_temperature

class v4l2Capture(Thread):
    def __init__(self, camera_num=0, res=None, network_table=None, exposure=None, frate=None, fourcc=None):
        #
        self.logger     = logging.getLogger("v4l2Capture{}".format(camera_num))
        self.camera_num = camera_num
        self.net_table  = network_table
        # Threading Locks
        self.capture_lock = Lock()
        self.frame_lock   = Lock()
        #
        # Video 4 Linux 2
        #
        device = "/dev/video" + str(camera_num)
        exists = os.path.isfile(device)
        if exists:
            self.camera = v4l2capture.Video_device(device)
            self.camera_open = True
        else:
            self.camera_open = False
            self.write_table_value("Camera{}Status".format(camera_num), 
                                    "Failed to open camera {}!".format(device), 
                                    level=logging.CRITICAL)

        # Exposure Time
        if exposure is not None:  
            self._exposure = exposure
        else: self._exposure = configs['v4l2exposure']

        # Frame Rate
        if frate is not None:
            self._framerate = frate
        else: self._framerate = configs['v4l2framerate']

        # fourcc
        if fourcc is not None:  
            self._fourcc = fourcc
        else: self._fourcc = configs['v4l2fourcc']

        # Resolution
        # We will need to have valid fourcc to set resolution
        if res is not None:  
            self.resolution = res
        else: self.resolution = configs['camera_res']

        # Turn Off Auto Features
        self.exposure_auto = 0
        self.auto_white_balance = 0
        self.white_balance_temperature = 0
        self.focus_auto = 0

        # Set Exposure
        self.exposure = self._exposure
        # Set Framerate
        self.framerate = self._framerate

        # Buffer
        self.camera.create_buffers(10)

        # Send the buffer to the device. Some devices require this to be done
        # before calling 'start'.
        self.camera.queue_all_buffers()

        # Threading Locks
        self.capture_lock = Lock()
        self.frame_lock = Lock()

        self._frame = None
        self._new_frame = False

        self.stopped = True
        Thread.__init__(self)

    @property
    def new_frame(self):
        out = False
        with self.frame_lock:
            out = self._new_frame
        return out

    @new_frame.setter
    def new_frame(self, val):
        with self.frame_lock:
            self._new_frame = val

    @property
    def frame(self):
        with self.frame_lock:
            self._new_frame = False
        # For maximum thread (or process) safety, you should copy the frame, but this is very expensive
        return self._frame

    @property
    def resolution(self):
        if self.cap_open:
            with self.capture_lock:
                size_width, size_height, fourcc = self.camera.get_format()
                self._fourcc = fourcc
                return (size_width, size_height)
        else:
            return float("NaN")

    @resolution.setter
    def resolution(self, val):
        if val is None:
            return
        if self.cap_open:
            with self.capture_lock:
                size_width, size_height = self.camera.set_format(val[0], val[1], fourcc=self._fourcc)
            self.write_table_value("Width",  int(size_width))
            self.write_table_value("Height", int(size_height))
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set width to {}!".format(val),
                                    level=logging.CRITICAL)

    @property
    def exposure(self):
        return self._exposure

    @exposure.setter
    def exposure(self, val):
        if val is None:
            return
        val = int(val)
        if self.cap_open:
            self._exposure=self.camera.set_exposure_absolute(val)
            self.write_table_value("Exposure", self._exposure)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set exposure to {}!".format(val),
                                    level=logging.CRITICAL)

    @property
    def fourcc(self):
        return self._fourcc

    @fourcc.setter
    def fourcc(self, val):
        if val is None:
            return
        val = int(val)
        self._fourcc = val
        if self.cap_open:
            self.camera.set_format(self.resolution[0], self.resolution[1], fourcc=self._fourcc)
            self._fourcc=self.camera.get_fourcc()
            self.write_table_value("FourCC", self._fourcc)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set fourcc to {}!".format(self._fourcc),
                                    level=logging.CRITICAL)

    @property
    def framerate(self):
        return self._framerate

    @framerate.setter
    def framerate(self, val):
        if val is None:
            return
        val = int(val)
        self._framerate = val
        if self.cap_open:
            with self.capture_lock:
                self._framerate = self.camera.set_fps(self._framerate)
            self.write_table_value("Framerate", self._framerate)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set framerate to {}!".format(val),
                                    level=logging.CRITICAL)

    @property
    def exposure_auto(self):
        return self.camera.get_exposure_auto()

    @exposure_auto.setter
    def exposure_auto(self, val):
        if val is None:
            return
        val = int(val)
        if self.cap_open:
            with self.capture_lock:
                self.camera.set_exposure_auto(val)
            self.write_table_value("Exposure Auto", val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set exposure auto to {}!".format(val),
                                    level=logging.CRITICAL)

    @property
    def auto_white_balance(self):
        return self.camera.get_auto_white_balance()

    @auto_white_balance.setter
    def auto_white_balance(self, val):
        if val is None:
            return
        val = int(val)
        if self.cap_open:
            with self.capture_lock:
                self.camera.set_auto_white_balance(val)
            self.write_table_value("White Balance Auto", val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set auto white balance to {}!".format(val),
                                    level=logging.CRITICAL)

    @property
    def white_balance_temperature(self):
        return self.camera.get_white_balance_temperature()

    @white_balance_temperature.setter
    def white_balance_temperature(self, val):
        if val is None:
            return
        val = int(val)
        if self.cap_open:
            with self.capture_lock:
                self.camera.set_white_balance_temperature(val)
            self.write_table_value("White Balance Temperature", val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set white balance temperature to {}!".format(val),
                                    level=logging.CRITICAL)

    @property
    def focus_auto(self):
        return self.camera.get_focus_auto()

    @focus_auto.setter
    def focus_auto(self, val):
        if val is None:
            return
        val = int(val)
        if self.cap_open:
            with self.capture_lock:
                self.camera.set_focus_auto(val)
            self.write_table_value("Auto Focus", val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set auto focus to {}!".format(val),
                                    level=logging.CRITICAL)

    def write_table_value(self, name, value, level=logging.DEBUG):
        self.logger.log(level, "{}:{}".format(name, value))
        if self.net_table is None:
            self.net_table = dict()
        if type(self.net_table) is dict:
            self.net_table[name] = value
        else:
            self.net_table.putValue(name, value)

    def stop(self):
        self.stopped = True
        self.camera.stop()
        self.camera.close()

    def start(self):
        self.stopped = False
        self.camera.start()
        Thread.start(self)

    def run(self):
        first_frame = True
        frame_hist = list()
        start_time = time.time()
        num_frames = 0
        img = None
        while not self.stopped:
            if (time.time() - start_time) >= 5.0:
                print("Capture{}: {}fps".format(self.camera_num, num_frames/5.0))
                num_frames = 0
                start_time = time.time()
            try:
                if self._exposure != self.net_table.getEntry("Exposure").value:
                    self.exposure = self.net_table.getEntry("Exposure").value
            except: pass
            with self.capture_lock:
                select.select((camera,), (), ())
                frame = camera.read_and_queue()
                img = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), cv2.IMREAD_COLOR)
            with self.frame_lock:
                self._frame = img[int(self.camera_res[1]*(configs['crop_top'])):int(self.camera_res[1]*(configs['crop_bot'])), :, :]
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
    camera = v4l2Capture(camera_num=0, network_table=FrontCameraTable)
    camera.start()

    print("Getting Frames")
    while True:
        if camera.new_frame:
            cv2.imshow('my webcam', camera.frame)
        if cv2.waitKey(1) == 27:
            break  # esc to quit
    camera.stop()
