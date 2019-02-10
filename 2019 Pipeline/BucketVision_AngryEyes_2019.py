import logging
import argparse
import time

from networktables import NetworkTables

from cv2capture import Cv2Capture
from cv2display import Cv2Display
from angryprocesses import AngryProcesses

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-ip', '--ip-address', required=False, default='10.41.83.2',
						help='IP Address for NetworkTable Server')

	parser.add_argument('-t', '--test', help='Test mode (uses cv2 display)', action='store_true')

	args = vars(parser.parse_args())

	if not args['test']:
		from csdisplay import CSDisplay

	NetworkTables.initialize(server=args['ip_address'])

	VisionTable = NetworkTables.getTable("BucketVision")
	VisionTable.putString("BucketVisionState", "Starting")
	CameraTable = VisionTable.getSubTable('FrontCamera')

	frontCamera = Cv2Capture(camera_num=0, network_table=CameraTable, exposure=-10)
	frontCamera.start()

	proc1 = AngryProcesses(frontCamera, network_table=CameraTable)
	proc1.start()

	if args['test']:
		window_display = Cv2Display(source=proc1)
		window_display.start()
	else:
		cs_display = CSDisplay(source=proc1)
		cs_display.start()

	while True:
		pass
