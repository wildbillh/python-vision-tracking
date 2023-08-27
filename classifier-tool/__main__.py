
import cv2, numpy as np, time, traceback
from app.dependencies.filecapturemanager import FileCaptureManager
from app.dependencies.videoshow import VideoShow
from app.dependencies.classifiertrackbar import ClassifierTrackBar
from app.dependencies.classifier import Classifier
from typing import Tuple, Union

class Main:
    """"""

    def __init__(self):
        self.classifier = Classifier('classifier-tool/cascade/cascade-24stage.xml')
        self.config_change = False

    def run(self):
        """"""
        cv2.startWindowThread()

        fcm = FileCaptureManager()
        fcm.open('classifier-tool/clips/fr-trans2.mp4')
        vs = VideoShow ({"windowName": "controls"})
        cv2.namedWindow("controls")
        
        track_bar = ClassifierTrackBar("controls", self.onChange)
        self.classifier.setProperties(track_bar.getValues())
        track_bar.load()
        
        should_run, frame, props = fcm.read()
        while should_run:

            process_frame = cv2.resize(src=frame, dsize=[960, 540])
            roi_tuple = self.getROIs(process_frame)
            print ("roi", roi_tuple, flush=True)
            process_frame = self.writeRectangles(process_frame, roi_tuple)
            should_run, keypress = vs.showSingleFrame({"frame": process_frame, "props": props}, 0)
            
            if should_run:
                if keypress == 'n':
                    should_run, frame, props = fcm.read()   
                elif keypress == 'r':
                    pass
        
        cv2.destroyAllWindows()

    # -------------------------------------------------------------------------

    def writeRectangles (self, frame: np.ndarray, rois: Union[Tuple[Tuple, Tuple], Tuple[np.ndarray, np.ndarray]]):
        """
            Writes the rectangles. Note: if no rois then ((),()) is sent, else (array, array)
        """  
        max_color = (0,255,0)
        color = (255,0,0)

        objects, levels = rois
        # if the classifier found any roi's and levels
        if isinstance(levels, np.ndarray):
            print(self.classifier.getProperties(), flush=True)
            # Get the index of the level with the highest value
            max_index = levels.argmax()
            object = None
            # For each roi, do something
            for i in range(levels.size):
                object = objects[i]   
    
                
                # Write the rectangle
                x, y, w, h = object
                frame = cv2.rectangle(frame, (x, y), (x + w, y + h), max_color if i == max_index else color, 3)

        # Return the processed frame and the given frame properties
        return frame      
    
    # ----------------------------------------------------------------------------

    def getROIs (self, frame):
        """"""
        process_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
        return self.classifier.process(frame)


    def onChange (self, val):
        """"""
        
        self.classifier.setProperties(val)

if __name__ == "__main__":
    try:
        main = Main()
        main.run()
        
    except BaseException as e:
        # print (e)
        traceback.print_exc()
