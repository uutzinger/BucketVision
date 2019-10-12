import cv2
import numpy as np
import time

cap = cv2.VideoCapture("./bitbuckets.mp4")
output = cv2.VideoWriter("./output.mp4", int(cap.get(cv2.CAP_PROP_FOURCC)),
    int(cap.get(cv2.CAP_PROP_FPS)), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

print "OpenCV Version: {0}".format(cv2.__version__)

oldtime = time.time()
fps = 0.0

while(True):
    ret, frame = cap.read()
    frame = cv2.pyrDown(frame)
	# frame = cv2.pyrDown(frame)

    hsv = cv2.blur(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV), (5,5))

    cv2.imshow('hsv', hsv)
    
	# From ImageJ 
	# H  90-145 [0..255] 63..103 [0..180]
	# S  30-120 [0..255] 
	# V 140-210 [0..255] 
    lower = np.array([ 63,  30,  140])
    upper = np.array([103, 120,  240])
	
    hsvthresh = cv2.inRange(hsv, lower, upper)

    cv2.imshow('thresh', hsvthresh)

    im2, contours, hierarchy = cv2.findContours(hsvthresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)

    for contour in contours:
        moments = cv2.moments(contour)

        if moments['m00'] > 0:
            area = cv2.contourArea(contour)
            perim = cv2.arcLength(contour, True)
            goalx = moments['m10']/moments['m00']
            goaly = moments['m01']/moments['m00']

            hull = cv2.convexHull(contour)
            hullarea = cv2.contourArea(hull)
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            boxarea = cv2.contourArea(box)

			# Need to Optimize hullarea threshold as that depends on camera
            if boxarea > 0 and hullarea/area > 2.0 and hullarea/area < 4.5 and hullarea/boxarea > 0.6 and hullarea > 400:
                cv2.putText(frame, 'X:{0:.2f}'.format(goalx), (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                cv2.putText(frame, 'Y:{0:.2f}'.format(goaly), (10,35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                cv2.putText(frame, 'AREA:{0:.2f}'.format(hullarea), (10,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2, cv2.LINE_AA)
                for p in range(len(hull)):
                    p1 = (hull[p-1][0][0],hull[p-1][0][1])
                    p2 = (hull[p][0][0], hull[p][0][1])
                    cv2.line(frame, p1, p2, (255,0,0), 2)

    cv2.imshow('frame', frame)
    output.write(frame)

    currtime = time.time()
    fps = 0.9 * fps + 0.1 * (1 / (currtime - oldtime))
    print "Framerate: {0}".format(fps)
    oldtime = currtime

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
output.release()
cv2.destroyAllWindows()
