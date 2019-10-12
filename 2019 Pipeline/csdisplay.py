from threading import Thread
from configs   import configs
from cscore    import CameraServer
import logging
import time
import cv2

class CSDisplay(Thread):

    def __init__(self, source=None, stream_name="Camera0", res=None, network_table=None):
        self.logger = logging.getLogger("CSDisplay")
        self.stream_name = stream_name
        self.source = source

        if res is not None:
            self.output_width = res[0]
            self.output_height = res[1]
        else:
            self.output_width = int(self.source.width)
            self.output_height = int(self.source.height)

        self._fps    = configs['serverfps']
        self._colors = configs['MarkingColors']

        cs = CameraServer.getInstance()
        self.outstream = cs.putVideo(self.stream_name, self.output_width, self.output_height)

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

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        Thread.start(self)

    @staticmethod
    def NetTableVisionGet(net_table):
        array_keys = ('angle', 'parallax', 'distance', 'pos_x', 'pos_y', 'size')
        ret_data = dict()
        ret_data['LastFrameTime'] = net_table.getNumber("LastFrameTime", None)
        ret_data['CurrFrameTime'] = net_table.getNumber("CurrFrameTime", None)
        ret_data['NumTargets'] = int(net_table.getNumber("NumTargets", 0))
        for key in array_keys:
            ret_data[key] = net_table.getNumberArray(key, None)
        return ret_data

    def drawtargets(self, image):
        if self.net_table is None:
            return image
        if self.net_table.getBoolean('Overlay', False):
            return image

        height, width, _ = image.shape
        targets = self.NetTableVisionGet(self.net_table)
        print("CSD: looping {}".format(targets['NumTargets']))
        for index in range(targets['NumTargets']):
            try:
                color = self._colors[index]
                x, y = targets['pos_x'][index], targets['pos_y'][index]
                image = cv2.circle(image, (int(x * width), int(y * height)),
                                    int((targets['size'][index] * width) / 4),
                                    color, -1)
            except IndexError:
                # More targets than colors!
                return image
        return image

    def write_table_value(self, name, value, level=logging.DEBUG):
        self.logger.log(level, "{}:{}".format(name, value))
        if self.net_table is None:
            self.net_table = dict()
        if type(self.net_table) is dict:
            self.net_table[name] = value
        else:
            self.net_table.putValue(name, value)

    def run(self):
        start_time = time.time()    # keep time to limit display fps
        last_fps_time = start_time  # keep time to calculate fps
        num_frames = 0              # fames displayed
        while not self.stopped:
            if self.source is None:
                if self._new_frame:
                    current_time = time.time()
                    if (current_time - start_time) >= (1.0/(self._fps+0.5)):      # limit display fps
                        start_time = current_time
                        self.outstream.putFrame(self._frame)
                        num_frames += 1
                        self._new_frame = False
            elif self.source.new_frame:
                current_time = time.time()
                if (current_time - start_time) >= (1.0/(self._fps+0.5)):
                    start_time = current_time
                    self.outstream.putFrame(self.source.frame)
                    num_frames +=1

            current_time = time.time()
            if (current_time - last_fps_time) >= 5.0:
                self.write_table_value("DisplayFPS", (num_frames/5.0))
                num_frames = 0
                last_fps_time = current_time

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sink = CSDisplay()
    sink.start()
    import cv2
    cam = cv2.VideoCapture(0)
    while True:
        ret_val, img = cam.read()
        sink.frame = img
        # Esc to quit
        if cv2.waitKey(1) == 27:
            break
    sink.stop()
