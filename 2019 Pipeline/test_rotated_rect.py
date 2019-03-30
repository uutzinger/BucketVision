import math
import time

import numpy as np
import cv2


def rotate_point(point, center, theta):
	cx, cy = center
	x, y = point
	tempX = x - cx
	tempY = y - cy

	rotatedX = tempX * math.cos(theta) - tempY * math.sin(theta)
	rotatedY = tempX * math.sin(theta) + tempY * math.cos(theta)
	x = rotatedX + cx
	y = rotatedY + cy

	return x, y


def rotated_rect(height, width, pos, theta):
	x, y = pos
	tl = x - width / 2, y - height / 2
	tr = x - width / 2, y + height / 2
	bl = x + width / 2, y - height / 2
	br = x + width / 2, y + height / 2

	tl = rotate_point(tl, pos, theta)
	tr = rotate_point(tr, pos, theta)
	bl = rotate_point(bl, pos, theta)
	br = rotate_point(br, pos, theta)

	return [tl, bl, br, tr]



if __name__ == '__main__':
	for t in np.linspace(0, 2*math.pi, num=360):
		pts = np.array(rotated_rect(160, 80, (250, 250), t), np.int32)
		pts = pts.reshape((-1, 1, 2))

		img = np.zeros((500, 500), np.uint8)
		img = cv2.fillPoly(img, [pts], (255))

		contours, _ = cv2.findContours(img, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
		min_rectangles = [cv2.minAreaRect(contour) for contour in contours]

		print("{1}\t{0}".format(min_rectangles[0][2], math.degrees(t)))

		cv2.imshow('test', img)
		cv2.waitKey(50)

	cv2.imshow('test', img)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
