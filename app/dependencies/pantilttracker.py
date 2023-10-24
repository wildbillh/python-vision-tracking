
import logging, math
from typing import Union, Tuple
from app.dependencies.pantilt import PanTilt
from app.dependencies.usbservocontroller import USBServoController

logger = logging.getLogger()

class PanTiltTracker (PanTilt):
    """
        Class that adds tracking of objects using the PanTilt class
    """

    DEFAULT_HORIZ_SLACK = 0.03
    DEFAULT_VERT_SLACK = 0.05
    DEFAULT_CENTER_OFFSET = (0.0, 0.2)
    DEFAULT_FRAME_DIMS = (1280, 720)

    DEFAULT_TRACKER_PROPS = {
            "horizSlack": DEFAULT_HORIZ_SLACK,
            "vertSlack": DEFAULT_VERT_SLACK,
            "centerOffset": DEFAULT_CENTER_OFFSET,
            "frameDims": DEFAULT_FRAME_DIMS}

    DEGREES_PER_RADIAN = 180 / math.pi

    # --------------------------------------------------------------------
    
    def __init__(self, pan: int = 4, tilt: int = 5, trackerProps = {}):
        """
        """

        super().__init__(pan=pan, tilt=tilt)
        
        self.tracker_props = PanTiltTracker.DEFAULT_TRACKER_PROPS.copy()
        self.setTrackerProperties(trackerProps)

    # --------------------------------------------------------------------
    
    def setTrackerProperties (self, trackerProps: dict = {}):
        """
        """

        for key, val in trackerProps.items():
            if key in self.tracker_props:
                self.tracker_props[key] = val
            else:
                logger.warning(f'Attempt to set unknown property {key} in {self.__class__.__name__}.setTrackerProperties()')

        # Calculate and store the frame center based on the frame dimensions and center offset
        frame_dims = self.tracker_props["frameDims"]

        self.frame_center = (
            frame_dims[0] // 2 + int(self.tracker_props["centerOffset"][0] * frame_dims[0] // 2),
            frame_dims[1] // 2 + int(self.tracker_props["centerOffset"][1] * frame_dims[1] // 2)
        )
  
        # Calculate and store the horizontal and vertical slack tuples
        self.horiz_slack = (
            self.frame_center[0] - int(self.frame_center[0] * self.tracker_props["horizSlack"]),
            self.frame_center[0] + int(self.frame_center[0] * self.tracker_props["horizSlack"])
        )

        self.vert_slack = (
            self.frame_center[1] - int(self.frame_center[1] * self.tracker_props["vertSlack"]),
            self.frame_center[1] + int(self.frame_center[1] * self.tracker_props["vertSlack"])
        )

    # -------------------------------------------------------------------------
    
    def calculateCorrectionDegrees (self, regionCenter: Tuple[int, int]) -> Tuple[Union[float, None], Union[float, None]]: 
        """
            If the ROI center is not within the slacked center region, calculate the angles of corrections
        """
        
        # Get the x and y cordinates of the center of the ROI
        x, y = regionCenter      
        hor_correction = None
        vert_correction = None

        # If the x or y coordinate is not within the slack region, calculate the angle of correction.
        # This is done to prevent jitter in the servos

        if x < self.horiz_slack[0] or x > self.horiz_slack[1]:
            hor_correction = math.atan((x - self.frame_center[0]) / self.tracker_props["frameDims"][1]) * PanTiltTracker.DEGREES_PER_RADIAN
        
        if y < self.vert_slack[0] or y > self.vert_slack[1]:
            vert_correction = math.atan((self.frame_center[1] - y) / self.tracker_props["frameDims"][0]) * PanTiltTracker.DEGREES_PER_RADIAN
    
        return (hor_correction, vert_correction)
    
    # --------------------------------------------------------------------------------------------
    
    def correct (self, regionCenter: Tuple[int, int], fps:int = 30) -> Tuple[float, int]:
        """
            Given the needed correction degrees for each servo, send the new positions to 
            the servos and return the estimated time and frames needed to complete the move.
        """
        
        # Calculate the degrees of correction needed by both servos
        correction_tuple = self.calculateCorrectionDegrees(regionCenter=regionCenter)
     
        if all(x is None for x in correction_tuple):
            return (0.0, 0)
        
        # Send the new positions
        self.setRelativePos(panPos=correction_tuple[0], tiltPos=correction_tuple[1], units=2)
        
        print("correct", correction_tuple[0], correction_tuple[1], flush=True)
                   
        # Calculate the time needed to perform the correction
        return self.calculateMovementTime(panDegrees=correction_tuple[0], tiltDegrees=correction_tuple[1], fps=fps)
         

    # --------------------------------------------------------------------------------------------
    
    def getFrameCenter (self) -> Tuple[int, int]: 
        """
        """

        return self.frame_center