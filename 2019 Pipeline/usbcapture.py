from   threading import Thread
from   threading import Lock
import logging
import time
import os
import cv2
from configs import configs
try:
    import networktables
except ImportError:
    pass

class USBCapture(Thread):
    def __init__(self, camera_num=0, res=(640, 480), network_table=None, exposure=None):
        self.logger = logging.getLogger("USBCapture{}".format(camera_num))
        self.camera_num = camera_num
        self.net_table = network_table

        # first vars
        self._exposure = exposure

        self.cap = cv2.VideoCapture()
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        self.cap.open(self.camera_num)
        self.cap_open = self.cap.isOpened()
        if self.cap_open is False:
            self.cap_open = False
            self.write_table_value("Camera{}Status".format(camera_num),
                                    "Failed to open camera {}!".format(camera_num),
                                    level=logging.CRITICAL)

        if res is not None:
            self.camera_res = res
        else:
            self.camera_res = (self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Threading Locks
        self.capture_lock = Lock()
        self.frame_lock = Lock()

        self._frame = None
        self._new_frame = False

        self.stopped = True
        self.exposure = exposure
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
                if os.name == 'nt':
                    #self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # must disable auto exposure explicitly on some platforms
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, val)
                else:
                    os.system("v4l2-ctl -c exposure_absolute={}".format(val))
                    print("Exposure set to: {}".format(val))
            self.write_table_value("Exposure", val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num),
                                    "Failed to set exposure to {}!".format(val),
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
        frame_hist = list()
        start_time = time.time()
        num_frames = 0
        img = None
        while not self.stopped:
            if (time.time() - start_time) >= 5.0:
                print("Capture{}: {}fps".format(self.camera_num, num_frames/5.0))
                num_frames = 0
                start_time = time.time()
            # TODO: Make this less crust, I would like to setup a callback
            try:
                if self._exposure != self.net_table.getEntry("Exposure").value:
                    self.exposure = self.net_table.getEntry("Exposure").value
            except: pass
            with self.capture_lock:
                _, img = self.cap.read()
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
    camera = USBCapture(network_table=FrontCameraTable)
    camera.start()

    os.system("v4l2-ctl -c exposure_absolute={}".format(configs['exposure']))

    print("Getting Frames")
    while True:
        if camera.new_frame:
            cv2.imshow('my webcam', camera.frame)
        if cv2.waitKey(1) == 27:
            break  # esc to quit
    camera.stop()
