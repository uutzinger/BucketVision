from networktables import NetworkTables
import cv2
import os

NetworkTables.initialize(server='10.41.83.2')

VisionTable = NetworkTables.getTable("BucketVision")


while True:
	exp = VisionTable.getEntry("Exposure").value
	os.system("v4l2-ctl -c exposure_absolute={} -d {}".format(exp, 0))
	os.system("v4l2-ctl -c exposure_absolute={} -d {}".format(exp, 1))
	print(exp)

