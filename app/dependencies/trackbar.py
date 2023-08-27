
import cv2
from typing import Callable, Union



class TrackBar:
    """ A class for creating trackbar"""

    def __init__ (self, windowName: str, config: dict, cb):
        """"""
        
        self.window_name = windowName
        self.config = config
        self.cb = cb 
        self.should_callback = False
        
    # ----------------------------------------------------------------

    def _cb_nothing(self, value):
        """Define a callback that does nothing"""
        pass    

    # -----------------------------------------------------------------
    
    def _cb (self, values):
        """"When called queries the trackbars to get the values"""

        if self.should_callback:
            for item in self.config.items():
                self.config[item[0]]["val"] = cv2.getTrackbarPos(item[0], self.window_name)   

            self.cb(self.config)
          
     # ---------------------------------------------------------------------------------                       
    
    def load (self):
        """Loads the trackbar in to the window defined in the constructor"""
        
        # By default the callbacks get called on creation. Disable this feature the boolean.
        self.should_callback = False

        # For each item in the config, create a new trackbar   
        for item in self.config.items():
            slider = str(item[0])

            if slider == "refresh":
                cv2.createTrackbar(slider, self.window_name, item[1]["val"], item[1]["max"], self._cb)
            else:
                cv2.createTrackbar(slider, self.window_name, item[1]["val"], item[1]["max"], self._cb)
    
    
        self.should_callback = True



