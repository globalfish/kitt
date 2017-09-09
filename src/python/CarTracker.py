

#
# demo to get webcam images from a Mac (possibly a PC?) and into AWS Rekognition
# Ideally, this will get triggered by an external event, e.g. a sensor that detects
# motion, a doorbell
#
# Author: vswamina, April 2017.
# 2017_08_06 Updated with multiple changes for sharing

# With a lot of help from the Internet
import cv2
import boto3
import json
import gallery
import threading

#
# if you have multiple cameras on your device then just use appropriate device
# if you have just one camera on your device then DEFAULT_CAM should work
DEFAULT_CAM = 0
REAR_CAM = 1
XTNL_CAM = 2

#
# colors to use for bounding box and text
RED = 0, 0, 255
BLUE = 255, 0, 0
GREEN = 0, 255, 0
WHITE = 255,255,255

# which camera do we use
camera_port = DEFAULT_CAM

# setup AWS Rekognition client
client = boto3.client('rekognition')

#
# load images from S3 bucket and create a gallery of known faces
#
s3client = boto3.client("s3")
gallery.createGallery(client, s3client, "com.vswamina.aws.test.images")

#
# In order to avoid buffering, we read the camera images
# in a separate thread and then get images as needed

class VideoStreamFromCamera:
    def __init__(self, src=camera_port):

        # setup camera to capture
        self.camera = cv2.VideoCapture(camera_port)
        (self.grabbed, self.frame) = self.camera.read()
        self.color = RED
        self.boxTopLeftX = 0
        self.boxTopLeftY = 0
        self.boxBotRightX = 0
        self.boxBotRightY = 0
        self.personName = "UNKNOWN"
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.faceCascade = cv2.CascadeClassifier('car.xml')
        self.faces=[] # initialize else we get an error in self.readFaces
        
        # should thread run or stop
        self.stopped = False

    def start(self):
        # start thread to read frame
        threading.Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # read camera
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.camera.read()
            self.drawRect(self.boxTopLeftX, self.boxTopLeftY,
                          self.boxBotRightX, self.boxBotRightY,
                          self.color)
      
            # detect faces
            self.faces = self.faceCascade.detectMultiScale(
                self.frame,
                scaleFactor = 1.2,
                minNeighbors = 3
                )
            # draw bounding box
            for (x,y,w,h) in self.faces:
                self.drawRect(x, y, x+w, y+h, self.color)
                cv2.putText(self.frame, self.personName, (x, y-10), self.font, 0.5, self.color, 2)
                
            cv2.imshow('Rekognition', self.frame)        
            cv2.waitKey(1)

    def drawRect(self, x1, y1, x2, y2, color):
        cv2.rectangle(self.frame, (x1, y1), (x2, y2), color, 2)
        return

    
    def read(self):
        return self.frame

    def readFaces(self):
        return self.faces
        
    def stop(self):
        self.stopped = True
        cv2.destroyAllWindows()
        del self.camera

    def setColor(self, color):
        self.color = color
        
    def setBoundingBox(self, x1,y1,x2,y2):
        self.boxTopLeftX = x1
        self.boxTopLeftY = y1
        self.boxBotRightX = x2
        self.boxBotRightY = y2

    def setName(self, name):
        self.personName = name
        
def IsBoundingBoxInFrame(frameSize, box):

    (x1,y1,x2, y2) = box
    height,width,_ = frameSize
    if( x1 > 50 and x2 < width-50 and
        y1 > 50 and  y1 < height-50):
        return True
    else:
        return False
    
vs = VideoStreamFromCamera().start()

faceIdentified = False

try: 
    while True:
        
        # say cheese
        camera_capture = vs.read()
        frameDims = camera_capture.shape

        vs.setColor(GREEN)
                
except (KeyboardInterrupt): # expect to be here when keyboard interrupt
    vs.stop()
    
