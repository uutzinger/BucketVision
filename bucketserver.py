# -*- coding: utf-8 -*-
"""
bucketserver

Simple web service for image

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

import cv2

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

from threading import Thread
        
class BucketServer:

    def __init__(self,name,httpserver):
        self.name= name
        self.server = httpserver
        print("Creating BuckerServer for " + self.name)
                
        # initialize the variable used to indicate if the thread should
        # be stopped
        self._stop = False
        self.stopped = True

        print("BucketServerImageProcessor created for " + self.name)
    
    def start(self):
        print("STARTING BucketServer for " + self.name)
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        print("BuckerServer for " + self.name + " RUNNING")
        

        self.stopped = False

        
        self.server.serve_forever()  # Until shutdown is commanded
        
        self._stop = False
        self.stopped = True
                
        print("BucketServer for " + self.name + " STOPPING")
    
    def stop(self):
        # indicate that the thread should be stopped
        self._stop = True
        self.server.shutdown()

    def isStopped(self):
        return self.stopped

