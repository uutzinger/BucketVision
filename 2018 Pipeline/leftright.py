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
import time
import math
from matplotlib import pyplot as pl
from matplotlib import image as mpimg

from mpl_toolkits.mplot3d import Axes3D


MIN_MATCH_COUNT = 10

# load the image, convert it to grayscale, and detect edges
img1 = cv2.imread("leftPic.jpg",cv2.IMREAD_GRAYSCALE)
#img1 = cv2.resize(img1,(int(img1.shape[1]/2),int(img1.shape[0]/2)))
print(img1.shape)

img2 = cv2.imread('rightPic.jpg', cv2.IMREAD_GRAYSCALE)
#img2 = cv2.resize(img2,(int(img2.shape[1]/2),int(img2.shape[0]/2)))
print(img2.shape)

# Initiate SIFT detector
sift = cv2.xfeatures2d.SIFT_create()
# Create SURF object. You can specify params here or later.
# Here I set Hessian Threshold to 400
surf = cv2.xfeatures2d.SURF_create(400)
# Initiate ORB detector
orb = cv2.ORB_create()

norm = cv2.NORM_L2
#norm = cv2.NORM_HAMMING

starttime = time.time()

# find the keypoints and descriptors with SIFT
#kp1, des1 = sift.detectAndCompute(img1,None)
#kp2, des2 = sift.detectAndCompute(img2,None)

kp1, des1 = surf.detectAndCompute(img1,None)
kp2, des2 = surf.detectAndCompute(img2,None)

# find the keypoints and descriptors with ORB
#kp1, des1 = orb.detectAndCompute(img1,None)
#kp2, des2 = orb.detectAndCompute(img2,None)

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
        if m.distance < 1.00*n.distance:
            good.append(m)
    
    goodCount= len(good)
    if (goodCount>MIN_MATCH_COUNT):
        src = [kp1[m.queryIdx].pt for m in good]
        src_x = np.array([x[0] for x in src])
        src_y = np.array([x[1] for x in src])
        src_pts = np.float32(src).reshape(-1,1,2)
        dst = [kp2[m.trainIdx].pt for m in good]
        dst_x = np.array([x[0] for x in dst])
        dst_y = np.array([x[1] for x in dst])
        dst_pts = np.float32(dst).reshape(-1,1,2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        matchesMask = mask.ravel().tolist()
#        h,w = img1.shape
#        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
#        dst = cv2.perspectiveTransform(pts,M)
#        
#        
#        angle = (goodCount-MIN_MATCH_COUNT-1)
#        if (angle > 50):
#            angle = 50
#        
#        angle = math.pi/2 * (angle / 50)
#        r = int(math.cos(angle)*255)
#        g = int(math.sin(angle)*255)
        
        #cv2.polylines(img2,[np.int32(dst)],True,(0,g,r),2, cv2.LINE_AA)
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

endtime = time.time()

print(endtime - starttime)
idx = list(np.nonzero(matchesMask)[0].astype(int))
src_x = src_x[idx]
src_y = src_y[idx]
dst_x = dst_x[idx]
dst_y = dst_y[idx]

pl.figure()
img = mpimg.imread("armstrong-trophy-and-naval-court-1862-web.jpg")
pl.imshow(img)

pl.figure()
pl.plot(src_x,-src_y,'+',dst_x,-dst_y,'x')
pl.xlabel('X')
pl.ylabel('Y')

pl.figure()
pl.plot(src_x,1/(src_x-dst_x),'+')
pl.xlabel('X')
pl.ylabel('Z')

fig = pl.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter((src_x + dst_x)/2, 1/(src_x-dst_x), -(src_y+dst_y)/2)
ax.set_xlabel('X Label')
ax.set_ylabel('Z Label')
ax.set_zlabel('Y Label')

pl.show(block=True)

#cv2.imshow("Image", img2c)

#cv2.waitKey(0)

#plt.imshow(img3, 'gray'),plt.show()
#plt.imshow(gray),plt.show()