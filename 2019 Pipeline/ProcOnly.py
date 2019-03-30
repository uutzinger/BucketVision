import logging
import os

from networktables import NetworkTables

from cv2capture import Cv2Capture
from angryprocesses import AngryProcesses

from configs import configs

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
	NetworkTables.initialize(server='10.41.83.2')

	VisionTable = NetworkTables.getTable("BucketVision")
	VisionTable.putString("BucketVisionState", "Starting")

	cap = Cv2Capture(camera_num=0, network_table=VisionTable, exposure=10, res=configs['camera_res'])
	proc = AngryProcesses(cap, network_table=VisionTable, debug_label="Proc0")
	cap.start()
	proc.start()

	os.system("v4l2-ctl -c exposure_absolute={}".format(configs['brigtness']))

	try:
		while True:
			pass
	except KeyboardInterrupt:
		proc.stop()
		cap.stop()
