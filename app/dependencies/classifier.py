import cv2, numpy as np
from typing import Tuple
from app.dependencies.utils import mergeWithDefault

class Classifier:

    def __init__(self, classifierFile: str, props: dict = {}):
    
        self.setProperties(props=props)
        
        # Instanciate the cv2 classifier
        self.classifier = cv2.CascadeClassifier(filename=classifierFile)

    # -------------------------------------------------------------------------

    def setProperties (self, props: dict={}):


         # Build the default properties for this classs
        default_props = {"minObjectSize": [18,18], "maxObjectSize": [128,128],
                        "scaleFactor": 1.09, "minNeighbors": 3}

        # Merge with whatever is sent in
        self.props = mergeWithDefault(props, default_props)
        
        # Set as member vars to avoid lots of dictionary lookups
        self.min_size = self.props["minObjectSize"]
        self.max_size = self.props["maxObjectSize"]
        self.scale_factor = self.props["scaleFactor"]
        self.min_neighbors = self.props["minNeighbors"]

    # ------------------------------------------------------------------------
    
    def process(self, frame: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
            Process the frame and return it
        """
        objects, weights, levels = self.classifier.detectMultiScale3(frame, 
            scaleFactor=self.scale_factor, minSize=self.min_size, 
            maxSize=self.max_size, minNeighbors=self.min_neighbors, outputRejectLevels=True)
        
        return (objects, levels)    
        
    # ------------------------------------------------------------------------
    
    def getProperties (self) -> dict:
        """
            Return the dictionary of properties used in the classifier calls
        """
        return self.props