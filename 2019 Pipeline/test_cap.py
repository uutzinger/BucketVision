import cv2

cam = cv2.VideoCapture(0)

for i in range(10):
	_, im = cam.read()
	cv2.imwrite('im{}.png'.format(i), im)

