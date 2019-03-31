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
import cv2
#from matplotlib import pyplot as plt

MIN_MATCH_COUNT = 10

# load the image, convert it to grayscale, and detect edges
img1 = cv2.imread("shirtTraining.jpg",cv2.IMREAD_GRAYSCALE)
img1 = cv2.resize(img1,(640,480))

img2 = cv2.imread('shirt4.jpg',cv2.IMREAD_GRAYSCALE) 
img2 = cv2.resize(img2,(640,480))


# Initiate SIFT detector
sift = cv2.xfeatures2d.SIFT_create()

# find the keypoints and descriptors with SIFT
kp1, des1 = sift.detectAndCompute(img1,None)
kp2, des2 = sift.detectAndCompute(img2,None)
norm = cv2.NORM_L2

# Create SURF object. You can specify params here or later.
# Here I set Hessian Threshold to 400
#surf = cv2.xfeatures2d.SURF_create(400)
#kp1, des1 = surf.detectAndCompute(img1,None)
#kp2, des2 = surf.detectAndCompute(img2,None)

# Initiate ORB detector
#orb = cv2.ORB_create()
# find the keypoints and descriptors with ORB
#kp1, des1 = orb.detectAndCompute(img1,None)
#kp2, des2 = orb.detectAndCompute(img2,None)
#norm = cv2.NORM_HAMMING

#FLANN_INDEX_KDTREE = 0
#
#index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
#search_params = dict(checks = 50)
#
#flann = cv2.FlannBasedMatcher(index_params, search_params)
#matches = flann.knnMatch(des1,des2,k=2)


# create BFMatcher object
crossCheck = False
bf = cv2.BFMatcher(norm, crossCheck)
# Match descriptors.
if (crossCheck == True):
    matches = bf.match(des1,des2)
    # Sort them in the order of their distance.
    matches = sorted(matches, key = lambda x:x.distance)
else:
    matches = bf.knnMatch(des1,des2,k=2)
    



if (crossCheck == False):
    # store all the good matches as per Lowe's ratio test.
    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)
            
    if (len(good)>MIN_MATCH_COUNT):
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        matchesMask = mask.ravel().tolist()
        h,w = img1.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        dst = cv2.perspectiveTransform(pts,M)
        img2 = cv2.polylines(img2,[np.int32(dst)],True,255,2, cv2.LINE_AA)
    else:
        print("Not enough matches are found - %d/%d" % (len(good),MIN_MATCH_COUNT))
        matchesMask = None
    
    
    draw_params = dict(matchColor = (0,255,0), # draw matches in green color
                       singlePointColor = None,
                       matchesMask = matchesMask, # draw only inliers
                       flags = 2)
    
    img3 = cv2.drawMatches(img1,kp1,img2,kp2,good,None,**draw_params)
        
else:
    ## Draw first 10 matches.
    img3 = cv2.drawMatches(img1,kp1,img2,kp2,matches[:10], None, flags=2)


cv2.imshow("Image", img3)
cv2.waitKey(0)

#plt.imshow(img3, 'gray'),plt.show()
#plt.imshow(gray),plt.show()