import threading
import logging

from cscore import CameraServer


class CSDisplay(threading.Thread):
	def __init__(self, source=None, stream_name="Camera0", res=(1920, 1080)):
		self.logger = logging.getLogger("CSDisplay")
		self.stream_name = stream_name
		self.source = source
		self.output_res = res
		
		cs = CameraServer.getInstance()
		self.outstream = cs.putVideo(self.stream_name, self.output_res[0], self.output_res[1])

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
			if self.source is None:
				if self._new_frame:
					self.outstream.putFrame(self._frame)
					self._new_frame = False
			elif self.source.new_frame:
				self.outstream.putFrame(self.source.frame)
		cv2.destroyAllWindows()


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
