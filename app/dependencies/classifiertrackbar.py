
from typing import Union, Callable
from app.dependencies.trackbar import TrackBar

class ClassifierTrackBar (TrackBar):
    """
        Class for converting trackbar values to property values a classifier can use
    """

    def __init__(self, windowName: str, cb: Callable):
        """"""

        config = {
            "scale": {"val": 90, "max":400},
            "minNeigh": {"val": 3, "max":8},
            "minObjW": {"val": 18, "max": 36},
            "minObjH": {"val": 18, "max": 36},
            "maxObjW": {"val": 128, "max": 200},
            "maxObjH": {"val": 128, "max": 200},
            "refresh": {"val": 0, "max": 1}
        }

        # Store the user callback function
        self.user_cb = cb
        # Call the base class init
        super().__init__(windowName, config, self.cbHandler)
    
    
    # --------------------------------------------------------------------------
    def cbHandler (self, val):
        """
            This handler is called with the trackbar data. Return a classifier config
            based on it.
        """

        self.user_cb(self.getValues(val))
    
    # -------------------------------------------------------------------------
    
    def getValues (self, val=None):
        """
            Convert the current values of the trackbars to a Classifier config
        """

        config = self.config
        
        returnConfig = {
            "scaleFactor": 1 + config["scale"]["val"] / 1000.0,
            "minNeighbors": config["minNeigh"]["val"],
            "minObjectSize": [config["minObjW"]["val"], config["minObjH"]["val"]],           
            "maxObjectSize": [config["maxObjW"]["val"], config["maxObjH"]["val"]]
        }

        return returnConfig
    
    
