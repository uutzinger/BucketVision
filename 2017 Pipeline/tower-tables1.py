import cv2
import numpy as np
import time
import sys
import logging
from networktables import NetworkTable

ip='10.38.14.2' # RoboRio on practice field
#ip='10.41.83.2' # RoboRio on competition field

# Use this command in a terminal to modify the exposure time
# v4l2-ctl -c exposure_auto=1 -c exposure_absolute=150 <--modify this number, higher = more exposure

# Adaptation lowpass filter 80% old and 20% new: alpha 0.2
alpha = 0.2

#for Bitbuckt and Logitech 270
avg_vals = [85,100,200] 
avg_stds = [10, 25, 20]

#for dropshot
#avg_vals = [75,100,200] 
#avg_stds = [10, 25, 20]

# for bitbuckets
# avg_vals = [80,60,180]
# avg_stds = [5, 15, 20]

# clamp average
hue_lower =  60
hue_upper =  100
sat_upper = 255
sat_lower = 100
val_upper = 255
val_lower = 100

# minimum threshold with
hue_std_min = 5
sat_std_min =10
val_std_min =15

# algorithm for goal detection
aspect_min   = 0.4 # acceptable aspect ratio of bounding rectangle 
aspect_max   = 2.5 # 
hullarea_min = 500 # 
area_min     = 100 # reject small objects

displayON = True

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)      
    
hue_range = np.arange(180)
sat_range = np.arange(256)
val_range = np.arange(256)

logging.basicConfig(level=logging.DEBUG)
NetworkTable.setIPAddress(ip)
NetworkTable.setClientMode()
NetworkTable.initialize()
sd = NetworkTable.getTable("BucketVision")

