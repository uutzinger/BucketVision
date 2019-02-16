import logging
import argparse
import time

import cv2

from networktables import NetworkTables

from cv2capture import Cv2Capture
from cv2display import Cv2Display
from angryprocesses import AngryProcesses
from class_mux import Class_Mux

# run "proc_setup.py build_ext --inplace" in order to compile the target finder first
# You will need to install cython first

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-ip', '--ip-address', required=False, default='10.41.83.2',
						help='IP Address for NetworkTable Server')

	parser.add_argument('-t', '--test', help='Test mode (uses cv2 display)', action='store_true')

	parser.add_argument('-cam', '--num-cam', required=False, default=1,
						help='Number of cameras to instantiate', type=int, choices=range(1, 10))

	args = vars(parser.parse_args())

	if not args['test']:
		from csdisplay import CSDisplay

	NetworkTables.initialize(server=args['ip_address'])

	VisionTable = NetworkTables.getTable("BucketVision")
	VisionTable.putString("BucketVisionState", "Starting")

	source_list = list()

	for i in range(args['num_cam']):
		cap = Cv2Capture(camera_num=i, network_table=VisionTable, exposure=-10)
		source_list.append(cap)
		cap.start()

	source_mux = Class_Mux(*source_list)

	VisionTable.putString("BucketVisionState", "Started Capture")

	proc1 = AngryProcesses(source_mux)
	proc1.start()

	VisionTable.putString("BucketVisionState", "Started Process")

	if args['test']:
		window_display = Cv2Display(source=source_mux)
		window_display.start()
		VisionTable.putString("BucketVisionState", "Started CV2 Display")
	else:
		cs_display = CSDisplay(source=source_mux)
		cs_display.start()
		VisionTable.putString("BucketVisionState", "Started CS Display")

	try:
		VisionTable.putValue("CameraNum", 0)
		while True:
			source_mux.source_num = int(VisionTable.getEntry("CameraNum").value)

	except KeyboardInterrupt:
		if args['test']:
			window_display.stop()
		else:
			cs_display.stop()
		proc1.stop()

