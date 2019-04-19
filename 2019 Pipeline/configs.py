configs = {
	'camera_res'   : (320, 240),
    'crop_top'     : 2/6,
    'crop_bot'     : 5/6,
    'exposure'     : 3,
    'fps'          : 100,      # 6, 9, 21, 30, 30, 60, 100
    'fourcc'       : 'MJPG',   # MJPG, YUY2, for ELP https://www.fourcc.org/
    'buffersize'   : 4,        # default is 4 for V4L2, max 10
    'CSIexposure'  : 3000,
    'CSIframerate' : 90,
}
cropped_vres = int(configs['camera_res'][1]*(configs['crop_bot'])) - int(configs['camera_res'][1]*(configs['crop_top']))
configs['output_res'] = (configs['camera_res'][0], cropped_vres)

# MJPG BUFFER 1 FPS 100, 46,44,82ms lag
# MJPG BUFFER 1 FPS 30, 41,68ms lag
# MJPG BUFFER 100 FPS 100, 38,45,111ms lag
# MJPG BUFFER 1 FPS 100, 75,55ms lag
# MJPG BUFFER 1 FPS 30, 98,83mslag
# YUY2 BUFFER 1 FPS 30 121,231,77mslag
# YUY2 BUFFER 100 FPS 30 ms 103,26,69,111mslag

