import logging
import argparse
import os
import time
import cv2
import threading

from networktables  import NetworkTables

from bucketvision.capturers.cv2capture           import Cv2Capture
from bucketvision.capturers.csicapture           import CSICapture
from bucketvision.displays.cv2display            import Cv2Display
from bucketvision.displays.cameraserverdisplay   import CameraServerDisplay
from bucketvision.postprocessors.angryprocessor  import AngryProcesses
from bucketvision.multiplexers.class_mux         import ClassMux
from bucketvision.multiplexers.mux1n             import Mux1N
from bucketvision.sourceprocessors.resizesource  import ResizeSource
from bucketvision.sourceprocessors.overlaysource import OverlaySource

from bucketvision.configs                        import configs

logging.basicConfig(level=logging.DEBUG)

def connectionListener(connected, info):
    """ used to wait till network tables is initalized """
    print(info, '; Connected=%s' % connected)
    with cond:
        notified[0] = True
        cond.notify()

if __name__ == '__main__':

    # add parse arguments
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-ip',   '--ip-address',     required=False, default='10.41.83.2',
                        help='IP Address for NetworkTable Server')

    parser.add_argument('-t',    '--test',           required=False,
                        help='Test mode (uses cv2 display)',                 action='store_true')

    parser.add_argument('-cam',  '--num-cam',        required=False, default=1,
                        help='Number of cameras to instantiate',   type=int, choices=range(1, 10))

    parser.add_argument('-co',   '--offs-cam',       required=False, default=0,
                        help='First camera index to instantiate',   type=int, choices=range(0, 10))
                        
    parser.add_argument('-proc', '--num-processors', required=False, default=4,
                        help='Number of processors to instantiate', type=int, choices=range(0, 10))

    parser.add_argument('-CSI',  '--CSI', 
                        help='Use CSI interface', action='store_true')

    args = vars(parser.parse_args())

    cond = threading.Condition()
    notified = [False]
    # init networktables
    NetworkTables.initialize(server=args.ip_address)
    # add a listener for connection
    NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)

    # if not connected then block and wait
    with cond:
        print("Waiting")
        if not notified[0]:
            cond.wait()

    VisionTable = NetworkTables.getTable("BucketVision")
    VisionTable.putString("BucketVisionState", "Starting")
    VisionTable.putNumber("Exposure", 50.0)
    
    # create a source per camera
    source_list = list()

    for i in range(args.num_cam):
        if not args.CSI:
            cap = Cv2Capture(camera_num=i+args.offs_cam, network_table=VisionTable, exposure=configs['exposure'], res=configs['camera_res'])
        else:
            cap = CSICapture(camera_num=i+args.offs_cam, network_table=VisionTable, exposure=configs['exposure'], res=configs['camera_res'])
        source_list.append(cap)
        cap.start()

    # Output is cropped to match vision target search area. 
    # UU would prefer to output full image from camera and adjust traget drawings to croppped target search area.
    # Right now its not clear how the output matches the input image and the target coordinates.
    # This is likely why the drawtarget routine has not yet been enabled.

    source_mux     = ClassMux(*source_list)
    output_mux     = Mux1N(source_mux)
    
    process_output = output_mux.create_output()
    display_output = OverlaySource(ResizeSource(output_mux.create_output(), res=configs['output_res']))
        
    VisionTable.putString("BucketVisionState", "Started Captures")

    # create post processor threads to process each image before sending it to the CameraServer (or window if testing)
    # this does the more complex target finding. We create multiple process threads to process the frames
    # as they are captured
    proc_list = list()
    for i in range(args.num_processors):
        proc = AngryProcesses(process_output, network_table=VisionTable, debug_label="Proc{}".format(i))
        proc_list.append(proc)
        proc.start()

    VisionTable.putString("BucketVisionState", "Started Processes")

    if args.test:
        window_display = Cv2Display(source=display_output)
        window_display.start()
        VisionTable.putString("BucketVisionState", "Started CV2 Display")
    else:
        cs_display = CSDisplay(source=display_output, network_table=VisionTable)
        cs_display.start()
        VisionTable.putString("BucketVisionState", "Started CS Display")

    try:
        VisionTable.putValue("CameraNum", 0)
        while True:
            source_mux.source_num = int(VisionTable.getEntry("CameraNum").value)
            # not sure how this works and if needed
            if args.test:
                if window_display._new_frame:
                    cv2.imshow(window_display.window_name, window_display._frame)
                    window_display._new_frame = False
                cv2.waitKey(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        if args.test:
            window_display.stop()
            cv2.destroyAllWindows()
        else:
            cs_display.stop()
        for proc in proc_list:
            proc.stop()
        for cap in source_list:
            cap.stop()
