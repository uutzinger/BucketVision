from   threading    import Thread
import logging
import time

import cv2

from   bucketvision.postprocessors.processimage import ProcessImage
from   bucketvision.configs                     import configs

class AngryProcesses(Thread):
    """
    The AngryProcessor takes a source that has been resized and uses ProcessImage() to
    find and draw a target on the output before sending it to NetworkTables
    """
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
            #   print("\nAP: {}: net table ahead!".format(self.debug_label))
            #   return
            self.net_table.putNumber("LastFrameTime", self.last_frame_time)
            self.net_table.putNumber("CurrFrameTime", time.time())
            result_data = self.dict_zip(*[r.dict() for r in self.results])
            self.net_table.putNumber("NumTargets", len(self.results))
            for key, value in result_data.items():
                # Here we assume that every param is a number of some kind
                self.net_table.putNumberArray(key, value)

    def write_table_value(self, name, value, level=logging.DEBUG):
        self.logger.log(level, "{}:{}".format(name, value))
        if self.net_table is None:
            self.net_table = dict()
        if type(self.net_table) is dict:
            self.net_table[name] = value
        else:
            self.net_table.putValue(name, value)

    def draw_targets(self):
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
        Target_Timing_hist = list() # Records the time it took to find targets for 50 frames
        start_time = time.time()    # Keeps track of loop timing
        num_frames = 0              # How many frames do we process in 5s
        while not self.stopped:
            if self.source is not None:
                if self.source.new_frame:
                    self._new_frame = True
            #continue
            if self._new_frame:
                # How many frames do we pass through the pipeline?
                if time.time() - start_time >= 5.0:
                    self.write_table_value("TargetFramesProcessedPS", num_frames/5.0 )
                    num_frames = 0
                    start_time = time.time()
                self.last_frame_time = time.time()

                # Find the target in cropped image
                time_target_start = time.time()
                crop_top = int(self.camera_res[1]*configs['crop_top'])
                crop_bot = int(self.camera_res[1]*configs['crop_bot'])
                if self.source is not None:
                    self.results, self.timings = self.processor.FindTarget(self.source.frame[crop_top:crop_bot, :, :])
                else:
                    self.results, self.timings = self.processor.FindTarget(self.frame[crop_top:crop_bot, :, :])

                # How long did it take?
                Target_Timing_hist.append((time.time() - time_target_start))
                if len(Target_Timing_hist) >= 50:
                   self.write_table_value("TargetProcessingTime", sum(Target_Timing_hist)/50.0 )
                   Target_Timing_hist = list()

                # Draw targets if requested
                if self.net_table is not None:
                    if self.net_table.getBoolean('Overlay', True):
                        # Adjust for cropping
                        self.frame[crop_top:crop_bot, :, :] = self.draw_targets(self.frame[crop_top:crop_bot, :, :], self.results)
                elif self.source is not None:
                    self.frame = self.source.frame
                else:
                    self.new_frame = True
                    
                self.update_results()
                self._new_frame = False
                num_frames = num_frames + 1

if __name__ == '__main__':
    from bucketvision.capturers.cv2capture import Cv2Capture
    from bucketvision.diplays.cv2display   import Cv2Display
    
    logging.basicConfig(level=logging.DEBUG)

    print("Start Cam")

    cam = Cv2Capture(camera_num=0, exposure=-2)
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
