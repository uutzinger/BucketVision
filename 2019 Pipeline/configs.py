configs = {
	'camera_res': (320, 240),
	'crop_top': 0,
	'crop_bot': 0.5,
	'brigtness': 3
}
cropped_vres = int(configs['camera_res'][1]*(configs['crop_bot'])) - int(configs['camera_res'][1]*(configs['crop_top']))
configs['output_res'] = (configs['camera_res'][0], cropped_vres)


