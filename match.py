# -*- coding: utf-8 -*-
"""
match

Example of matching a template to an image
Derived from techniques found at http://www.pyimagesearch.com/2015/01/26/multi-scale-template-matching-using-python-opencv/

Copyright (c) 2017 - RocketRedNeck.com RocketRedNeck.net 

RocketRedNeck and MIT Licenses 

RocketRedNeck hereby grants license for others to copy and modify this source code for 
whatever purpose other's deem worthy as long as RocketRedNeck is given credit where 
where credit is due and you leave RocketRedNeck out of it for all other nefarious purposes. 

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal 
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions: 

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software. 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE. 
**************************************************************************************************** 
"""

# import the necessary packages
import numpy as np
import imutils
import cv2

# load the image image, convert it to grayscale, and detect edges
img = cv2.imread("shirt.jpg")
img = cv2.resize(img,(640,480))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
template = cv2.Canny(gray, 50, 200)
(tH, tW) = template.shape[:2]
cv2.imshow("Template", template)

sift = cv2.xfeatures2d.SIFT_create()
kp = sift.detect(gray,None)
keypoint=cv2.drawKeypoints(gray,kp,img)
cv2.imshow("KeyPoints",keypoint)

# loop over the images to find the template in
#for imagePath in range(1,2) #glob.glob("/*.jpg"):
# load the image, convert it to grayscale, and initialize the
# bookkeeping variable to keep track of the matched region
image = cv2.imread("shirt.jpg")
image = cv2.resize(image, (640,480))
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
found = None
 
# loop over the scales of the image
for scale in np.linspace(0.2, 1.0, 20)[::-1]:
	# resize the image according to the scale, and keep track
	# of the ratio of the resizing
	resized = imutils.resize(gray, width = int(gray.shape[1] * scale))
	r = gray.shape[1] / float(resized.shape[1])
 
	# if the resized image is smaller than the template, then break
	# from the loop
	if resized.shape[0] < tH or resized.shape[1] < tW:
		break

	# detect edges in the resized, grayscale image and apply template
	# matching to find the template in the image
	edged = cv2.Canny(resized, 50, 200)
	result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
	(_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)
 
	# check to see if the iteration should be visualized
#	if args.get("visualize", False):
#		# draw a bounding box around the detected region
#		clone = np.dstack([edged, edged, edged])
#		cv2.rectangle(clone, (maxLoc[0], maxLoc[1]),
#			(maxLoc[0] + tW, maxLoc[1] + tH), (0, 0, 255), 2)
#		cv2.imshow("Visualize", clone)
#		cv2.waitKey(0)
 
	# if we have found a new maximum correlation value, then ipdate
	# the bookkeeping variable
	if found is None or maxVal > found[0]:
		found = (maxVal, maxLoc, r)
 
# unpack the bookkeeping varaible and compute the (x, y) coordinates
# of the bounding box based on the resized ratio
(_, maxLoc, r) = found
(startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
(endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
 
# draw a bounding box around the detected result and display the image
cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
cv2.imshow("Image", image)
cv2.waitKey(0)