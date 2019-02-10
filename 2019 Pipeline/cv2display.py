import threading
import logging

import cv2


class Cv2Display(threading.Thread):
	def __init__(self, source=None, window_name="Camera0"):
		self.logger = logging.getLogger("Cv2Display")
		self.window_name = window_name
		self.source = source

		self._frame = None
		self._new_frame = False

		self.stopped = True
		threading.Thread.__init__(self)

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
		threading.Thread.start(self)

	def run(self):
		while not self.stopped:
			if self.source is not None:
				if self.source.new_frame:
					self.frame = self.source.frame
			if self._new_frame:
				cv2.imshow(self.window_name, self._frame)
				self._new_frame = False
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
