"""
Simply display the contents of the webcam with optional mirroring using OpenCV
via the new Pythonic cv2 interface.  Press <esc> to quit.
"""

import cv2
import time


if __name__ == '__main__':
	cam = cv2.VideoCapture(1)
	frame_width = 1920
	frame_height = 1080

	cam.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
	cam.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
	cam.set(cv2.CAP_PROP_EXPOSURE, -10)

	out = cv2.VideoWriter('outpy.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 24, (frame_width, frame_height))

	while True:
		ret_val, img = cam.read()
		out.write(img)
		cv2.imshow('my webcam', img)
		if cv2.waitKey(1) == 27:
			break  # esc to quit
	out.release()
	cam.release()
	cv2.destroyAllWindows()
