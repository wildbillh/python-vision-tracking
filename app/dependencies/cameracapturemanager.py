# Note if using the MSMF backend, you must include the next 2 lines
# to avoid serious lags in camera initialization
import time, os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

import cv2, numpy as np, logging, sys
from typing import Tuple, Union
from app.dependencies.capturemanager import CaptureManager

logger = logging.getLogger()

class CameraCaptureManager (CaptureManager):
    """
        Adds camera specific featurs to the CaptureManager class
    """

    MIN_ZOOM = 100
    MAX_ZOOM = 180

    def __init__(self, openCVBackend = cv2.CAP_DSHOW):
        """
            For Windows, only Direct Show and MSMF backends work out of the box
        """
        super().__init__()

        self.backend = openCVBackend
        # If the backend is MSMF, zoom set works but zoom get does not. 
        # Store the value of zoom and bypass the get method
        self.zoom = 100

        self.current_time = time.time()

     
    def read(self) -> Tuple[bool, Union[np.ndarray, None], Union[dict, None]]:
        """
        """

        parent_tuple = super().read()
        if self.zoom == 100.0:
            return parent_tuple
        
        return (parent_tuple[0], self.digitalZoom(parent_tuple[1], self.zoom), parent_tuple[2])
     
     
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

    
    # -----------------------------------------------------------------------
    
    def setZoom (self, val: int) -> float:
        """
            Sets the value of self.zoom in the class
            Since we are using a software zoom, this zoom is applied
            after the image is read. 
        """
        if val < CameraCaptureManager.MIN_ZOOM:
            val = CameraCaptureManager.MIN_ZOOM
        elif val > CameraCaptureManager.MAX_ZOOM:
            val = CameraCaptureManager.MAX_ZOOM

        self.zoom = val

    # ----------------------------------------------------------------------

    def setCameraProperties (self, props: {}):
        """
            Sets the camera properties.
            Oddly enough, the order these are called is crucial.
            When setting the zoom value after the program is running,
            use the setZoom() function instead.
        """ 
        
        
        if "zoom" in props:
            self.setZoom(float(props["zoom"])) 

        for description, prop_id in [
                ("height",          cv2.CAP_PROP_FRAME_HEIGHT), 
                ("width",           cv2.CAP_PROP_FRAME_WIDTH,), 
                ("fps",             cv2.CAP_PROP_FPS),
                ("autoExposure",    cv2.CAP_PROP_AUTO_EXPOSURE),
                ("brightness",      cv2.CAP_PROP_BRIGHTNESS),
                ("contrast",        cv2.CAP_PROP_CONTRAST),
                ("saturation",      cv2.CAP_PROP_SATURATION),
                ("hue",             cv2.CAP_PROP_HUE)
            ]:
                     #"zoom", "autoexposure", 
                     #"brightness", "contrast", "saturation", "hue"]:

            if description in props:
                self.setProperty(prop_id, props[description], description)
        
        # Always call this function last
        self.setProperty(propId=cv2.CAP_PROP_FOURCC, 
                         val=cv2.VideoWriter.fourcc('M','J','P','G'),
                         description="fourcc")
        
        
    
    # ------------------------------------------------------------------------

    def setProperty (self, propId:int, val:float, description:str):

        if not self.cap.set(propId=propId, value=float(val)):
            logger.error(f'Camera property "{description} was not set')

    # --------------------------------------------------------------

    def getFrameProperties(self) -> dict:
        """
            Get the capture device or file properties as a dictionary
        """
        return {
            "height": self.height,
            "width": self.width,
            "rate": self.fps,
            "time": int((time.time() - self.current_time) * 1000),
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
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
            "fourcc": fourcc,
            "brightness": self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": self.cap.get(cv2.CAP_PROP_CONTRAST),
            "saturation": self.cap.get(cv2.CAP_PROP_SATURATION),
            "hue": self.cap.get(cv2.CAP_PROP_HUE),
            "zoom": self.cap.get(cv2.CAP_PROP_ZOOM) if self.zoom is None else self.zoom,
            "autoExposure": self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        }
   
   
    # -----------------------------------------------------------------------------

    def digitalZoom(self, img:np.ndarray, magnification:float = 100.0):
        """
            Returns an image zoomed in based on the given magnification.
            100 = No zoom
        """
        if magnification == 100.0:
            return img
        
        zoom_factor = magnification / 100
        
        y_size = img.shape[0]
        x_size = img.shape[1]
    
        # define new boundaries
        x1 = int(0.5*x_size*(1-1/zoom_factor))
        x2 = int(x_size-0.5*x_size*(1-1/zoom_factor))
        y1 = int(0.5*y_size*(1-1/zoom_factor))
        y2 = int(y_size-0.5*y_size*(1-1/zoom_factor))

        # first crop image then scale
        img_cropped = img[y1:y2,x1:x2]
        return cv2.resize(img_cropped, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)