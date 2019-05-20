###############################################################################
# file:    PCA_onfiles.py                                                     #
# authors: BitBuckets FRC 4183                                                #
#          Urs Utzinger                                                       #
# date:    April 24th 2019                                                    #
# brief:   This file opens various images and computes the least correlated   #
#          color conversion of an RGB image. Principal Component Analsis on   #
#          the RGB values is used, which when using a custom illuminaiton     #
#          light source should result in the main component being the image   #
#          created by the lightsource without the background caused by        #
#          regular ilumination                                                #
###############################################################################

###############################################################################
# Novel PCA-based color-to-gray image conversion
#
###############################################################################
folder = 'D:/GitHub/Python Playground/BucketVision/2019 Pipeline - mp/img/2/t'
###############################################################################
# Imports
#
# Execution
import os
import time
# Math
import numpy as np
# Vision
import cv2
# Graphics
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

###############################################################################
def display_scaled_image(name, image, scale):
    height, width = image.shape[:2]
    cv2.imshow(name, cv2.resize(image,
            (int(scale * width), int(scale * height)),
            interpolation=cv2.INTER_CUBIC))

###############################################################################
files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
images = [f for f in files if f.endswith(".png")]
if True:
    data = np.zeros((1,3))
    for imagepath in images:
        print(imagepath)
        img = cv2.imread(imagepath)
        #cv2.imshow('IMG',img)
        #cv2.waitKey(0)
        s   = img.shape
        img = np.reshape(img,(s[0]*s[1],s[2]))  
        data= np.concatenate((data, img), axis=0)
else:
    img=cv2.imread(images[0])
    s=img.shape
    data = np.reshape(img,(s[0]*s[1],s[2]))

# calculate the mean of each column
# M = np.mean(data, axis=0)
# center columns by subtracting column means
# data = data - M

# Covariance data.T.dot(data)
V=np.cov(data.T)
# eigenvalues and eigenvectors
values, vectors = np.linalg.eig(V)
# sort eigenvectors based on eigen values
index=np.argsort(-values)
vectors=vectors[:,index]
values=values[index]
# invert vectors  so that large numbers are positive
invert=(abs(vectors.max(0)) < abs(vectors.min(0)))
if invert[0] == True:
    vectors[:,0] = -vectors[:,0]

if invert[1] == True:
    vectors[:,1] = -vectors[:,1]

if invert[2] == True:
    vectors[:,2] = -vectors[:,2]

# project data onto eigenvectors
P=data.dot(vectors)

# compute explained variance
Vp=np.cov(P.T)
variance_explained = np.diag(Vp)
variance_explained = variance_explained / variance_explained.sum()

# Save eigenvectors
# vectors=(vectors*127).round().astype(np.int8)
np.savetxt('ColorVectors_2_t.txt', vectors)

###############################################################################
# Plot subset of data

# data of interest >2% <99.9%, removes bg and satturated pixesl
p=np.percentile(data,(2,99.9),axis=0)
p[0,:] = p[0,:]*2
ok0 = (data[:,0] > p[0,0]) & (data[:,0] < p[1,0])
ok1 = (data[:,1] > p[0,1]) & (data[:,1] < p[1,1])
ok2 = (data[:,2] > p[0,2]) & (data[:,2] < p[1,2])
ok = ok0 & ok1 & ok2
idx = np.arange(s[0]*s[1])
idx = idx[ok]
# can not plot more than 10,000 data points
idxr=np.random.choice(idx,10000)
fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
ax = fig.gca(projection='3d')
x=data[idxr,0]
y=data[idxr,1]
z=data[idxr,2]
ax.scatter(x,y,z, c='r', marker='o')
ax.quiver(0, 0, 0, vectors[0,:], vectors[1,:], vectors[2,:], length = 150, normalize = True)
ax.set_xlabel('Blue')
ax.set_ylabel('Green')
ax.set_zlabel('Red')
plt.show()

###############################################################################
# create projected image
Pimg=P.reshape(s)

# scale and display
tmp=Pimg[:,:,0]
mi = tmp.min()
ma = tmp.max()
tmp0=(tmp-mi)/(ma-mi)
display_scaled_image('Projected 0', tmp0, 0.5)
#imshow('Projected 0 ',tmp0)
cv2.imwrite("Projected0.png",tmp0)

tmp=Pimg[:,:,1]
mi = tmp.min()
ma = tmp.max()
tmp1=(tmp-mi)/(ma-mi)
display_scaled_image('Projected 1', tmp1, 0.5)
#imshow('Projected 1 ',tmp)
cv2.imwrite("Projected1.png",tmp1)

tmp=Pimg[:,:,2]
mi = tmp.min()
ma = tmp.max()
tmp2=(tmp-mi)/(ma-mi)
display_scaled_image('Projected 2', tmp2, 0.5)
# imshow('Projected 2 ',tmp)
cv2.imwrite("Projected2.png",tmp2)

# save projected image
tmp = zeros(s)
tmp[:,:,0]=tmp0
tmp[:,:,1]=tmp1
tmp[:,:,2]=tmp2
display_scaled_image('Projected All', tmp, 0.5)

cv2.imwrite("Projected.png",tmp)

waitKey(0)

