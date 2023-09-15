import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2, numpy as np, sys
from queue import Queue
from threading import Thread
from typing import Tuple, Union
from app.dependencies import constants

class CaptureManager():

    def __init__(self):
        
        self.cap = None
        self.fps = 0
        self.width = 0
        self.height = 0
        self.frame_count = 0
        
    # --------------------------------------------------------------


    def __del__(self):
        """
        """
        if self.cap is not None:
            self.cap.release()

    # --------------------------------------------------------------
    
    def getOpenCVCapture(self) -> cv2.VideoCapture:
        """
            Return the underlying class
        """
        return self.cap
    
    
    # -------------------------------------------------------------- 

    def open(self, source: Union[str, int], props={}):
        """
            Open the capture source. Raises an exception on failure
        """
        
        if isinstance(source, int):
            self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            raise Exception(f'Could not open Source from {source}')
        
        if "fps" in props:
            self.cap.set(cv2.CAP_PROP_FPS, float(props["fps"]))
        
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
   
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
            "frame": int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        }  

    # --------------------------------------------------------------
    
    def read(self) -> Tuple[bool, Union[np.ndarray, None], Union[dict, None]]:
        """
            Read the next frame and metadata
            Returns a tuple as:
            (success: bool, frame: np.ndarray, frameProps: dict) 
        """
        if not self.cap:
            raise Exception("Source not initialized")

        ret, frame = self.cap.read()

        if ret:
            self.frame_count += 1
            return (True, frame, self.getFrameProperties())
            
        else:
            return (False, None, None)
        
    # ----------------------------------------------------------
    
    def stats(self):
        return self.frame_count
    
    # ----------------------------------------------------------

    def destroy(self):
        """
            Release the resources
        """
        if self.cap is not None:
            self.cap.release()
        self.cap = None            

