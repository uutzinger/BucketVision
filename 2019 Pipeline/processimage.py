import math
import os

import numpy as np
import cv2


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
		:param y: y pos (normally in mm
		"""
		if len(x) is 2:
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
		self.raw_rect = rect
		self.center_pos = Point(rect[0])
		self.width = min(rect[1])
		self.height = max(rect[1])
		self.angle = rect[2]


class VisionTarget(object):
	def __init__(self, left_rect, right_rect):
		self.l_rect = RotatedRect(left_rect)
		self.r_rect = RotatedRect(right_rect)

	@property
	def angle(self):
		"""Angle from target 1 to 2"""
		return self.l_rect.center_pos.angle(self.r_rect.center_pos)


class ProcessImage(object):
	HSV_Top = (49, 0, 48)
	HSV_Bot = (91, 255, 255)
	Min_Rect_Area = 0.0001
	Max_Trgt_Ratio = 3
	Rect_Ratio_Limit = 6
	Min_Ang = 50
	Max_Ang = 75

	colors = [
		(75, 25, 230),
		(25, 225, 255),
		(200, 130, 0),
		(48, 130, 245),
		(240, 240, 70),
		(230, 50, 240),
		(190, 190, 250),
		(128, 128, 0),
		(255, 190, 230),
		(40, 110, 170),
		(200, 250, 255),
		(0, 0, 128),
		(195, 255, 170),
		(128, 0, 0),
		(128, 128, 128),
		(255, 255, 255),
		(75, 180, 60)
	]

	def __init__(self):
		pass

	def FindTarget(self, image):
		height, width, _ = image.shape
		image_area = height * width

		# Convert BGR to HSV
		HSV_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

		# HSV threshold
		threshold = cv2.inRange(HSV_image, self.HSV_Top, self.HSV_Bot)

		# Find Contours
		contours, _ = cv2.findContours(threshold, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

		# Convert min area rect
		min_rectangles = [cv2.minAreaRect(contour) for contour in contours]

		# Filter Rectangles, and classify as left (leaning right) or right (leaning left)
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

		return found_targets

	@staticmethod
	def drawtargets(image, targets):
		for index, target in enumerate(targets):
			found_cont = [np.int0(cv2.boxPoints(r)) for r in [target.l_rect.raw_rect, target.r_rect.raw_rect]]
			try:
				image = cv2.drawContours(image, found_cont, -1, ProcessImage.colors[index], 3)
			except IndexError:
				# More targets than colors!
				pass
		return image


def live_video():
	proc = ProcessImage()

	cam = cv2.VideoCapture(1)
	frame_width = 1920
	frame_height = 1080

	cam.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
	cam.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
	cam.set(cv2.CAP_PROP_EXPOSURE, -10)

	while True:
		ret_val, img = cam.read()
		img = proc.FindTarget(img)
		display_scaled_image('test', img, 0.5)
		if cv2.waitKey(1) == 27:
			break  # esc to quit
	cam.release()
	cv2.destroyAllWindows()


def single_image(image_path):
	proc = ProcessImage()
	img = cv2.imread(image_path)
	found_targets = proc.FindTarget(img)
	img = proc.drawtargets(img, found_targets)
	display_scaled_image('test', img, 0.5)


if __name__ == '__main__':
	folder = "..\\out2"
	files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
	images = [f for f in files if f.endswith(".png")]
	for image in images:
		print(image)
		single_image(image)
		cv2.waitKey(20)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
