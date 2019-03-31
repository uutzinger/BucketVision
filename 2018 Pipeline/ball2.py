import cv2
import time

im = cv2.imread('balls.jpg')
w = 640.0
r = w / im.shape[1]
dim = (int(w), int(im.shape[0] * r))

im = cv2.resize(im, dim, interpolation = cv2.INTER_AREA)

start = time.time()

hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)

hue = [0.0, 61.74061433447099]
sat = [73.38129496402877, 255.0]
val = [215.55755395683454, 255.0]


thresh3 = cv2.inRange(hsv, (hue[0], sat[0], val[0]),  (hue[1], sat[1], val[1]))

th, bw = cv2.threshold(hsv[:, :, 2], 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
bw = thresh3

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
morph = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
dist = cv2.distanceTransform(morph, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
borderSize = 25 #75
distborder = cv2.copyMakeBorder(dist, borderSize, borderSize, borderSize, borderSize, 
                                cv2.BORDER_CONSTANT | cv2.BORDER_ISOLATED, 0)
gap = 10                                
kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*(borderSize-gap)+1, 2*(borderSize-gap)+1))
kernel2 = cv2.copyMakeBorder(kernel2, gap, gap, gap, gap, 
                                cv2.BORDER_CONSTANT | cv2.BORDER_ISOLATED, 0)
distTempl = cv2.distanceTransform(kernel2, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
nxcor = cv2.matchTemplate(distborder, distTempl, cv2.TM_CCOEFF_NORMED)
mn, mx, _, _ = cv2.minMaxLoc(nxcor)
th, peaks = cv2.threshold(nxcor, mx*0.5, 255, cv2.THRESH_BINARY)
peaks8u = cv2.convertScaleAbs(peaks)
_, contours, hierarchy = cv2.findContours(peaks8u, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
peaks8u = cv2.convertScaleAbs(peaks)    # to use as mask
for i in range(len(contours)):
	area = cv2.contourArea(contours[i])
	if 12 < area:
		x, y, w, h = cv2.boundingRect(contours[i])
		_, mx, _, mxloc = cv2.minMaxLoc(dist[y:y+h, x:x+w], peaks8u[y:y+h, x:x+w])
		cv2.circle(im, (int(mxloc[0]+x), int(mxloc[1]+y)), int(mx), (255, 0, 0), 2)
		cv2.rectangle(im, (x, y), (x+w, y+h), (0, 255, 0), 2)
		cv2.drawContours(im, contours, i, (0, 0, 255), 2)

print("Duration = ",time.time() - start)
cv2.imshow('Balls', im)
cv2.waitKey(0)
