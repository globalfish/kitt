#
# Car sensor demo using OpenCV
#
# Author: vswamina, Sept 2017.
# 2017_09_09 Created from code in globalfish/FaceTracker

# With a lot of help from the Internet
import cv2
import json
import threading
import time
from espeak import espeak

#
# Type of camera you want to use: we keep the code here but we shall use the PiCamera
#
DLINK930 = 1 # D-Link camera model 930. URL = user:pass@ip:port/video.cgi
DLINK2312 = 2 # D-Link camera model 2312. URL = user:pass@ip/video1.mjpg 
BUILTINCAMERA = 3 # USB or built in camera on laptop
PICAMERA = 4 # Pi camera if running on Raspberry Pi

#
# if you have multiple cameras on your device then just use appropriate device
# if you have just one camera on your device then DEFAULT_CAM should work
DEFAULT_CAM = 0
REAR_CAM = 1
XTNL_CAM = 2
flywheelPin = 14 #broadcom pin to start flywheel
triggerPin = 15

#
# colors to use for bounding box and text
RED = 0, 0, 255
BLUE = 255, 0, 0
GREEN = 0, 255, 0
WHITE = 255,255,255
BLACK=10,10,10

# which camera do we use
camera_port = DEFAULT_CAM

#
# generic class that's called with a parameter and this then instantiates the
# correct type of implementation. The video recognition logic is in this class

class VideoCamera:
    
    def __init__(self, cameraType, arg1=DEFAULT_CAM, arg2=None):

        self.cameraType = cameraType
        
        # setup camera based on cameraType
        if( cameraType == BUILTINCAMERA):
            if( arg1 is not None ):
                print("BUILTINCAMERA OK")
                camera_port = arg1
                # no additional imports needed, OpenCV3 can deal with cameras
                self.camera = cv2.VideoCapture(camera_port)
                (self.grabbed, self.frame) = self.camera.read()
            else:
                print("If using built in camera, need to specify camera port")

        elif( cameraType == DLINK930):
            if( arg1 is not None and arg2 is not None):
                print("DLINK930 OK")
                cameraUrl = arg1
                authString = arg2
                streamurl = "http://" + ':'.join(authString) + '@' + cameraUrl + "/video.cgi"
                # no additional imports needed, OpenCV3 can deal with the URL
                self.camera= cv2.VideoCapture(streamurl)
                (self.grabbed, self.frame) = self.camera.read()
            else:
                print("If using IP Camera, need to specify camera IP and user:password")

        elif( cameraType == DLINK2312):
            if( arg1 is not None and arg2 is not None):
                print("DLINK2312 OK")
                cameraUrl = arg1
                authString = arg2
                streamurl = "http://" + ':'.join(authString) + '@' + cameraUrl + "/video1.mjpg"
                # no additional imports needed, OpenCV3 can deal with the URL
                self.camera= cv2.VideoCapture(streamurl)
                (self.grabbed, self.frame) = self.camera.read()
            else:
                print("If using IP Camera, need to specify camera IP and user:password")
            
        elif( cameraType == PICAMERA):
            if( arg1 is not None and arg2 is not None):
                # imports to handle picamera
                from picamera.array import PiRGBArray
                from picamera import PiCamera
                self.camera = PiCamera()
                self.camera.contrast = 50
                self.camera.resolution = arg1
                self.camera.framerate = arg2
                self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
                time.sleep(1)

            else:
                print("If using Pi Camera, need to specify resolution (x,y) and framerate")
        else:
            print("couldn't make sense of your arguments. Cannot proceed!")
            exit()
            
        # default color for bounding box
        self.color = RED

        #default coordinates for bounding box
        self.boxTopLeftX = 0
        self.boxTopLeftY = 0
        self.boxBotRightX = 0
        self.boxBotRightY = 0
        self.personName = "UNKNOWN"

        # default font for name
        self.font = cv2.FONT_HERSHEY_SIMPLEX

        self.carCascade = cv2.CascadeClassifier('car.xml')
        self.nearCars=[] # initialize else we get an error in self.readFaces
        self.farCars=[] # initialize else we get an error in self.readFaces
        self.foundCars = False
        
        # should thread run or stop
        self.stopped = False

    def start(self):
        # start thread to read frame
        threading.Thread(target=self.update, args=()).start()
        return self

    def update(self): # This will work only for Pi Camera
        # read camera
        for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):

            if self.stopped:
                return
            
            self.frame=frame.array
            self.rawCapture.truncate(0)
      
            # detect cars using grayscale (for speed?)
            #grayFrame = cv2.cvtColor(self.frame,cv2.COLOR_BGR2GRAY)
            tempCarList = self.carCascade.detectMultiScale(
                self.frame,
                scaleFactor = 1.1,
                minNeighbors = 5
                )
            self.nearCars = []
            self.farCars = []
            
            # draw bounding box and track only large objects
            for (x,y,w,h) in tempCarList:
                area = w*h

                if(area > 500 and area < 2000):
                    self.farCars.append((x,y,w,h))
                    self.drawRect(x, y, x+w, y+h, GREEN)
                    
                if(area >= 2000):
                    self.nearCars.append((x,y,w,h))
                    self.drawRect(x, y, x+w, y+h, RED)

            cv2.moveWindow('Cars',1,1)
            cv2.imshow('Cars', self.frame)        
            key = cv2.waitKey(1)
            if( 'q' == chr(key & 255) or 'Q' == chr(key & 255)):
                self.stopped = True
                
    def drawRect(self, x1, y1, x2, y2, color):
        cv2.rectangle(self.frame, (x1, y1), (x2, y2), color, 2)
        return

    
    def read(self):
        return self.frame

    def readNearCars(self):
        return self.nearCars

    def foundNearCarsInFrame(self):
        if( len(self.nearCars) > 0):
            return True
        else:
            return False

    def readFarCars(self):
        return self.farCars

    def foundFarCarsInFrame(self):
        if( len(self.farCars) > 0):
            return True
        else:
            return False
            
    def stop(self):
        self.stopped = True
        cv2.destroyAllWindows()
        if( self.cameraType == PICAMERA):
            self.rawCapture.truncate(0)
            self.camera.close
        del self.camera

    def isStopped(self):
        return self.stopped
    
    def setColor(self, color):
        self.color = color
        
    def setBoundingBox(self, x1,y1,x2,y2):
        self.boxTopLeftX = x1
        self.boxTopLeftY = y1
        self.boxBotRightX = x2
        self.boxBotRightY = y2


