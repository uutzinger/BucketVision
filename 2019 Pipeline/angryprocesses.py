from   threading import Thread
import logging
import cv2
import time
from   processimage import ProcessImage
from   configs import configs

class AngryProcesses(Thread):
    def __init__(self, source=None, network_table=None, debug_label=""):
        self.logger = logging.getLogger("AngryProcesses")
        self.net_table = network_table
        self.source = source
        self.debug_label = debug_label

        self._frame = None
        self._new_frame = False
        self.new_frame = False
        self.last_frame_time = 0.0
        
        if self.net_table is not None:
            self.net_table.putNumber("LastFrameTime", 0.0)

        self.processor = ProcessImage()
        self.results = list()

        self.camera_res = configs['camera_res']

        self.stopped = True
        Thread.__init__(self)

    @property
    def frame(self):
        self.new_frame = False
        return self._frame

    @frame.setter
    def frame(self, img):
        self._frame = img
        self._new_frame = True

    @staticmethod
    def dict_zip(*dicts):
        all_keys = {k for d in dicts for k in d.keys()}
        return {k: [d[k] for d in dicts if k in d] for k in all_keys}

    def update_results(self):
        if self.net_table is not None:
            #last_net_time = float(self.net_table.getEntry("LastFrameTime").value)
            #if last_net_time >= self.last_frame_time:
                #print("\nAP: {}: net table ahead!".format(self.debug_label))
            #    return
            self.net_table.putNumber("LastFrameTime", self.last_frame_time)
            self.net_table.putNumber("CurrFrameTime", time.time())
            result_data = self.dict_zip(*[r.dict() for r in self.results])
            self.net_table.putNumber("NumTargets", len(self.results))
            for key, value in result_data.items():
                # Here we assume that every param is a number of some kind
                self.net_table.putNumberArray(key, value)

    def draw_trgt(self):
        if self.source is None:
            return self.processor.drawtargets(self.frame, self.results)
        else:
            return self.processor.drawtargets(self.source.frame, self.results)

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        if self.net_table is not None:
            self.net_table.putBoolean('Overlay', False)
        Thread.start(self)

    def run(self):
        Target_Timing_hist = list()
        start_time = time.time()
        num_frames = 0
        while not self.stopped:
            if self.source is not None:
                if self.source.new_frame:
                    self._new_frame = True
            if self._new_frame:
                if time.time() - start_time >= 5.0:
                    print("Targets processed:{}/s".format(num_frames/5.0))
                    num_frames = 0
                    start_time = time.time()
                self.last_frame_time = time.time()
                tmp_s = time.time()
                if self.source is not None:
                    frame = self.source.frame
                else:
                    frame = self.frame
                crop_top = int(self.camera_res[1]*configs['crop_top'])
                crop_bot = int(self.camera_res[1]*configs['crop_bot'])
                self.results = self.processor.FindTarget(frame[crop_top:crop_bot, :, :])
                Target_Timing_hist.append((time.time() - tmp_s))
                if len(Target_Timing_hist) >= 50:
                   print("Target detected in:{:.3f} ms".format(sum(Target_Timing_hist)/50.0))
                   Target_Timing_hist = list()
                if self.net_table is not None:
                    pass
                    # self.frame = self.draw_trgt()
                    # if self.net_table.getBoolean('Overlay', False):
                    #     self.frame = self.draw_trgt()
                    # elif self.source is None:
                    #    pass
                    # else:
                    #     self.frame = self.source.frame
                elif self.source is not None:
                    self.frame = self.source.frame
                else:
                    self.new_frame = True
                self.update_results()
                self._new_frame = False
                num_frames = num_frames + 1
                #print("\nAP: {} done at {}".format(self.debug_label, time.time()))

if __name__ == '__main__':
    from usbcapture import USBCapture
    from cv2display import Cv2Display
    logging.basicConfig(level=logging.DEBUG)

    print("Start Cam")

    cam = USBCapture(camera_num=0, exposure=-2)
    cam.start()

    print("Start Proc")

    proc = AngryProcesses(cam)
    proc.start()

    print("Start Display")

    sink = Cv2Display(source=proc)
    sink.start()

    print("Started Everything!")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        sink.stop()
        proc.stop()
        cam.stop()
