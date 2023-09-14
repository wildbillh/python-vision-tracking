# Note if using the MSMF backend, you must include the next 2 lines
# to avoid serious lags in camera initialization
import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

import cv2, sys
from app.dependencies.capturemanager import CaptureManager


class CameraCaptureManager (CaptureManager):
    """
        Adds camera specific featurs to the CaptureManager class
    """


    def __init__(self, openCVBackend = cv2.CAP_MSMF):
        """
            For Windows, only Direct Show and MSMF backends work out of the box
        """
        super().__init__()

        self.backend = openCVBackend
        # If the backend is MSMF, zoom set works but zoom get does not. 
        # Store the value of zoom and bypass the get method
        self.zoom = 100.0 if openCVBackend == cv2.CAP_MSMF else None

     # -------------------------------------------------------------- 

    def open(self, source: int, props: dict = {}):
        """
            Open the capture source. Raises an exception on failure
        """
    
        #self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        self.cap = cv2.VideoCapture(source, self.backend)
        
        if not self.cap.isOpened():
            raise Exception(f'Could not open Source from {source}')
        
        # Set any properties passed to the method
        self.setCameraProperties (props)
                
        # Store these properites since they don't normally change
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))

    # ----------------------------------------------------------------------

    def setCameraProperties (self, props: {}):
        """
            Sets the camera properties
        """
        if "fps" in props:
            self.cap.set(cv2.CAP_PROP_FPS, float(props["fps"]))
        if "height" in props:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(props["height"]))   
        if "width" in props:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(props["width"]))  
        if "zoom" in props:
            self.cap.set(cv2.CAP_PROP_ZOOM, float(props["zoom"]))
            self.zoom = props["zoom"] if self.zoom is not None else None  
        if "brightness" in props:
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, float(props["brightness"]))
        if "contrast" in props:
            self.cap.set(cv2.CAP_PROP_CONTRAST, float(props["contrast"]))
        if "saturation" in props: 
            self.cap.set(cv2.CAP_PROP_SATURATION, float(props["saturation"]))
        if "hue" in props: 
            self.cap.get(cv2.CAP_PROP_HUE, float(props["hue"]))

    
    # --------------------------------------------------------------

    def getFrameProperties(self) -> dict:
        """
            Get the capture device or file properties as a dictionary
        """
        return {
            "height": self.height,
            "width": self.width,
            "rate": self.fps,
            "time": int(self.cap.get(cv2.CAP_PROP_POS_MSEC)),
            "frame": self.frame_count
        }  
    
    # ----------------------------------------------------------------
    
    def getCameraProperties(self) -> dict: 
        """
            Return a dictionary of pertinent camera properties
        """
        fourcc = "N/A "
        if self.backend != cv2.CAP_MSMF:
            raw_fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            if raw_fourcc > 0:
                fourcc = raw_fourcc.to_bytes(4, byteorder=sys.byteorder).decode()
        
        return {
            "fourcc": fourcc,
            "brightness": self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": self.cap.get(cv2.CAP_PROP_CONTRAST),
            "saturation": self.cap.get(cv2.CAP_PROP_SATURATION),
            "hue": self.cap.get(cv2.CAP_PROP_HUE),
            "zoom": self.cap.get(cv2.CAP_PROP_ZOOM) if self.zoom is None else self.zoom 
        }