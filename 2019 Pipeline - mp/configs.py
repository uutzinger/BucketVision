configs = {
	'camera_res'    : (320, 240),     # camera width & height                                      CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT
    'crop_top'      : 2/6,            # crop top
    'crop_bot'      : 5/6,            # crop bottom
    'fov'           : 80,             # camera lens field of view in degress
    'exposure'      : 3,              # 1=100micro seconds, max=frame interval,                    CAP_PROP_EXPOSURE
    'fps'           : 100,            # 6, 9, 21, 30, 30, 60, 100, 120                             CAP_PROP_FPS
    'fourcc'        : 'MJPG',         # MJPG, YUY2, for ELP camera https://www.fourcc.org/         CAP_PROP_FOURCC 
    'buffersize'    : 4,              # default is 4 for V4L2, max 10,                             CAP_PROP_BUFFERSIZE 
    'autoexposure'  : 1,              # 0=auto, 1=manual, 2=shutter priority, 3=aperture priority, CAP_PROP_AUTO_EXPOSURE
    'autowhite'     : 0,              # 0, 1 bool                                                  CAP_PROP_AUTO_WB 
    'whitetemp'     : 57343,          # min=800 max=6500 step=1 default=57343                      CAP_PROP_WB_TEMPERATURE 
    'autofocus'     : 0,              # 0 or 1 bool,                                               CAP_PROP_AUTOFOCUS
    'serverfps'     : 10,             # frame rate for display server
    'HSV_Top'       : (49, 0, 48),    # HSV top threshold for find target
    'HSV_Bot'       : (91, 255, 255), # HSV bottom threshold for find target
    'Min_Area'      : 0.0001,         # Object needs to be bigger than Min_Area * # of pixels to quaify for valid object
    'MaxTargetRatio': 3,              # Target height to Dsitance to Target ratio
    'Colorfactors'  : (-0.2957, 0.7606, -0.5780),      # Color factors from the Principal Component Analysis
    'GrayThresh'    : 24,             # Threshold for grayscale image
    'ip'            : '10.41.83.2'    # address of network table server
}

cropped_vres = int(configs['camera_res'][1]*(configs['crop_bot'])) - int(configs['camera_res'][1]*(configs['crop_top']))
configs['output_res'] = (configs['camera_res'][0], cropped_vres)

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
