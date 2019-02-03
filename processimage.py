import math

import numpy as np
import cv2

import os

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

class ProcessImage:
	HSV_Top = (49, 0, 48)
	HSV_Bot = (91, 255, 255)
	Min_Rect_Area = 0.0001
	Max_Trgt_Ratio = 10
	Rect_Ratio_Limit = 6
	Min_Ang = 50
	Max_Ang = 75

	colors = [
		(255, 0, 0),
		(0, 255, 0),
		(0, 0, 255),
		(255, 255, 0),
		(0, 255, 255),
		(255, 255, 255)
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
		filtered_rect = list()
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

			# Find the distance from the current rect to
			dist_list = [point_dist(l_rect[0], r_rect[0]) for r_rect in right_rect]

			for r_index, dist in enumerate(dist_list):
				# Get the corresponding right rectangle
				r_rect = right_rect[r_index]
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

		out_img = image

		for index, rect in enumerate(rect_pairs):
			found_cont = [np.int0(cv2.boxPoints(r)) for r in rect]
			# Mark Left Contours Blue
			try:
				out_img = cv2.drawContours(out_img, found_cont, -1, self.colors[index], 3)
			except:
				pass
		return out_img


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


def single_image():
	proc = ProcessImage()
	img = cv2.imread('BitBucket Test Data/out/image-0000376.png')
	img = proc.FindTarget(img)
	display_scaled_image('test', img, 0.5)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

def multiple_images():
	proc = ProcessImage()

	pressed = 0

	imageDir = "BitBucket Test Data/out/" #specify your path here
	image_path_list = []
	valid_image_extensions = [".png"] #specify your vald extensions here
	valid_image_extensions = [item.lower() for item in valid_image_extensions]
	
	#create a list all files in directory and
	#append files with a vaild extention to image_path_list
	for file in os.listdir(imageDir):
		extension = os.path.splitext(file)[1]
		if extension.lower() not in valid_image_extensions:
			continue
		image_path_list.append(os.path.join(imageDir, file))

	#loop through image_path_list to open each image
	for imagePath in image_path_list:
		img = cv2.imread(imagePath)
		img = proc.FindTarget(img)
		display_scaled_image('yeet', img, 0.5)
		
		key = cv2.waitKey(0)
		if key == 32: # spacebar
			pressed += 1
			print(pressed)
			continue
	
	# close any open windows
	cv2.destroyAllWindows()


if __name__ == '__main__':
	multiple_images()