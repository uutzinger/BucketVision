import math
import os
import numpy as np
import cv2

from   bucketvision.configs import configs

def display_scaled_image(name, image, scale):
    """Function to display a scaled cv2 image
    :param name:
        Window name
    :type name:
        basestring
    :param image:
        Image as numpy array
    :type image:
        numpy.ndarray
    :param scale:
        Scale factor applied to image
    :type scale:
        float
    """
    height, width = image.shape[:2]
    cv2.imshow(name, cv2.resize(image,
            (int(scale * width), int(scale * height)),
            interpolation=cv2.INTER_CUBIC))


def point_dist(a, b):
    x_1, y_1 = a
    x_2, y_2 = b
    return math.sqrt((x_1 - x_2) ** 2 + (y_1 - y_2) ** 2)


class Point(object):
    def __init__(self, x, y=None):
        """
        Point class, is a point
        :param x: x pos (normally in mm)
        :param y: y pos (normally in mm)

        -- or --

        :param x: (x, y) pos tuple
        """
        if y is None:
            self.x = x[0]
            self.y = x[0]
        else:
            self.x = x
            self.y = y
    
    def dist(self, point):
        """
        Caculates the distance to the selected point
        :param point: Another point
        :type point: Point
        :return: Distance
        :rtype: float
        """
        return math.sqrt((self.x - point.x)**2 + (self.y - point.y)**2)

    def angle(self, point):
        delta_x = self.x - point.x
        delta_y = self.y - point.y
        return math.atan2(delta_y, delta_x)


class RotatedRect(object):
    def __init__(self, rect):
        self.raw_rect   = rect
        self.center_pos = Point(rect[0][0], rect[0][1])
        self.width      = min(rect[1])
        self.height     = max(rect[1])
        self.angle      = rect[2]

    @property
    def ratio(self):
        """ Returns the ratio, always greater than 1 """
        return self.height / self.width


class VisionTarget(object):
    # Data from 4.10 Vision Tragets
    # a pair of 5½ in. (~14 cm) long by 2 in. (~5 cm) wide strips
    rect_height = 5.5
    rect_height_m = rect_height * 0.0254
    rect_width = 2
    rect_aspect_ratio = rect_height / rect_width
    angle = 90 - (2 * 14.5)  # angled toward each other at ~14.5 degrees
    center_cap = 11.31  # calculalted based on specs

    camera_hfov = configs['fov']            # degrees
    camera_hres = configs['camera_res'][0]  # pixels
    camera_vres = configs['camera_res'][1]  # pixels
    camera_px_per_deg = camera_hres / camera_hfov

    def __init__(self, left_rect, right_rect):
        self.l_rect = RotatedRect(left_rect)
        self.r_rect = RotatedRect(right_rect)
        
    @property
    def angle(self):
        """Angle from target 1 to 2"""
        return self.l_rect.center_pos.angle(self.r_rect.center_pos)

    @property
    def parallax(self):
        """
        unitless parallax between the left and right strips,
        returns Nan if we think one of the rectangles is covered
        negative if we are on the right side of the target
        "should" be invariant of the distance to target
        """
        
        # aspect_tol = 0.1

        # Check left rect ratio
        #if not (1 - aspect_tol) * self.rect_aspect_ratio < self.l_rect.ratio:
        #    return float('NaN')

        # Check right rect ratio
        #if not (1 - aspect_tol) * self.rect_aspect_ratio < self.r_rect.ratio:
        #    return float('NaN')

        return (1000 * (self.l_rect.height - self.r_rect.height)) / (self.l_rect.height + self.r_rect.height)

    @property
    def distance(self):
        """
        returns an estimated distance to target in meters
        """
        pixel_height = (self.l_rect.height + self.r_rect.height) / 2.0
        angle = pixel_height / self.camera_px_per_deg
        dist_m = self.rect_height_m / math.tan(math.radians(angle))
        return dist_m

    @property
    def pos(self):
        """
        returns the position as a tuple (x, y) from 0 to 1
        the origin is in the top left of the image (like OpenCV)
        """
        pos_pix_x = (self.l_rect.center_pos.x + self.r_rect.center_pos.x) / 2.0
        pos_pix_y = (self.l_rect.center_pos.y + self.r_rect.center_pos.y) / 2.0

        return pos_pix_x / self.camera_hres, pos_pix_y / self.camera_vres

    @property
    def size(self):
        """
        returns the distance between the targets as a fraction of the image width (from 0 to 1)
        """
        return self.l_rect.center_pos.dist(self.r_rect.center_pos) / self.camera_hres

    def dict(self):
        """
        Returns a dict of important features about the vision target
        """
        return {
            'angle': self.angle,
            'parallax': self.parallax,
            'distance': self.distance,
            'pos_x': self.pos[0],
            'pos_y': self.pos[1],
            'size': self.size
        }


