import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2
from app.dependencies.cameracapturemanager import CameraCaptureManager
from app.dependencies.videoshow import VideoShow

# Instanciate the the camera capture class with the proper OpenCV backend
cm = CameraCaptureManager(openCVBackend = cv2.CAP_MSMF)

# Set the initial camera properties 
props = {"height": 720, "width": 1280, "fps": 60, "zoom": 110}

# Open the camera 
cm.open(1, props)
print(cm.getCameraProperties(), flush=True)

# Get the class for display
vs = VideoShow()



should_run = True
while should_run:

    success, frame, props = cm.read ()
    if success:
        should_run, keypress = vs.show({"frame": frame, "props": props})
        if props["frame"] % 45 == 0:
            cm.setCameraProperties({"zoom": 200.0})
            print(cm.getCameraProperties(), flush=True)
        elif props["frame"] % 65 == 0:
            cm.setCameraProperties({"zoom": 100.0})
            print(cm.getCameraProperties(), flush=True)
        #print (cm.getFrameProperties(), flush=True)
       