# cap = cv2.VideoCapture("/home/pi/Documents/BitBucketsCV/bitbuckets.mp4")
# cap = cv2.VideoCapture("/home/pi/Documents/BitBucketsCV/dropshot.mp4")
cap = cv2.VideoCapture(0)
if displayON:
    output = cv2.VideoWriter("/home/pi/Documents/BitBucketsCV/output.mp4", int(cap.get(cv2.CAP_PROP_FOURCC)),
        int(cap.get(cv2.CAP_PROP_FPS)), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

print("FourCC: {0}".format(int(cap.get(cv2.CAP_PROP_FOURCC))))
print("FPS: {0}".format(int(cap.get(cv2.CAP_PROP_FPS))))
print("OpenCV Version: {0}".format(cv2.__version__))

oldtime = time.time()
fps = 0.0
upper = np.array([int(avg_vals[x] + 2.5*avg_stds[x]) for x in range(3)])
lower = np.array([int(avg_vals[x] - 2.5*avg_stds[x]) for x in range(3)])

while(True):
    #print('Start'),
    #starttime = time.time()
    ret, frame = cap.read() # 20ms
    #print('Capture'),
    #print(time.time()-starttime) # 

    if ret == False:
        break
    
    frame = cv2.pyrDown(frame) # reduce size for bitbuckets  # 30ms
    #print('Downsample'),
    #print(time.time()-starttime) # 

    #starttime = time.time()
    # low pass filter
    hsv = cv2.blur(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV), (3,3)) # 16ms
    #print('Lowpass'),
    #print(time.time()-starttime) # 

    #starttime = time.time()
    # 17ms
    hsvthresh = cv2.inRange(hsv, lower, upper)       # binary thresholded image
    mask = cv2.bitwise_and(hsv, hsv, mask=hsvthresh) # all pixels inside the mask in color
    #print('Threshold'),
    #print(time.time()-starttime) # 

    #cv2.imshow('thresh', hsvthresh)
    #cv2.imshow('mask', mask)

    #starttime = time.time()
    # Connected Components 2ms
    im2, contours, hierarchy = cv2.findContours(hsvthresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    #print('Contour'),
    #print(time.time()-starttime) # 

    # initialize goal
    goalx = -1
    goaly = -1
    hullarea = -1
    area = -1
    present = False

    #print('Thresh and Contour'),
    #print(time.time()-starttime) # 140ms
            
    for contour in contours:

        #starttime = time.time()
        area = cv2.contourArea(contour)       # size
        #print('Area'),
        #print(time.time()-starttime) # 0.02 ms
        if area < area_min:  # ignore small objects
            continue

        #starttime = time.time()
        hull = cv2.convexHull(contour)     # out polygon fully inclosing object with only convex polygons
        hullarea = cv2.contourArea(hull)   # polygon enclosing area
        #print('Hull'),
        #print(time.time()-starttime) # 0.1 ms
        if hullarea <= hullarea_min:                 #
            continue

        #starttime = time.time()
        # center etc. of the objects
        moments = cv2.moments(contour)
        #print('Moments'),
        #print(time.time()-starttime) # 0.2ms
        if moments['m00'] <= 0:
            continue

        #starttime = time.time()
        rect = cv2.minAreaRect(contour)    # minimum bounding rectangle, can roate on original contour
        box = cv2.boxPoints(rect)          # find area of rectangle
        box = np.int0(box)                 
        boxarea = cv2.contourArea(box)
        aspect = rect[1][1]/rect[1][0]     # center, width/height etc.
        #print('Aspect'),
        #print(time.time()-starttime) # 0.4 ms
        if aspect <= aspect_min and aspect >= aspect_max:
            continue
        
        #starttime = time.time()
        # attempt creating a size reduced mask that lays within the U-shape 
        adjusted_rect = rect
        adjusted_rect = ((rect[0][0], rect[0][1]-rect[1][0]*0.15), (adjusted_rect[1][0] * 0.40, adjusted_rect[1][1] * 0.40), rect[2])
        adjusted_box = cv2.boxPoints(adjusted_rect)
        adjusted_box = np.int0(adjusted_box)
        adjusted_mask = np.zeros(hsvthresh.shape,np.uint8) # empty image
        cv2.drawContours(adjusted_mask,[adjusted_box],0,255,-1) # draw the adjusted mask onto image
        adjusted_mask = cv2.bitwise_not(adjusted_mask, adjusted_mask)  # inverts the image

        # mask of original contour
        mask = np.zeros(hsvthresh.shape,np.uint8) # creat empty 8bit image
        cv2.drawContours(mask,[contour],0,255,-1) # draw current contour (filled) onto 8bit image

        # subtract adjusted mask from original contour mask
        # should result in original contour, otherwise object not associated with goal pattern
        adjusted_mask = cv2.bitwise_and(adjusted_mask, mask) # 
        present = not(np.bitwise_xor(adjusted_mask,mask).any()) # if any of (adjusted_mask xor mask) are true then present is fals (do not have right shape)

        #print('Adjusted Mask'),
        #print(time.time()-starttime) # 10ms
            
        if present:
                # cv2.imshow('Found', mask)
  
                goalx = moments['m10']/moments['m00']
                goaly = moments['m01']/moments['m00']

                # starttime = time.time()
                
                hist_hue = cv2.calcHist([hsv],[0],mask,[180],[0,180])
                hist_sat = cv2.calcHist([hsv],[1],mask,[256],[0,256])
                hist_val = cv2.calcHist([hsv],[2],mask,[256],[0,256])

                # compute cumulative histogram
                #hist_hue_cs = np.cumsum(hist_hue)
                #hist_hue_cs = hist_hue_cs / hist_hue_cs[179]
                #hist_sat_cs = np.cumsum(hist_sat)
                #hist_sat_cs = hist_sat_cs / hist_sat_cs[255]
                #hist_val_cs = np.cumsum(hist_val)
                #hist_val_cs = hist_val_cs / hist_val_cs[255]
                
                # compute the quantiles
                #low=0.18
                #med=0.5
                #high=0.84
                #hue_low = np.amin(np.where(hist_hue_cs >=low))
                #sat_low = np.amin(np.where(hist_sat_cs >=low))
                #val_low = np.amin(np.where(hist_val_cs >=low))
                #hue_med = np.amin(np.where(hist_hue_cs >=med))
                #sat_med = np.amin(np.where(hist_sat_cs >=med))
                #val_med = np.amin(np.where(hist_val_cs >=med))
                #hue_high = np.amin(np.where(hist_hue_cs >=high))
                #sat_high = np.amin(np.where(hist_sat_cs >=high))
                #val_high = np.amin(np.where(hist_val_cs >=high))
                ## unfortunately this command does not work with mask
                ## p25, p50, p75 = np.percentile(img, (25,50,75))
                
                ## compute the boundaries and keep them wide
                #hue_plus  = max(hue_high-hue_med, 5)
                #hue_minus = max(hue_med-hue_low, 5)
                #sat_plus  = max(sat_high-sat_med, 10)
                #sat_minus = max(sat_med-sat_low, 10)
                #val_plus  = max(val_high-val_med, 10)
                #val_minus = max(val_med-val_low, 10)

                #plus_avg  = lp_filter_array([hue_plus,  sat_plus,  val_plus],   plus_avg, 0.05)
                #med_avg   = lp_filter_array([hue_med,   sat_med,   val_med],     med_avg, 0.05)
                #minus_avg = lp_filter_array([hue_minus, sat_minus, val_minus], minus_avg, 0.05)

                #upper = np.array([int(med_avg[0] + 2.5*plus_avg[0]), int(med_avg[1] + 2.5*plus_avg[1]), int(med_avg[2] + 2.5*plus_avg[2] ) ])
                #lower = np.array([int(med_avg[0] - 2.5*minus_avg[1]), int(med_avg[1] - 2.5*minus_avg[1]), int(med_avg[2] - 2.5*minus_avg[2] ) ])
                #print(upper, lower)

                #Average
                hue_avg=np.sum(hist_hue[:,0] * hue_range)/np.sum(hist_hue) 
                sat_avg=np.sum(hist_sat[:,0] * sat_range)/np.sum(hist_sat)
                val_avg=np.sum(hist_val[:,0] * val_range)/np.sum(hist_val)

                hue_avg = clamp(hue_avg, hue_lower, hue_upper)
                sat_avg = clamp(sat_avg, sat_lower, sat_upper)
                val_avg = clamp(val_avg, val_lower, val_upper)
                
                avg_vals[0] = hue_avg*alpha + avg_vals[0]*(1.0 - alpha)
                avg_vals[1] = sat_avg*alpha + avg_vals[1]*(1.0 - alpha)
                avg_vals[2] = val_avg*alpha + avg_vals[2]*(1.0 - alpha)

                # Standard Deviation
                hue_std= ( np.sum( hist_hue[:,0]*((hue_avg-hue_range)**2) ) / np.sum(hist_hue))**0.5 #
                sat_std= ( np.sum( hist_sat[:,0]*((sat_avg-sat_range)**2) ) / np.sum(hist_sat))**0.5 
                val_std= ( np.sum( hist_val[:,0]*((val_avg-val_range)**2) ) / np.sum(hist_val))**0.5

                hue_std=max(hue_std,hue_std_min)
                sat_std=max(sat_std,sat_std_min)
                val_std=max(val_std,val_std_min)

                avg_stds[0] = hue_std*alpha + avg_stds[0]*(1.0 - alpha)
                avg_stds[1] = sat_std*alpha + avg_stds[1]*(1.0 - alpha)
                avg_stds[2] = val_std*alpha + avg_stds[2]*(1.0 - alpha)

                # Threhshold update
                upper = np.array([int(avg_vals[x] + 2.0*avg_stds[x]) for x in range(3)])
                lower = np.array([int(avg_vals[x] - 2.0*avg_stds[x]) for x in range(3)])
                # print('Histogram Analysis'),
                # print(time.time()-starttime) # 20-40ms
                # print (avg_vals, avg_stds)

                if displayON:
                    for p in range(len(hull)):
                        p1 = (hull[p-1][0][0],hull[p-1][0][1])
                        p2 = (hull[p][0][0], hull[p][0][1])
                        cv2.line(frame, p1, p2, (255,0,0), 2)

                    cv2.drawContours(frame,[adjusted_box],0,(0,0,255),2)
                    cv2.putText(frame, 'Hull:{0:.2f}'.format(hullarea), (10,65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                    cv2.putText(frame, 'Aspect:{0:.1f}'.format(aspect), (10,80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                    cv2.putText(frame, 'Area:{0:.1f}'.format(area), (10,95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                    cv2.putText(frame, 'Moments:{0:.2f}'.format(moments['m00']), (10,110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)

                    cv2.putText(frame, 'H:{0:.1f}'.format(avg_vals[0]), (10,125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                    cv2.putText(frame, 'S:{0:.1f}'.format(avg_vals[1]), (10,140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                    cv2.putText(frame, 'V:{0:.1f}'.format(avg_vals[2]), (10,155), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)

                    cv2.putText(frame, 'H:{0:.1f}'.format(avg_stds[0]), (10,170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                    cv2.putText(frame, 'S:{0:.1f}'.format(avg_stds[1]), (10,185), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                    cv2.putText(frame, 'V:{0:.1f}'.format(avg_stds[2]), (10,200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)

    currtime = time.time()
    fps = 0.7 * fps + 0.3 * (1 / (currtime - oldtime))
    oldtime = currtime
    if displayON:
        cv2.putText(frame, 'X:{0:.2f}'.format(goalx), (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
        cv2.putText(frame, 'Y:{0:.2f}'.format(goaly), (10,35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
        cv2.putText(frame, 'FPS:{0:.2f}'.format(fps), (10,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
        cv2.imshow('frame', frame)
        output.write(frame)

    # print fps

    sd.putNumber('goalx', goalx)
    sd.putNumber('goaly', goaly)
    sd.putNumber('area', hullarea)
    sd.putBoolean('present', present)
    sd.putNumber('time', time.time())

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
if displayON:
    output.release()
cv2.destroyAllWindows()
