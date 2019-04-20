from threading import Thread
import logging
import cv2
import time
from configs import configs
try:
    import networktables
except ImportError:
    pass

class Cv2Display(Thread):
    def __init__(self, source=None, window_name="Camera0", network_table=None):
        self.logger = logging.getLogger("Cv2Display")
        self.window_name = window_name
        self.source = source

        self._fps = configs['serverfps']

        self._frame = None
        self._new_frame = False

        self.net_table = network_table

        self.stopped = True
        Thread.__init__(self)

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, img):
        self._frame = img
        self._new_frame = True

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
        Thread.start(self)

    def run(self):
        start_time = time.time()        # limit display fps
        last_fps_time = start_time      # keep time for fps measurement
        num_frames = 0                  # number of frames displayed
        while not self.stopped:
            if self.source is not None:
                if self.source.new_frame:
                   self.frame = self.source.frame
                    
            if self._new_frame:
                current_time = time.time()
                if (current_time - start_time) >= (1.0/(self._fps+0.5)):         # limit display fps
                    cv2.imshow(self.window_name, self._frame)
                    start_time =  current_time
                    num_frames += 1
                    self._new_frame = False
                
            current_time = time.time()
            if (current_time - last_fps_time) >= 5.0:               # compute fps every 5 secs
                self.write_table_value("DisplayFPS", (num_frames/5.0))
                num_frames = 0
                last_fps_time = current_time

            cv2.waitKey(1)
        cv2.destroyAllWindows()

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
