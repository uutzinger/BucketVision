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

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from threading import Thread

class HTTPHandler(BaseHTTPRequestHandler):
    
    # Note this is static (class) variable
    jpgSource = None

    
    def do_GET(self):

        print(self.path)
        
        # Respond to URL 'hostname:port/' or 'hostname:port/cam.mjpg'
        if self.path.endswith('/') or self.path.endswith('.mjpg'):
    
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            
            while True:
                
                buf = self.jpgSource.get()
                                              
                self.wfile.write("--jpgboundary\r\n")
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(buf)))
                self.end_headers()
                self.wfile.write(buf)
                self.wfile.write('\r\n')
                
        else:
            self.send_error(404, "Not found")
        

class Server:

    def __init__(self, jpgSource):
        
        print("Creating Server")
        
        # This is an ugly way to do things but have to
        # because 2nd arg to HTTPServer is a class, not an instance
        HTTPHandler.jpgSource = jpgSource
        self.server = HTTPServer(('', 8080), HTTPHandler)
                       
        self.running = False
    
    def start(self):
        print("Server STARTING")
        t = Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return self

    def run(self):
        print("Server RUNNING")
        self.running = True
        self.server.serve_forever()
  
    def isRunning(self):
        return self.running

