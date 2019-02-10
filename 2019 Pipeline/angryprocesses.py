import threading
import logging

import cv2

from processimage import ProcessImage


class AngryProcesses(threading.Thread):
	def __init__(self, source=None, network_table=None):
		self.logger = logging.getLogger("AngryProcesses")
		self.net_table = network_table
		self.source = source

		self._frame = None
		self._new_frame = False
		self.new_frame = False

		self.processor = ProcessImage()

		self.results = list()

		self.stopped = True
		threading.Thread.__init__(self)

	@property
	def frame(self):
		self.new_frame = False
		return self._frame

	@frame.setter
	def frame(self, img):
		self._frame = img
		self.new_frame = True

	@staticmethod
	def dict_zip(*dicts):
		all_keys = {k for d in dicts for k in d.keys()}
		return {k: [d[k] for d in dicts if k in d] for k in all_keys}

	def update_results(self):
		if self.net_table is not None:
			self.net_table.putNumber("NumTargets", len(self.results))
			result_data = self.dict_zip(*[r.dict() for r in self.results])
			for key, value in result_data.items():
				# HEre we assume that every param is a number of some kind
				self.net_table.putNumberArray(key, value)

	def draw_trgt(self):
		return self.processor.drawtargets(self.source.frame, self.results)

	def stop(self):
		self.stopped = True

	def start(self):
		self.stopped = False
		if self.net_table is not None:
			self.net_table.putBoolean('Overlay', False)
		threading.Thread.start(self)

	def run(self):
		while not self.stopped:
			if self.source is not None:
				if self.source.new_frame:
					self._new_frame = True
			if self._new_frame:
				if self.source is not None:
					self.results = self.processor.FindTarget(self.source.frame)
				else:
					self.results = self.processor.FindTarget(self.frame)
				if self.net_table is not None:
					if self.net_table.getBoolean('Overlay', False):
						self.frame = self.draw_trgt()
					else:
						self.frame = self.source.frame
				self.update_results()
				self._new_frame = False


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
