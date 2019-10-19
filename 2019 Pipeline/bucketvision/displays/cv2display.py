###############################################################################
#                                                                             #
# file:    cv2display.py                                                      #
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
from   threading import Thread
import logging
import time
import cv2
from   networktables import NetworkTables

from   bucketvision.configs import configs

###############################################################################
# Video Display
###############################################################################
class Cv2Display(Thread):
    """
    This displays output to a cv2 window (i.e. you are testing locally)
    """
    def __init__(self, source=None, window_name="Camera0", res=None, network_table=None):
        self.logger = logging.getLogger("Cv2Display")
        self.window_name = window_name
        self.source = source
        self.net_table = network_table

        if res is not None:
            self.output_width = res[0]
            self.output_height = res[1]
        else:
            self.output_width = int(self.source.width)
            self.output_height = int(self.source.height)

        self.fps     = configs['serverfps']       # max display fps
        self._colors = configs['MarkingColors']

        self._frame = None                     # clear frame storage
        self._new_frame = False                # no new frame yet

        self.stopped = True                    # prepare for continous running
        Thread.__init__(self)

    ###############################################################################
    # Setting
    # frame, fps
    ###############################################################################

    @property
    def frame(self):
        self._new_frame = False
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

    @staticmethod
    def NetTableVisionGet(net_table):
        array_keys = ('angle', 'parallax', 'distance', 'pos_x', 'pos_y', 'size')
        ret_data = dict()
        ret_data['LastFrameTime'] = net_table.getNumber("LastFrameTime", None)
        ret_data['CurrFrameTime'] = net_table.getNumber("CurrFrameTime", None)
        ret_data['NumTargets']    = int(net_table.getNumber("NumTargets", 0))
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

        for index in range(targets['NumTargets']):
            found_cont = [np.int0(cv2.boxPoints(r)) for r in [target.l_rect.raw_rect, target.r_rect.raw_rect]]
            try:
                color = self.colors[index]
                # mark the center of the target with solid circle
                x, y = targets['pos_x'][index], targets['pos_y'][index]
                x_screen = int(x * width)
                y_screen = int(Y * height)
                circle_radius = int((targetx['size'][index] * width) / 8)
                image = cv2.circle(image, (x_screen, y_screen), circle_radius, color, -1)
                # enable distance and parallax display if within range
                if (tagets['distance'][index] < self.target_dist_max) and (targets['distance'][index] > self.target_dist_min):
                    # distance and parallax circle (red circle)                                   
                    # bold distance circle if within range
                    circle_radius = (height * 10.0 / targets['distance'][index]) / 100
                    offset = int(targets['parallax'][index] * width / 200) 
                    if (abs(targets['distance'][index] - self.target_dist) < 0.2) :
                        image = cv2.circle(image, (x_screen - offset,y_screen), circle_radius, (0,0,255), 10)
                    else:
                        image = cv2.circle(image, (x_screen - offset,y_screen), circle_radius, (0,0,255), 2)
                    # Desired target distance reference circle 
                    circle_radius = (height * 10.0 / self.target_dist / 100
                    image = cv2.circle(image, (x_screen,y_screen), circle_radius, color, 2)
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

    ###############################################################################
    # Thread establishing and running
    ###############################################################################

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        Thread.start(self)

    def run(self):
        start_time = time.time()        # limit display fps
        last_fps_time = start_time      # keep time for fps measurement
        num_imgs = 0                    # number of frames displayed

        while not self.stopped:
            current_time = time.time()
            if (current_time - start_time) >= (1.0/(self._fps+0.5)): # limit display fps
                start_time =  current_time
                if self.source is not None:
                    if self.source.new_frame:
                        self.frame = self.source.frame # get picture from grabbed frame
                    if self._new_frame:
                        self._new_frame = False
                        img = self.frame
                        img = drawtargets(img)         # mark targets
                        cv2.imshow(self.window_name, img)
                        num_imgs +=1

            if (current_time - last_fps_time) >= 5.0:                    # compute fps every 5 secs
                self.write_table_value("DisplayFPS", (num_imgs/5))
                num_imgs/5 = 0
                last_fps_time = current_time

            cv2.waitKey(1) # wait at least 1ms
            
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
