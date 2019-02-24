import threading
import logging

import cv2

import time

import pyximport
pyximport.install()

from processimage import ProcessImage


class AngryProcesses(threading.Thread):
	def __init__(self, source=None, network_table=None, debug_label=""):
		self.logger = logging.getLogger("AngryProcesses")
		self.net_table = network_table
		self.source = source
		self.debug_label = debug_label

		self._frame = None
		self._new_frame = False
		self.new_frame = False
		self.last_frame_time = 0.0
		
		if self.net_table is not None:
			self.net_table.putNumber("LastFrameTime", 0.0)

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
		self._new_frame = True

	@staticmethod
	def dict_zip(*dicts):
		all_keys = {k for d in dicts for k in d.keys()}
		return {k: [d[k] for d in dicts if k in d] for k in all_keys}

	def update_results(self):
		if self.net_table is not None:
			#last_net_time = float(self.net_table.getEntry("LastFrameTime").value)
			#if last_net_time >= self.last_frame_time:
				#print("\nAP: {}: net table ahead!".format(self.debug_label))
			#	return
			self.net_table.putNumber("LastFrameTime", self.last_frame_time)
			self.net_table.putNumber("CurrFrameTime", time.time())
			result_data = self.dict_zip(*[r.dict() for r in self.results])
			self.net_table.putNumber("NumTargets", len(result_data))
			for key, value in result_data.items():
				# Here we assume that every param is a number of some kind
				self.net_table.putNumberArray(key, value)

	def draw_trgt(self):
		if self.source is None:
			return self.processor.drawtargets(self.frame, self.results)
		else:
			return self.processor.drawtargets(self.source.frame, self.results)

	def stop(self):
		self.stopped = True

	def start(self):
		self.stopped = False
		if self.net_table is not None:
			self.net_table.putBoolean('Overlay', False)
		threading.Thread.start(self)

	def run(self):
		frame_hist = list()
		while not self.stopped:
			if self.source is not None:
				if self.source.new_frame:
					self._new_frame = True
			if self._new_frame:
				if len(frame_hist) == 10:
					print("angproc:{}".format(1/(sum(frame_hist)/len(frame_hist))))
					frame_hist = list()
				self.last_frame_time = time.time()
				#print("\nAP: {} gets frame at {}".format(self.debug_label, self.last_frame_time))
				if self.source is not None:
					self.results = self.processor.FindTarget(self.source.frame)
				else:
					self.results = self.processor.FindTarget(self.frame)
				if self.net_table is not None:
					pass
					# self.frame = self.draw_trgt()
					# if self.net_table.getBoolean('Overlay', False):
					# 	self.frame = self.draw_trgt()
					# elif self.source is None:
					#	pass
					# else:
					# 	self.frame = self.source.frame
				elif self.source is not None:
					self.frame = self.source.frame
				else:
					self.new_frame = True
				self.update_results()
				self._new_frame = False
				duration = time.time() - self.last_frame_time
				frame_hist.append(duration)
				#print("\nAP: {} done at {}".format(self.debug_label, time.time()))


if __name__ == '__main__':
	from cv2capture import Cv2Capture
	from cv2display import Cv2Display
	logging.basicConfig(level=logging.DEBUG)

	print("Start Cam")

	cam = Cv2Capture(camera_num=0, exposure=-2)
	cam.start()

	print("Start Proc")

	proc = AngryProcesses(cam)
	proc.start()

	print("Start Display")

	sink = Cv2Display(source=proc)
	sink.start()

	print("Started Everything!")

	try:
		while True:
			pass
	except KeyboardInterrupt:
		sink.stop()
		proc.stop()
		cam.stop()
