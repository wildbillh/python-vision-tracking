import cv2, numpy as np
from typing import Tuple
from app.dependencies.utils import mergeWithDefault

class Classifier:

    def __init__(self, classifierFile: str, props: dict = {}):
    
        # Build the default properties for this classs
        default_props = {"minObjectSize": [18,18], "maxObjectSize": [128,128],
                        "scaleFactor": 1.09,"minNeighbors": 3}

        # Merge with whatever is sent in
        self.props = mergeWithDefault(props, default_props)
        
        # Set as member vars to avoid lots of dictionary lookups
        self.min_size = self.props["minObjectSize"]
        self.max_size = self.props["maxObjectSize"]
        self.scale_factor = self.props["scaleFactor"]
        self.min_neighbors = self.props["minNeighbors"]
        
        # Instanciate the cv2 classifier
        self.classifier = cv2.CascadeClassifier(filename=classifierFile)

    # -------------------------------------------------------------------------


    def process(self, frame: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
            Process the frame and return it
        """
        #frame = cv2.resize(src=frameTuple[0], dsize=[960, 540], interpolation=cv2.INTER_AREA)
        #gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  
        objects, weights, levels = self.classifier.detectMultiScale3(frame, 
            scaleFactor=self.scale_factor, minSize=self.min_size, 
            maxSize=self.max_size, minNeighbors=self.min_neighbors, outputRejectLevels=True)


        return (objects, levels)    
        print(weights, flush=True)
        cropped = None
        # if there are no detections, this will be false
        if isinstance(levels, np.ndarray):
            maxIndex = levels.argmax()



            if levels.shape[0] == 1:
                x, y, w, h = objects[maxIndex]
                cropped = cv2.resize(frame[y:y+h, x:x+w ], dsize=[300, 160])
            else:
                pass

            """
            print("------------------------------")
            for i in range(levels.size):
                #i = levels.argmax()
                x, y, w, h = objects[i]
                color = (255,0,0)
                color = (0,255,0)
                
                if i == maxIndex:
                    color = (0,255,0)
                elif levels[i] < 0.7:
                    color = (0,0,255)
                    
                print(objects[i], levels, maxIndex, flush=True)
                try:
                    if i == maxIndex:
                        cropped = cv2.resize(frame[y:y+h, x:x+w ], dsize=[300, 160])
                    else:
                        cropped = np.concatenate((cropped, cv2.resize(frame[y:y+h, x:x+w ], dsize=[300, 160])), axis=0)
                except Exception:
                    continue
                #frame = cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
            """


        return (cropped, frameTuple[1])

    # ------------------------------------------------------------------------
    
    def getProps (self) -> dict:
        """
            Return the dictionary of properties used in the classifier calls
        """
        return self.props