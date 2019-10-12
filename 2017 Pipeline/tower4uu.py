import cv2
import numpy as np
from matplotlib.pyplot import plot, show, draw, clf, hist, figure
import time
import sys

def avg_hist(hist, length):
    val = 0
    count = 0
    for i in range(length):
        count += hist[i]
        val += i * hist[i]
    return val/count

def std_dev_hist(hist, length):
    avg = avg_hist(hist, length)
    count = 0
    sqerr = 0
    for i in range(length):
        count += hist[i]
        sqerr += hist[i] * (avg-i)**2
    return (sqerr / count)**0.5

def lp_filter_array(new, old, alpha=0.05):
    res = []
    for x in range(len(new)):
        res.append(new[x]*alpha + old[x]*(1.0 - alpha))
    return res

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)      
    
cap = cv2.VideoCapture("./bitbuckets.mp4")
# cap = cv2.VideoCapture("./dropshot.mp4")
output = cv2.VideoWriter("./output.mp4", int(cap.get(cv2.CAP_PROP_FOURCC)),
    int(cap.get(cv2.CAP_PROP_FPS)), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

print("FourCC: {0}".format(int(cap.get(cv2.CAP_PROP_FOURCC))))
print("FPS: {0}".format(int(cap.get(cv2.CAP_PROP_FPS))))
print("OpenCV Version: {0}".format(cv2.__version__))

oldtime = time.time()
fps = 0.0

# avg_vals = [70,180,220] #for dropshot
# avg_stds = [10, 20, 10]
avg_vals = [80,60,180]  #for bitbuckets
avg_stds = [5, 15, 20]
upper = np.array([int(avg_vals[x] + 2.5*avg_stds[x]) for x in range(3)])
lower = np.array([int(avg_vals[x] - 2.5*avg_stds[x]) for x in range(3)])

#plus_avg = avg_stds
#med_avg = avg_vals
#minus_avg = avg_stds

hue_l=[80]
sat_l=[60]
vals_l=[180]

while(True):
    ret, frame = cap.read()
    frame = cv2.pyrDown(frame)

    hsv = cv2.blur(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV), (5,5))

    # cv2.imshow('hsv', hsv)

    hsvthresh = cv2.inRange(hsv, lower, upper)
    mask = cv2.bitwise_and(hsv, hsv, mask=hsvthresh)

    cv2.imshow('thresh', hsvthresh)
    cv2.imshow('mask', mask)

    im2, contours, hierarchy = cv2.findContours(hsvthresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

    goalx = -1
    goaly = -1

    for contour in contours:
        moments = cv2.moments(contour)

        if moments['m00'] > 0:
            area = cv2.contourArea(contour)
            perim = cv2.arcLength(contour, True)

            if area < 100:
                continue

            hull = cv2.convexHull(contour)
            hullarea = cv2.contourArea(hull)
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            boxarea = cv2.contourArea(box)

            aspect = rect[1][1]/rect[1][0]

            adjusted_rect = rect
            adjusted_rect = ((rect[0][0], rect[0][1]-rect[1][0]*0.15), (adjusted_rect[1][0] * 0.40, adjusted_rect[1][1] * 0.40), rect[2])
            adjusted_box = cv2.boxPoints(adjusted_rect)
            adjusted_box = np.int0(adjusted_box)
            adjusted_mask = np.zeros(hsvthresh.shape,np.uint8)
            cv2.drawContours(adjusted_mask,[adjusted_box],0,255,-1)
            adjusted_mask = cv2.bitwise_not(adjusted_mask, adjusted_mask)

            mask = np.zeros(hsvthresh.shape,np.uint8)
            cv2.drawContours(mask,[contour],0,255,-1)
            # pixelpoints = np.transpose(np.nonzero(mask))
            # cv2.imshow('points', mask)
            adjusted_mask = cv2.bitwise_and(adjusted_mask, mask)
            # cv2.imshow('adjusted', cv2.bitwise_xor(adjusted_mask, mask))
            present = not(np.bitwise_xor(adjusted_mask,mask).any())

            if present and aspect > 0.4 and aspect < 2.5 and hullarea > 500:
                goalx = moments['m10']/moments['m00']
                goaly = moments['m01']/moments['m00']
                cv2.drawContours(frame,[adjusted_box],0,(0,0,255),2)
                cv2.putText(frame, 'AREA:{0:.2f}'.format(hullarea), (10,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                hist_hue = cv2.calcHist([hsv],[0],mask,[180],[0,180])
                hist_sat = cv2.calcHist([hsv],[1],mask,[256],[0,256])
                hist_val = cv2.calcHist([hsv],[2],mask,[256],[0,256])

                # compute cumulative histogram
                hist_hue_cs = np.cumsum(hist_hue)
                hist_hue_cs = hist_hue_cs / hist_hue_cs[179]
                hist_sat_cs = np.cumsum(hist_sat)
                hist_sat_cs = hist_sat_cs / hist_sat_cs[255]
                hist_val_cs = np.cumsum(hist_val)
                hist_val_cs = hist_val_cs / hist_val_cs[255]
                
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
                

                avg_vals = lp_filter_array(
                    [clamp(avg_hist(hist_hue, 180)[0],  82,  98), 
                    clamp(avg_hist(hist_sat, 256)[0] ,  60, 95),
                    clamp(avg_hist(hist_val, 256)[0], 150, 230)],
                    avg_vals)
                avg_stds = lp_filter_array(
                    [max(std_dev_hist(hist_hue, 180)[0], 5),
                    max(std_dev_hist(hist_sat, 256)[0], 10),
                    max(std_dev_hist(hist_val, 256)[0], 15)],
                    avg_stds)
                upper = np.array([int(avg_vals[x] + 2.5*avg_stds[x]) for x in range(3)])
                lower = np.array([int(avg_vals[x] - 2.5*avg_stds[x]) for x in range(3)])
                print (avg_vals, avg_stds)
                
                hue_l.append(avg_vals[0])
                sat_l.append(avg_vals[1])
                vals_l.append(avg_vals[2])
                
                #clf()
                #plot(hist_hue, color='r')
                #plot(hist_sat, color='g')
                #plot(hist_val, color='b')
                #show(block=False)
                
                for p in range(len(hull)):
                    p1 = (hull[p-1][0][0],hull[p-1][0][1])
                    p2 = (hull[p][0][0], hull[p][0][1])
                    cv2.line(frame, p1, p2, (255,0,0), 2)

    cv2.putText(frame, 'X:{0:.2f}'.format(goalx), (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
    cv2.putText(frame, 'Y:{0:.2f}'.format(goaly), (10,35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
    cv2.imshow('frame', frame)
    output.write(frame)

    currtime = time.time()
    fps = 0.9 * fps + 0.1 * (1 / (currtime - oldtime))
    #print "Framerate: {0}".format(fps)
    oldtime = currtime

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

figure()
hist(np.asarray(hue_l))
figure()
hist(np.asarray(sat_l))
figure()
hist(np.asarray(vals_l))
show();

# reasonable values for average hue, sat and vals are
# 77-101 max at 93 limit 82-98
# 62-105 max at 72 limit 60-95
# 150-230 max at 190 limit 150-230
# Start was [80,60,180]

cap.release()
output.release()
cv2.destroyAllWindows()
