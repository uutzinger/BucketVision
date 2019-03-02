import threading
import logging

from cscore import CameraServer


class CSDisplay(threading.Thread):
	def __init__(self, source=None, stream_name="Camera0", res=None):
		self.logger = logging.getLogger("CSDisplay")
		self.stream_name = stream_name
		self.source = source
		if res is not None:
			self.output_width = res[0]
			self.output_height = res[1]
		else:
			self.output_width = int(self.source.width)
			self.output_height = int(self.source.height)
		
		cs = CameraServer.getInstance()
		self.outstream = cs.putVideo(self.stream_name, self.output_width, self.output_height)

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