class ProcessImage(object):
    """
    Searches for rectangles
    Pairs rectangles to target
    Returns Position, Distance and Angle to target
    """
    def __init__(self):
        (self.cv2major, self.cv2minor, _) = cv2.__version__.split(".")
        self.HSV_Top          = configs['HSV_Top']
        self.HSV_Bot          = configs['HSV_Bot']
        self.Min_Rect_Area    = configs['Min_Area']
        self.Max_Trgt_Ratio   = configs['MaxTargetRatio']
        self.Rect_Ratio_Limit = configs['RectRatioLimit']
        self.Min_Ang          = configs['MinAngle']
        self.Max_Ang          = configs['MaxAngle']        
        self.colors           = configs['MarkingColors']
        
    def FindTarget(self, image):
        height, width, _ = image.shape
        image_area = height * width

        # Convert BGR to HSV 
        # 7,4,12,13,13,6,6,8 ms
        e1 = cv2.getTickCount()
        HSV_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # HSV threshold 
        # 12,7,5,6,6,6,6,11 ms
        e2 = cv2.getTickCount()
        threshold = cv2.inRange(HSV_image, self.HSV_Top, self.HSV_Bot)

        # Find Contours 
        # 252, 76, 141, 48, 114
        e3 = cv2.getTickCount()
        if self.cv2major == '4':
            contours, _    = cv2.findContours(threshold, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
        else:
            _, contours, _ = cv2.findContours(threshold, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
        # print("proc:{}contoures".format(len(contours)))
        
        # Filter Contours that are smaller than threshold 
        # 46, 41, 0.1, 17
        e4 = cv2.getTickCount()
        c_contours = list() # candidate objects
        for contour in contours:
            contour_area = cv2.contourArea(contour)
            if contour_area > (self.Min_Rect_Area * image_area):
                c_contours.append(contour)

        # Convert min area rect 
        # 0.1
        # 109, 127, 106, 86, 146, 115, 47, 141
        e5 = cv2.getTickCount()
        min_rectangles = [cv2.minAreaRect(contour) for contour in c_contours]

        # Filter Rectangles, and classify as left (leaning right) or right (leaning left)
        # 0.5, 0.01 0.5
        e6 = cv2.getTickCount()
        right_rect = list()
        left_rect = list()
        for rect in min_rectangles:
            width, height = rect[1]
            rect_area = width * height
            # Filter small (relative to image) rects
            if rect_area / image_area < self.Min_Rect_Area:
                continue

            # Filter things that are too long and skinny
            if max(width, height) / min(width, height) > self.Rect_Ratio_Limit:
                continue

            # Classify if we are looking at a right or left rectangle
            if abs(rect[2]) < 45:
                right_rect.append(rect)
            else:
                left_rect.append(rect)

        rect_pairs = list()

        # Pair rects (based on the left rects) 
        # 0.5ms 0.7
        e7 = cv2.getTickCount()
        for l_rect in left_rect:
            found_match = False
            l_x, l_y = l_rect[0]
            l_width, l_height = l_rect[1]

            for r_index, r_rect in enumerate(right_rect):
                dist = point_dist(l_rect[0], r_rect[0])
                # Get some properties
                r_x, r_y = r_rect[0]
                r_width, r_height = r_rect[1]

                # Check if the left rectangle is right of the current right rectangle (this means it cannot be valid)
                if r_x < l_x:
                    continue

                # Check if the dist between points vs the rectangle height is too large
                if dist / max(l_width, l_height) > self.Max_Trgt_Ratio:
                    continue

                # Check if the angle between the targets is around the right value
                if not (self.Min_Ang < abs(l_rect[2]) - abs(r_rect[2]) < self.Max_Ang):
                    continue

                # If we got this far we found a match!
                found_match = True
                break

            if found_match:
                rect_pairs.append([l_rect, r_rect])
                del right_rect[r_index]

        found_targets = [VisionTarget(t[0], t[1]) for t in rect_pairs]
        
        e8 = cv2.getTickCount()
        #print("Time consumed for Target Detection:{}".format((e11  - e1)/cv2.getTickFrequency()))
        #print ("Color             ", (e2 - e1)/cv2.getTickFrequency())
        #print ("Threshold         ", (e3 - e2)/cv2.getTickFrequency())
        #print ("A Contours        ", (e4 - e3)/cv2.getTickFrequency())
        #print ("A Contour Filter  ", (e5 - e4)/cv2.getTickFrequency())
        #print ("Min Area Rectangle", (e6 - e5)/cv2.getTickFrequency())
        #print ("Filter Rectangles ", (e7 - e6)/cv2.getTickFrequency())
        #print ("Pair Rectangles   ", (e8 - e7)/cv2.getTickFrequency())
        tmp_scale  = cv2.getTickFrequency()
        t_color             = (e2 - e1)/tmp_scale
        t_thresh            = (e3 - e2)/tmp_scale
        t_contours          = (e4 - e3)/tmp_scale
        t_contour_filter    = (e5 - e4)/tmp_scale
        t_min_area_rect     = (e6 - e5)/tmp_scale
        t_filter_rectangles = (e7 - e6)/tmp_scale
        t_pair_rectangles   = (e8 - e7)/tmp_scale
        
        return found_targets, [t_color, t_thresh, t_contours, t_contour_filter, t_min_area_rect, t_filter_rectanglest t_pair_rectangles]

    @staticmethod
    def drawtargets(image, targets):
        height, width, _ = image.shape
        for index, target in enumerate(targets):
            found_cont = [np.int0(cv2.boxPoints(r)) for r in [target.l_rect.raw_rect, target.r_rect.raw_rect]]
            try:
                # mark the target
                color = ProcessImage.colors[index]
                image = cv2.drawContours(image, found_cont, -1, color, 3)
            except IndexError:
                # More targets than colors!
                pass
        return image


def live_video():
    import os
    from configs import configs
    import time
    proc = ProcessImage()

    cam = cv2.VideoCapture(0)
    frame_width = 320
    frame_height = 240
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    if os.name == 'nt':
        cam.set(cv2.CAP_PROP_EXPOSURE, -10)
    else:
        os.system("v4l2-ctl -c exposure_absolute={}".format(10))
    frame_time = list()
    while True:
        start = time.time()
        if len(frame_time) == 10:
            print("FPS:{}".format(1/sum(frame_time)))
            frame_time = list()
        ret_val, img = cam.read()
        camera_res = img.shape
        img = img[int(camera_res[1]*(configs['crop_top'])):int(camera_res[1]*(configs['crop_bot'])), :, :]
        res, _ = proc.FindTarget(img)
        display_scaled_image('test', proc.drawtargets(img, res), 1)
        if cv2.waitKey(1) == 27:
            break  # esc to quit
        frame_time.append(time.time() - start)
    cam.release()
    cv2.destroyAllWindows()

def single_image(image_path):
    proc = ProcessImage()
    img = cv2.imread(image_path)
    found_targets, _ = proc.FindTarget(img)
    img = proc.drawtargets(img, found_targets)
    if len(found_targets) > 0:
        pass
        # print(found_targets[-1].l_rect.raw_rect)
    display_scaled_image('test', img, 0.5)


if __name__ == '__main__':
    # live_video()
    # exit()
    folder = 'D:/GitHub/Python Playground/BucketVision/2019 Pipeline'
    files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    images = [f for f in files if f.endswith(".png")]
    for image in images:
        # print(image)
        single_image(image)
        cv2.waitKey(20)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
