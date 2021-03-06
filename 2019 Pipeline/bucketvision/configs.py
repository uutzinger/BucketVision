configs = {
    'ip'              : '10.41.83.2',   # address of network table server
	'camera_res'      : (320, 240),     # camera width & height                                      CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT
    'fov'             : 80,             # camera lens field of view in degress
    'exposure'        : 3,              # 1=100micro seconds, max=frame interval,                    CAP_PROP_EXPOSURE
    'fps'             : 100,            # 6, 9, 21, 30, 30, 60, 100, 120                             CAP_PROP_FPS
    'fourcc'          : 'MJPG',         # MJPG, YUY2, for ELP camera https://www.fourcc.org/         CAP_PROP_FOURCC 
    'buffersize'      : 4,              # default is 4 for V4L2, max 10,                             CAP_PROP_BUFFERSIZE 
    'autoexposure'    : 1,              # 0=auto, 1=manual, 2=shutter priority, 3=aperture priority, CAP_PROP_AUTO_EXPOSURE
    'autowhite'       : 0,              # 0, 1 bool                                                  CAP_PROP_AUTO_WB 
    'whitetemp'       : 57343,          # min=800 max=6500 step=1 default=57343                      CAP_PROP_WB_TEMPERATURE 
    'autofocus'       : 0,              # 0 or 1 bool,                                               CAP_PROP_AUTOFOCUS
    'serverfps'       : 16,             # frame rate for display server
    # Target Recognition
    'HSV_Top'         : (49, 0, 48),    # HSV top threshold for find target
    'HSV_Bot'         : (91, 255, 255), # HSV bottom threshold for find target
    'Min_Area'        : 0.0001,         # Object needs to be bigger than Min_Area * # of pixels to quaify for valid object
    'MaxTargetRatio'  : 3,              # Target height to Dsitance to Target ratio
    'RectRatioLimit'  : 6,              #
    'MinAngle'        : 50,             #
    'MaxAngle'        : 75,             #
    'crop_top'        : 2/6,            # crop top for target search
    'crop_bot'        : 5/6,            # crop bottom for target search
    'Colorfactors'    : (-0.2957, 0.7606, -0.5780),      # Color factors from the Principal Component Analysis
    'GrayThresh'      : 24,             # Threshold for grayscale image
    # Target Display
    'output_res'      : (320:240),      # Output resolution 
    'target_dist'     : 1.0             # desired target distance
    'target_dist_min' : 10.0            # turn on target display if target closer
    'target_dist_max' : 0.5             # turn on target display if target further
    'MarkingColors'   : [               # For labeling targets 
                      ( 75,  25, 230),
                      ( 25, 225, 255),
                      (200, 130,   0),
                      ( 48, 130, 245),
                      (240, 240,  70),
                      (230,  50, 240),
                      (190, 190, 250),
                      (128, 128,   0),
                      (255, 190, 230),
                      ( 40, 110, 170),
                      (200, 250, 255),
                      (  0,   0, 128),
                      (195, 255, 170),
                      (128,   0,   0),
                      (128, 128, 128),
                      (255, 255, 255),
                      ( 75, 180,  60) ]
}
 

# original configs had 'brigtness':3

# MJPG BUFFER 1 FPS 100, 46,44,82ms lag
# MJPG BUFFER 1 FPS 30, 41,68ms lag
# MJPG BUFFER 100 FPS 100, 38,45,111ms lag
# MJPG BUFFER 1 FPS 100, 75,55ms lag
# MJPG BUFFER 1 FPS 30, 98,83ms lag
# YUY2 BUFFER 1 FPS 30 121,231,77ms lag
# YUY2 BUFFER 100 FPS 30 ms 103,26,69,111ms lag
#
# 5.595800888707158638e-01 -2.957290628907573438e-01 7.765443421602964413e-01
# 6.277237972334540617e-01 7.605741413306832399e-01 -1.615063864575108366e-01
# 5.411404240363634210e-01 -5.779890110554425364e-01 -6.090111425846570503e-01