#
# Thread for voice prompts. Run in separate thread to avoid blocking main thread
# and also to prevent irritating repetition and chatter
class VoicePrompts:
    def __init__(self, threshold=2):

        timeThreshold = 2 # 2 seconds between prompts
        espeak.synth("Voice system initialized")
        #
        # We store the previous phrase to avoid repeating the same phrase
        # If new phrase is the same as previous phrase do nothing
        self.phrase = None
        self.oldPhrase = None
        
        self.stopped = False
        self.threshold=threshold
        time.sleep(threshold)
        
    def start(self):
        threading.Thread(target=self.speak, args=()).start()
        return self

    def speak(self):
        while True:

            if( self.stopped):
                return
            
            if( not self.phrase == None):
                if( not self.phrase == self.oldPhrase):
                    espeak.synth(self.phrase)
                    self.oldPhrase = self.phrase
                    self.phrase == None
                # sleep thread for duration to allow gap between voice prompts
                time.sleep(self.threshold)


    def setPhrase(self, phrase):
        self.phrase = phrase

    def stop(self):
        self.stopped = True

    
def IsBoundingBoxInFrame(frameSize, box):

    (x1,y1,x2, y2) = box
    height,width,_ = frameSize
    if( x1 > 50 and x2 < width-50 and
        y1 > 50 and  y1 < height-50):
        return True
    else:
        return False

x = 400
y = 300
frameArea = x*y
vs = VideoCamera(PICAMERA, (x,y), 15)
vs.start()
vp = VoicePrompts().start()

carsIdentified = False

try: 
    while True:

        if( vs.foundNearCarsInFrame() ):
            cars = vs.readNearCars()
                
            for car in cars:

                (x1,y1,w, h) = car
                centerX = x1+w/2
                centerY = y1+h/2

                if ( w*h > 3000):
                    vp.setPhrase("Watch out. Vehicle ahead!")
                else:
                    vp.setPhrase("")

                if( w*h > 4000 and abs(centerX-200)<50 and abs(centerY-150) < 50):
                    vp.setPhrase("Approaching vehicle")
                else:
                    vp.setPhrase("")
                    
        if( vs.isStopped() ):
            vs.stop()
            vp.stop()
                    
except (KeyboardInterrupt): # expect to be here when keyboard interrupt
    #vs.stop()
    vp.stop()
    
