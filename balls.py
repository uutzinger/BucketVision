import numpy as np
import math
import argparse
import cv2
import time

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required = True,
help = "Path to the image")
args = vars(ap.parse_args())

image = cv2.imread(args["image"])

w = 640.0
r = w / image.shape[1]
dim = (int(w), int(image.shape[0] * r))

image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
start = time.time()

imagebw = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(imagebw, (9, 9), 0)
#cv2.imshow("Image", imagebw)

thresh1 = cv2.adaptiveThreshold(blurred, 255,
cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 4)
#cv2.imshow("Mean Thresh", thresh1)

#thresh2 = cv2.adaptiveThreshold(blurred, 255,
#cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)
#cv2.imshow("Gaussian Thresh", thresh2)

f = 1.0
hue = [0.0, 61.74061433447099]
sat = [73.38129496402877, 255.0]
val = [215.55755395683454*f, 255.0*f]

out = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
thresh3 = cv2.inRange(out, (hue[0], sat[0], val[0]),  (hue[1], sat[1], val[1]))
#cv2.imshow("HSV Thresh", thresh3)

threshmask = cv2.bitwise_and(thresh1, thresh1, mask = thresh3) 
#cv2.imshow("and mask", threshmask)

masked = cv2.bitwise_and(image, image, mask = threshmask)
#cv2.imshow("Mask Applied to Image", masked)

canny = cv2.Canny(masked, 10, 255)
#cv2.imshow("Canny", canny)

#(_, contours, _) = cv2.findContours(canny.copy(), cv2.RETR_EXTERNAL,
#cv2.CHAIN_APPROX_SIMPLE)

(_, contours, _) = cv2.findContours(threshmask.copy(), cv2.RETR_EXTERNAL,
cv2.CHAIN_APPROX_SIMPLE)

#print("{} candidates in this image".format(len(contours)))

contours_area = []

# calculate area and filter into new array
for con in contours:
	area = cv2.contourArea(con)
	if 35 < area:
		contours_area.append(con)
#print("Reduce to {} balls in this image".format(len(contours_area)))

#contours_circles = []

#check if contour is of circular shape
# for con in contours_area:
	# perimeter = cv2.arcLength(con, True)
	# area = cv2.contourArea(con)
	# if perimeter != 0:
		# circularity = 4*math.pi*(area/(perimeter*perimeter))
		# if 0.3 < circularity < 1.2:
			# contours_circles.append(con)
			
balls = image.copy()

for con in contours_area:
	(x,y),radius = cv2.minEnclosingCircle(con)
	center = (int(x),int(y))
	radius = int(radius)
	cv2.circle(balls,center,radius,(0,255,0),2)
	x,y,w,h = cv2.boundingRect(con)
	cv2.rectangle(balls,(x,y),(x+w,y+h),(255,0,0),2)
	rect = cv2.minAreaRect(con)
	box = cv2.boxPoints(rect)
	box = np.int0(box)
	cv2.drawContours(balls,[box],0,(0,0,255),2)

print("Duration = ", time.time() - start)

cv2.imshow("Candidate balls", balls)


cv2.waitKey(0)