###############################################################################
# Eigenvector 2
# 26ms
data0=img[:,:,0]*vectors[0,1]
data1=img[:,:,1]*vectors[1,1]
data2=img[:,:,2]*vectors[2,1]
data = (data0 + data1 + data2)
mi = data.min()
ma = data.max()
tmp=(data-mi)/(ma-mi)
display_scaled_image('Projected', tmp, 0.5)

start = time.perf_counter()
#7.3ms
for i in range(10000):
    HSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

end=time.perf_counter()
(end-start)/10000

# with lookup table
# 50ms
factors = vectors[:,1]
r= np.arange(0,256,dtype=np.int16)
lutB = (r*10. * factors[0]).astype(np.int16)
lutG = (r*10. * factors[1]).astype(np.int16)
lutR = (r*10. * factors[2]).astype(np.int16)
start = time.perf_counter()
for i in range(1000):
    dataC = ((lutB[img[:,:,0]] + lutG[img[:,:,1]] + lutR[img[:,:,2]])/10)

end=time.perf_counter()
(end-start)/1000

# with cv2 lookup table
# 21ms
factors = vectors[:,1]
r= np.arange(0,256,dtype=np.int16)
lutB = (r*10. * factors[0]).astype(np.int16)
lutG = (r*10. * factors[1]).astype(np.int16)
lutR = (r*10. * factors[2]).astype(np.int16)
lut=np.array([lutB,lutG,lutR])
start = time.perf_counter()
for i in range(1000):
    dataC=cv2.LUT(img[:,:,0],lutB)+cv2.LUT(img[:,:,1],lutG)+cv2.LUT(img[:,:,2],lutR)

end=time.perf_counter()
(end-start)/1000

# 8.7ms float64
# 8.8ms float32
factors = vectors[:,1]
m=np.array([[factors[0],factors[1],factors[2]]],dtype='float32')
start = time.perf_counter()
for i in range(10000):
    gray = cv2.transform(img,m)

end=time.perf_counter()
(end-start)/10000

#integer math
# 9ms
mi=np.int16(m*255)
imgi=np.int16(img)
start = time.perf_counter()
for i in range(10000):
    grayi = cv2.transform(imgi,mi)

end=time.perf_counter()
(end-start)/10000

#########################################################################

####
# Run Above for all directories and then combine
####

# Load all results
v01=np.loadtxt('ColorVectors_1_a.txt')
v02=np.loadtxt('ColorVectors_1_b.txt')
v03=np.loadtxt('ColorVectors_1_c.txt')
v04=np.loadtxt('ColorVectors_1_d.txt')
v05=np.loadtxt('ColorVectors_2_a.txt')
v06=np.loadtxt('ColorVectors_2_b.txt')
v07=np.loadtxt('ColorVectors_2_c.txt')
v08=np.loadtxt('ColorVectors_2_d.txt')
v09=np.loadtxt('ColorVectors_2_e.txt')
v10=np.loadtxt('ColorVectors_2_f.txt')
v11=np.loadtxt('ColorVectors_2_g.txt')
v12=np.loadtxt('ColorVectors_2_h.txt')
v13=np.loadtxt('ColorVectors_2_i.txt')
v14=np.loadtxt('ColorVectors_2_j.txt')
v15=np.loadtxt('ColorVectors_2_k.txt')
v16=np.loadtxt('ColorVectors_2_l.txt')
v17=np.loadtxt('ColorVectors_2_m.txt')
v18=np.loadtxt('ColorVectors_2_n.txt')
v19=np.loadtxt('ColorVectors_2_o.txt')
v20=np.loadtxt('ColorVectors_2_p.txt')
v21=np.loadtxt('ColorVectors_2_q.txt')
v22=np.loadtxt('ColorVectors_2_r.txt')
v23=np.loadtxt('ColorVectors_2_s.txt')
v24=np.loadtxt('ColorVectors_2_u.txt')
v25=np.loadtxt('ColorVectors_2_v.txt')
v26=np.loadtxt('ColorVectors_2_w.txt')
v27=np.loadtxt('ColorVectors_2_x.txt')
v28=np.loadtxt('ColorVectors_2_y.txt')

v=np.array([v01,v02,v03,v04,v05,v06,v07,v08,v09,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,v21,v22,v23,v24,v25,v26,v27,v28])

# Find outlayers
m=np.mean(v,0)
s=np.std(v,0)
# Need to be within +/-2std
ok = ((v>m-2*s) & (v<m+2*s))
l=np.ones(ok.shape[0])
for i in np.arange(ok.shape[0]):
    if sum(sum(ok[i,::])) == 9:
        l[i] = 1
    else:
        l[i] = 0

#Keep the ones in the range
vok=v[l==1,:,:]
m=np.mean(vok,0)
s=np.std(vok,0)

# repeat above
ok = ((vok>m-2*s) & (vok<m+2*s))
l=np.ones(ok.shape[0])
for i in np.arange(ok.shape[0]):
    if sum(sum(ok[i,::])) == 9:
        l[i] = 1
    else:
        l[i] = 0

# Final selection of vectors
vok=vok[l==1,:,:]
m=np.mean(vok,0)
s=np.std(vok,0)
# Make sure the vector length / norm is 1
n=np.linalg.norm(m,axis=0)
m=m/n
np.savetxt('All.txt', m)
