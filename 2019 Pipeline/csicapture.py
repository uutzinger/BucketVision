# Multi Threading
from threading import Thread
from threading import Lock
#
import logging
import time
# Open Computer Vision
import cv2
# Camera    
from picamera.array import PiRGBArray
from picamera import PiCamera
# Bucketvision Camerra
from configs import configs
# Networktables
try:
    import networktables
except ImportError:
    pass

class CSICapture(Thread):
    def __init__(self, camera_num=0, res=None, network_table=None, exposure=None, frate=None):
        #
        self.logger     = logging.getLogger("CSICapture{}".format(camera_num))
        self.camera_num = camera_num
        self.net_table  = network_table
        # Threading Locks
        self.capture_lock = Lock()
        self.frame_lock   = Lock()

        #
        # PiCamera
        #
        self.camera      = PiCamera(self.camera_num)
        self.camera_open = not self.camera.closed
        if self.camera_open is False: self.write_table_value("Camera{}Status".format(camera_num), "Failed to open camera {}!".format(camera_num), level=logging.CRITICAL)
        # Resolution
        if res is not None:  
            self.resolution = res
        else: self.resolution = configs['camera_res']
        # Buffer
        self.rawCapture = PiRGBArray(self.camera, size=self.resolution)
        # Exposure Time
        if exposure is not None:  
            self._exposure = exposure
        else: self._exposure = configs['CSIexposure']
        self.exposure = self._exposure
        # Frame Rate
        if frate is not None:
            self.framerate = frate
        else: self.framerate = configs['CSIframerate']
        # Turn Off Auto Features
        self.awb_mode     = 'off'            # No auto white balance
        self.awb_gains    = (1,1)            # Gains for red and blue are 1
        self.brightness   = 50               # No change in brightness
        self.contrast     = 0                # No change in contrast
        self.drc_strength = 'off'            # Dynamic Range Compression off
        self.clock_mode   = 'raw'            # Frame numbers since opened camera
        self.color_effects = None            # No change in color
        self.fash_mode    = 'off'            # No flash
        self.image_denoise = False           # In vidoe mode
        self.image_effect = 'none'           # No image effects
        self.sharpness    = 0                # No changes in sharpness
        self.video_stabilization = False     # No image stablization
        self.iso          = 100              # Use ISO 100 setting, smallest analog and digital gains
        self.exposure_mode = 'off'           # No automatic exposure control
        self.exposure_compensation = 0       # No automatic expsoure controls compensation
        try:
            self.stream = self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True)
        except:
            self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to create camera stream {}!".format(self.camera_num), level=logging.CRITICAL)

        # Init Frame and Thread
        self._frame     = None
        self._new_frame = False
        self.stopped    = False
        Thread.__init__(self)
    #
    # Frame routines ##################################################
    #
    @property
    # reads most recent frame
    def frame(self):
        with self.frame_lock: 
            self._new_frame = False
        return self._frame
    @property
    # check if new frame available
    def new_frame(self):
        out = False
        with self.frame_lock: 
            out = self._new_frame
        return out
    @new_frame.setter
    # sets wether new frame is available
    def new_frame(self, val):
        with self.frame_lock: 
            self._new_frame = val

    #
    # Network Table routines ##########################################
    #
    def write_table_value(self, name, value, level=logging.DEBUG):
        self.logger.log(level, "{}:{}".format(name, value))
        if self.net_table is None:
            self.net_table = dict()
        if type(self.net_table) is dict:
            self.net_table[name] = value
        else:
            self.net_table.putValue(name, value)

    #
    # Thread routines #################################################
    #
    def stop(self): 
        self.stopped = True

    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # Contents of thread
        first_frame = True
        start_time = time.time()
        num_frames = 0
        img = None
        for f in self.stream: 
            # FPS calculation
            if (time.time() -  start_time) >= 5.0:
                print("CSI{} frames captured: {:.1f}/s".format(self.camera_num, num_frames/5.0))
                num_frames = 0
                start_time = time.time()
            # Adjust exposure if requested via network tables
            try:
                if self._exposure != self.net_table.getEntry("Exposure").value: 
                    self.exposure = self.net_table.getEntry("Exposure").value
            except: pass
            # Get latest image
            with self.capture_lock:
                img = f.array
                self.rawCapture.truncate(0)
            # Adjust image size: crop top and bottom
            with self.frame_lock:
                self._frame = img[int(self._resolution[1]*(configs['crop_top'])):int(self._resolution[1]*(configs['crop_bot'])), :, :]
                if first_frame:
                    first_frame = False
                    print(img.shape, self._frame.shape)
                self._new_frame = True
            num_frames = num_frames + 1
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()        
    
    #
    # Camera Essentials ################################################
    #
    # Resolutions Frame Rate
    # 1920, 1080  1..30
    # 1640, 1232  1/10..40
    # 1640,  922  1/10..40
    # 1280,  720  40..90
    # 1296,  730  1..90
    #  640,  480  1/500..90
    # write shutter_speed  sets exposure in microseconds
    # read  exposure_speed gives actual exposure 
    # shutter_speed = 0 then auto exposure
    # framerate determines maximum exposure
    # Read
    @property
    def resolution(self):            
        if self.camera_open: 
            with self.capture_lock: return self.camera.resolution                            
        else: return float("NaN")
    @property
    def width(self):                 
        if self.camera_open: 
            with self.capture_lock: return self.camera.resolution[0]
        else: return float("NaN")
    @property
    def height(self):                
        if self.camera_open: 
            with self.capture_lock: return self.camera.resolution[1]                         
        else: return float("NaN")
    @property
    def framerate(self):             
        if self.camera_open: 
            with self.capture_lock: return self.camera.framerate+self.camera.framerate_delta 
        else: return float("NaN")
    @property
    def exposure(self):              
        if self.camera_open: 
            with self.capture_lock: return self.camera.exposure_speed                        
        else: return float("NaN")
    # Write
    @resolution.setter
    def resolution(self, val):
        if val is None:
            return
        if self.camera_open:
            with self.capture_lock:
                if len(val) > 1:
                    self.camera.resolution = val
                    self.write_table_value("Width",  val[0])
                    self.write_table_value("Height", val[1])
                    self._resolution = val
                else:
                    self.camera.resolution = (val, val)
                    self.write_table_value("Width",  val)
                    self.write_table_value("Height", val)
                    self._resolution = (val, val)                    
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Resolution to {}!".format(val), level=logging.CRITICAL)
    @width.setter
    def width(self, val):
        if val is None:
            return
        val = int(val)
        if self.camera_open:
            with self.capture_lock:
                self.camera.resolution = (val, self.camera.resolution[1])
                self.write_table_value("Width", val)
                self._resolution = (val, self.camera.resolution[1])
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Width to {}!".format(val), level=logging.CRITICAL)
    @height.setter
    def height(self, val):
        if val is None:
            return
        val = int(val)
        if self.camera_open:
            with self.capture_lock:
                self.camera.resolution = (self.camera.resolution[0], val)
                self.write_table_value("Height", val)
                self._resolution = (self.camera.resolution[0], val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Height to {}!".format(val), level=logging.CRITICAL)
    @framerate.setter
    def framerate(self, val):
        if val is None:
            return
        val = float(val)
        if self.camera_open:
            with self.capture_lock:
                self.camera.framerate = val
                self.write_table_value("Framerate", val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Framerate to {}!".format(val), level=logging.CRITICAL)
    @exposure.setter
    def exposure(self, val):
        if val is None:
            return
        if self.camera_open:
            with self.capture_lock:
                self.camera.shutter_speed  = val
                print("Exposure set to: {}".format(val))
            self.write_table_value("Exposure", val)
            self._exposure = self.exposure
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Exposure to {}!".format(val), level=logging.CRITICAL)

    #
    # Color Balancing ##################################################
    #
    # Cannot set digital and analog gains, set ISO then read the gains.
    # awb_mode: can be off, auto, sunLight, cloudy, share, tungsten, fluorescent, flash, horizon, default is auto
    # analog gain: retreives the analog gain prior to digitization
    # digital gain: applied after conversion, a fraction
    # awb_gains: 0..8 for red,blue, typical values 0.9..1.9 if awb mode is set to "off:
    # Read
    @property
    def awb_mode(self):              
        if self.camera_open: 
            with self.capture_lock: return self.camera.awb_mode               
        else: return float('NaN')
    @property
    def awb_gains(self):             
        if self.camera_open: 
            with self.capture_lock: return self.camera.awb_gains              
        else: return float('NaN')
    @property
    def analog_gain(self):           
        if self.camera_open: 
            with self.capture_lock: return self.camera.analog_gain           
        else: return float("NaN")
    @property
    def digital_gain(self):          
        if self.camera_open: 
            with self.capture_lock: return self.camera.digital_gain           
        else: return float("NaN")
    # Write
    @awb_mode.setter
    def awb_mode(self, val):
        if val is None: return
        if self.camera_open:
            with self.capture_lock:
                self.camera.awb_mode  = val
                self.write_table_value("AWB Mode", val)
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set AWB Mode to {}!".format(val), level=logging.CRITICAL)
    @awb_gains.setter
    def awb_gains(self, val):
        if val is None:
            return
        if self.camera_open:
            with self.capture_lock:
                if len(val) > 1:
                    self.camera.awb_gains  = val
                    self.write_table_value("AWB Gains", val)
                else:
                    self.camera.awb_gains = (val, val)
                    self.write_table_value("AWB Gains", (val, val))
        else:
            self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set AWB Gains to {}!".format(val), level=logging.CRITICAL)
    # Can not set analog and digital gains, needs special code
    #@analog_gain.setter
    #@digital_gain.setter

    #
    # Intensity and Contrast ###########################################
    #
    # brightness 0..100 default 50
    # contrast -100..100 default is 0
    # drc_strength is dynamic range compression strength; off, low, medium, high, default off
    # iso 0=auto, 100, 200, 320, 400, 500, 640, 800, on some cameras iso100 is gain of 1 and iso200 is gain for 2
    # exposure mode can be off, auto, night, nightpreview, backight, spotlight, sports, snow, beach, verylong, fixedfps, antishake, fireworks, default is auto, off fixes the analog and digital gains
    # exposure compensation -25..25, larger value gives brighter images, default is 0
    # meter_mode'average', 'spot', 'backlit', 'matrix'
    # Read
    @property
    def brightness(self):            
        if self.camera_open: 
            with self.capture_lock: return self.camera.brightness             
        else: return float('NaN')
    @property
    def iso(self):                   
        if self.camera_open: 
            with self.capture_lock: return self.camera.iso                    
        else: return float("NaN")
    @property
    def exposure_mode(self):         
        if self.camera_open: 
            with self.capture_lock: return self.camera.exposure_mode          
        else: return float("NaN")
    @property
    def exposure_compensation(self): 
        if self.camera_open: 
            with self.capture_lock: return self.camera.exposure_compensation  
        else: return float("NaN")
    @property
    def drc_strength(self):          
        if self.camera_open: 
            with self.capture_lock: return self.camera.drc_strength           
        else: return float('NaN')
    @property
    def contrast(self):              
        if self.camera_open: 
            with self.capture_lock: return self.camera.contrast               
        else: return float('NaN')
    # Write
    @brightness.setter
    def brightness(self, val):
        if val is None:  return
        val = int(val)
        if self.camera_open:
            with self.capture_lock:
                self.camera.brightness = val
                self.write_table_value("Brightness", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Brightness to {}!".format(val), level=logging.CRITICAL)    
    @iso.setter
    def iso(self, val):
        if val is None: return
        val = int(val)
        if self.camera_open:
            with self.capture_lock:
                self.camera.iso = val
                self.write_table_value("ISO", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set ISO to {}!".format(val), level=logging.CRITICAL)
    @exposure_mode.setter
    def exposure_mode(self, val):
        if val is None: return
        if self.camera_open:
            with self.capture_lock:
                self.camera.exposure_mode = val
                self.write_table_value("Exposure Mode", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Exposure Mode to {}!".format(val), level=logging.CRITICAL)
    @exposure_compensation.setter
    def exposure_compensation(self, val):
        if val is None: return
        val = int(val)
        if self.camera_open:
            with self.capture_lock:
                self.camera.exposure_compensation = val
                self.write_table_value("Exposure Compensation", int(val))
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Exposure Compensation to {}!".format(val), level=logging.CRITICAL)
    @drc_strength.setter
    def drc_strength(self, val):
        if val is None: return
        if self.camera_open:
            with self.capture_lock:
                self.camera.drc_strength = val
                self.write_table_value("DRC Strength", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set DRC Strength to {}!".format(val), level=logging.CRITICAL)
    @contrast.setter
    def contrast(self, val):
        if val is None: return
        val = int(val)
        if self.camera_open:
            with self.capture_lock:
                self.camera.contrast = val
                self.write_table_value("Contrast", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Contrast to {}!".format(val), level=logging.CRITICAL)

    #
    # Other Effects ####################################################
    #
    # flash_mode
    # clock mode "reset", is relative to start of recording, "raw" is relative to start of camera
    # color_effects, "None" or (u,v) where u and v are 0..255 e.g. (128,128) gives black and white image
    # flash_mode 'off', 'auto', 'on', 'redeye', 'fillin', 'torch' defaults is off
    # image_denoise, True or False, activates the denosing of the image
    # video_denoise, True or False, activates the denosing of the video recording
    # image_effect, can be negative, solarize, sketch, denoise, emboss, oilpaint, hatch, gpen, pastel, watercolor, film, blur, saturation, colorswap, washedout, colorpoint, posterise, colorbalance, cartoon, deinterlace1, deinterlace2, default is 'none'
    # image_effect_params, setting the parameters for the image effects see https://picamera.readthedocs.io/en/release-1.13/api_camera.html
    # sharpness -100..100 default 0
    # video_stabilization default is False
    # Read
    @property
    def flash_mode(self):            
        if self.camera_open: 
            with self.capture_lock: return self.camera.flash_mode             
        else: return float('NaN')
    @property
    def clock_mode(self):            
        if self.camera_open: 
            with self.capture_lock: return self.camera.clock_mode             
        else: return float('NaN')
    @property
    def sharpness(self):             
        if self.camera_open: 
            with self.capture_lock: return self.camera.sharpness              
        else: return float('NaN')
    @property
    def color_effects(self):         
        if self.camera_open: 
            with self.capture_lock: return self.camera.color_effects           
        else: return float('NaN')
    @property
    def image_effect(self):          
        if self.camera_open: 
            with self.capture_lock: return self.camera.image_effect           
        else: return float('NaN')
    @property
    def image_denoise(self):         
        if self.camera_open: 
            with self.capture_lock: return self.camera.image_denoise          
        else: return float('NaN')
    @property
    def video_denoise(self):         
        if self.camera_open: 
            with self.capture_lock: return self.camera.video_denoise          
        else: return float('NaN')
    @property
    def video_stabilization(self):   
        if self.camera_open: 
            with self.capture_lock: return self.camera.video_stabilization    
        else: return float('NaN')
    # Write
    @flash_mode.setter
    def flash_mode(self, val):
        if val is None:  return
        if self.camera_open:
            with self.capture_lock:
                self.camera.flash_mode = val
                self.write_table_value("Flash Mode", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Flash Mode to {}!".format(val), level=logging.CRITICAL)
    @clock_mode.setter
    def clock_mode(self, val):
        if val is None:  return
        if self.camera_open:
            with self.capture_lock:
                self.camera.clock_mode = val
                self.write_table_value("Clock Mode", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Clock Mode to {}!".format(val), level=logging.CRITICAL)
    @sharpness.setter
    def sharpness(self, val):
        if val is None:  return
        if self.camera_open:
            with self.capture_lock:
                self.camera.sharpness = val
                self.write_table_value("Sharpness", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Sharpness to {}!".format(val), level=logging.CRITICAL)
    @color_effects.setter
    def color_effects(self, val):
        if val is None:  return
        if self.camera_open:
            with self.capture_lock:
                self.camera.color_effects = val
                self.write_table_value("Color Effects", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Color Effects to {}!".format(val), level=logging.CRITICAL)
    @image_effect.setter
    def image_effect(self, val):
        if val is None:  return
        if self.camera_open:
            with self.capture_lock:
                self.camera.image_effect = val
                self.write_table_value("Image Effect", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Image Effect to {}!".format(val), level=logging.CRITICAL)
    @image_denoise.setter
    def image_denoise(self, val):
        if val is None:  return
        if self.camera_open:
            with self.capture_lock:
                self.camera.image_denoise = val
                self.write_table_value("Image Denoise", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Image Denoise to {}!".format(val), level=logging.CRITICAL)
    @video_denoise.setter
    def video_denoise(self, val):
        if val is None:  return
        if self.camera_open:
            with self.capture_lock:
                self.camera.video_denoise = val
                self.write_table_value("Video Denoise", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Video Denoise to {}!".format(val), level=logging.CRITICAL)
    @video_stabilization.setter
    def video_stabilization(self, val):
        if val is None:  return
        if self.camera_open:
            with self.capture_lock:
                self.camera.video_stabilization = val
                self.write_table_value("Video Stablilization", val)
        else: self.write_table_value("Camera{}Status".format(self.camera_num), "Failed to set Video Stabilization to {}!".format(val), level=logging.CRITICAL)

#
# Main ################################################################
#

if __name__ == '__main__':
    from networktables import NetworkTables
    logging.basicConfig(level=logging.DEBUG)

    NetworkTables.initialize(server='localhost')

    VisionTable = NetworkTables.getTable("BucketVision")
    VisionTable.putString("BucketVisionState", "Starting")
    FrontCameraTable = VisionTable.getSubTable('FrontCamera')

    print("Starting Capture")
    camera = CSICapture(network_table=FrontCameraTable)
    camera.start()

    print("Getting Frames")
    while True:
        if camera.new_frame:
            cv2.imshow('my picam', camera.frame)
            #temp = camera.frame
        if cv2.waitKey(1) == 27:
            break  # esc to quit
    camera.stop()
