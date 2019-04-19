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
###############################################################
#width, height = 
#set_format(width, height, yuv420 = 0, fourcc='MJPEG)
#   Request the video device to set image size and format. 
#   The device may choose another size than requested and will return its choice. 
#   The image format will be RGB24 if yuv420 is zero (default) or YUV420 if yuv420 is 1, 
#   if fourcc keyword is set that will be the fourcc pixel format used.
#width, height, fourcc = 
#get_format()
#   Request current format
#autoexp = 
#set_exposure_auto(autoexp)
#   Request the video device to set auto exposure to value. 
#   The device may choose another value than requested and will return its choice.
#   0=auto, 1=manual, 2=shutter priority, 3=aperture priority
#autoexp = 
#get_exposure_auto()
#   Request the video device to get auto exposure value.
#exposure = 
#set_exposure_absolute(exposure)
#   Request the video device to set exposure time to value. 
#   The device may choose another value than requested and will return its choice. 
#   1=100micro seconds, max=frame interval
#exposure = 
#get_exposure_absolute()
#   Request the video device to get exposure time value.
##############################################################
# OPEN CLOSE AND BUFFERS
#start()
#   Start video capture.
#stop()
#   top video capture.
#create_buffers(count)
#   Create buffers used for capturing image data. Can only be 
#   called once for each video device object.
#queue_all_buffers()
#   Let the video device fill all buffers created. 
#read()
#   Reads image data from a buffer that has 
#   been filled by the video device.  The image data is in RGB 
#   or YUV420 format as decided by 'set_format'. The buffer 
#   is removed from the queue. Fails if no buffer is filled. 
#   Use select.select to check for filled buffers.
#read_and_queue()
#   Same as 'read', but adds the buffer back to the queue so 
#   the video device can fill it again."
#close()
#   Close video device. Subsequent calls to other methods will fail.
##############################################################
# SETTINGS
#fileno = 
#fileno()
#   This enables video devices to be passed select.select for waiting
#   until a frame is available for reading.
#driver, card, bus_info, capabilities = 
#get_info()
#   Returns three strings with information about the video device,
#   and one set containing strings identifying the capabilities of the video device.
#fourcc_int = 
#get_fourcc(fourcc_string)
#   Return the fourcc string encoded as int.
#fps = 
#set_fps(fps)
#   Request the video device to set frame per seconds.
#   The device may choose another frame rate than requested and will return its choice.
#autowb = 
#set_auto_white_balance(autowb)
#   Request the video device to set auto white balance to value. 
#   The device may choose another value than requested and will return its choice.
#   autowb is 0, 1 bool
#autowb = 
#get_auto_white_balance()
#   Request the video device to get auto white balance value.
#temp = 
#set_white_balance_temperature(temp)
#   Request the video device to set white balance tempature to value. 
#   min=800 max=6500 step=1 default=57343
#   The device may choose another value than requested and will return its choice.
#temp = 
#get_white_balance_temperature()
#   equest the video device to get white balance temperature value.
#auto_focus = 
#set_focus_auto(auto_focus)
#   Request the video device to set auto focuse on or off. 
#   The device may choose another value than requested and will return its choice.
#   auto_focus 0 or 1 bool
#auto_focus = 
#get_focus_auto()
#   Request the video device to get auto focus value.
##############################################################

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
        exists = os.path.exists(device)
        if exists:
            self.camera = v4l2capture.Video_device(device)
            self.camera_open = True
        else:
            self.camera_open = False
            self.write_table_value("Camera{}Status".format(camera_num), 
                                    "Failed to open camera {}!".format(device), 
                                    level=logging.CRITICAL)

        # Settings that are not yet applied

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

        # Lets Apply All settings
        
        # Turn Off Auto Features
        self.exposure_auto = 1 # manual
        self.auto_white_balance = 0
        self.white_balance_temperature = 57343
        self.focus_auto = 0 # Off
        # Resolution
        # This will also apply fourcc
        if res is not None:  
            self.resolution = res
        else: self.resolution = configs['camera_res']

        # Set Exposure
        self.exposure = self._exposure
        # Set Framerate
        self.framerate = self._framerate

        # Prepare Buffers and Camera
       
        # Buffer
        self.camera.create_buffers(10)
        # Send the buffer to the device. 
        self.camera.queue_all_buffers()

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
        if self.camera_open:
            with self.capture_lock:
                width, height, fourcc = self.camera.get_format()
                self._fourcc = fourcc
                return (width, height)
        else:
            return float("NaN")

    @resolution.setter
    def resolution(self, val):
        if val is None:
            return
        if self.camera_open:
            with self.capture_lock:
                width, height = self.camera.set_format(val[0], val[1], yuv420 = 0, fourcc=self._fourcc)
            self.write_table_value("Width",  int(width))
            self.write_table_value("Height", int(height))
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
        if self.camera_open:
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
        self._fourcc = val
        if self.camera_open:
            width, height, fourcc = get_format()
            self.camera.set_format(width, height, yuv420 = 0, fourcc=self._fourcc)
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
        self._framerate = val
        if self.camera_open:
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
        if self.camera_open:
            with self.capture_lock:
                exposure_auto = self.camera.set_exposure_auto(val)
            self.write_table_value("Exposure Auto", exposure_auto)
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
        if self.camera_open:
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
        if self.camera_open:
            with self.capture_lock:
                temp = self.camera.set_white_balance_temperature(val)
            self.write_table_value("White Balance Temperature", temp)
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
        val = bool(val)
        if self.camera_open:
            with self.capture_lock:
                auto_focus= self.camera.set_focus_auto(val)
            self.write_table_value("Auto Focus", auto_focus)
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
