###############################################################################
#                                                                             #
# file:    BucketVision_AngyEyes_2019_CSI_MP.py                               #
#                                                                             #
# authors: BitBuckets FRC 4183                                                #
#          Mark Omo                                                           #
#          Mike Kessel                                                        #
#          Urs Utzinger                                                       #
#                                                                             #
# date:    April 1st 2019                                                     #
#                                                                             #
# brief:   This file uses multicore processing to detet the angry eyse. We    #
#          utilize all four cores to create a more fluid video.               #
#                                                                             #
###############################################################################

###############################################################################
#
# Camera Server
#   Camera USB 1 -> frame, new_frame
#   Camera USB 2 -> frame, new_frame
#   Camera CSI 1 -> frame, new_frame
#
# Network Table Server
#    BucketVisionState
#    LastFrameTime
#    CurrentFrameTime
#    NumTargets
#    [left_rectangle, right_rectangle]
#    angle, parallax, distance, pos_x, pos_y, size
#
# Target Recognition (FindTarget)
#    img -> countours -> list of paired rectangles [l-rect, r-rect]
# cv2.cvtColor
# cv2.inRange
# cv2.findContours
# cv2.minAreaRect
#
# Local Display: cv2display
#    cv2.imshow(window_name, frame)
# Network Display:  cddisplay
#    Camera Server:             cs=CameraServer.getInstance()
#    Camera Server Stream:      outstream = cs.putVideo
#    Enqueue frame into Stream: outstream.putFrame
#
###############################################################################

###############################################################################
# Imports
#
# Execution
import os
import time
import multiprocessing as mp
import logging
import argparse
from functools         import partial
# Camera
from cv2capture        import Cv2Capture
# Vision
import cv2
# FIRST
from networktables     import NetworkTables
# Custom 4183
from visionyprocesses  import VisionProcesses
from class_mux         import ClassMux
from mux1n             import Mux1N
from resizesource      import ResizeSource
from overlaysource     import OverlaySource
from configs           import configs

logging.basicConfig(level=logging.DEBUG)

##############################################################################
# Main
if __name__ == '__main__':

    # Setup Loggin
    logging.basicConfig(level=logging.DEBUG)

    # Command Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip',   '--ip-address',     required=False, default='10.41.83.2', help='IP Address for NetworkTable Server')
    parser.add_argument('-t',    '--test',                                                 help='Test mode (uses cv2 display)',        action='store_true')
    parser.add_argument('-cam',  '--num-cam',        required=False, default=1,            help='Number of cameras to instantiate',    type=int, choices=range(1, 10))
    parser.add_argument('-co',   '--offs-cam',       required=False, default=0,            help='First camera index to instantiate',   type=int, choices=range(0, 10))
    parser.add_argument('-proc', '--num-processors', required=False, default=4,            help='Number of processors to instantiate', type=int, choices=range(0, 10))
    args = vars(parser.parse_args())

    if not args['test']:  from csdisplay import CSDisplay
    else:                 from cv2display import Cv2Display

    # Network Table Initialize
    NetworkTables.initialize(server=args['ip_address'])
    VisionTable = NetworkTables.getTable("BucketVision")
    VisionTable.putString("BucketVisionState", "Starting")


    source_list = list()
    for i in range(args['num_cam']):
        cap = Cv2Capture(camera_num=i+args['offs_cam'], network_table=VisionTable, res=configs['camera_res'])
        source_list.append(cap)
        cap.start()

    source_mux     = ClassMux(*source_list)
    output_mux     = Mux1N(source_mux)
    process_output = output_mux.create_output()
    display_output = OverlaySource(ResizeSource(output_mux.create_output(), res=configs['output_res']))

    VisionTable.putString("BucketVisionState", "Started Capture")

    proc_list = list()

    for i in range(args['num_processors']):
        proc = VisionProcesses(process_output, network_table=VisionTable, debug_label="Proc{}".format(i))
        proc_list.append(proc)
        proc.start()

    VisionTable.putString("BucketVisionState", "Started Process")

    if args['test']:
        window_display = Cv2Display(source=display_output)
        window_display.start()
        VisionTable.putString("BucketVisionState", "Started CV2 Display")
    else:
        cs_display = CSDisplay(source=display_output)
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
        for proc in proc_list:
            proc.stop()
        for cap in source_list:
            cap.stop()
