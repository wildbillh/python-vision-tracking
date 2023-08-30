
import cv2, numpy as np, time, traceback
from app.dependencies.filecapturemanager import FileCaptureManager
from app.dependencies.videoshow import VideoShow, SelectionVideoShow
from app.dependencies.classifiertrackbar import ClassifierTrackBar
from app.dependencies.classifier import Classifier
from app.dependencies.utils import removeROIs
from typing import Tuple, Union

class Main:
    """
        A tool for viewing a clip frame by frame and applying different classification 
        properties to the each image
    """

    def __init__(self):
        
        self.target_clip_folder = "extract-negatives/negatives"

    # --------------------------------------------------------------------------
    
    def run(self):
        """"""
        cv2.startWindowThread()

        # Get the source
        fcm = FileCaptureManager()
        fcm.open('clips/kb/fr-trans2.mp4')

        # Get the display 
        props = {"windowName": "extract-negatives"}
        vs = SelectionVideoShow (props=props, interimProcessFunc=removeROIs)
        
           
        
        should_run, frame, frame_props = fcm.read()
        
        while should_run and not vs.shouldQuit():
            
            # for each frame display the image with the classifier rectangles.
            # if 'r' is pressed reclassify the current image

            resized_frame = cv2.resize(src=frame, dsize=[960, 540])
            processed_frame, selections = vs.show(resized_frame)
            
            if selections:
                # capture the modified frame
                filename = f'{self.target_clip_folder}/fr_trans2-{frame_props["frame"]}.jpg'
                print(f'Writing frame: {filename}')
                
                print(processed_frame.shape, selections, flush=True)
                cv2.imwrite(filename, processed_frame) 
            
            should_run, frame, frame_props = fcm.read()
            
        
        cv2.destroyWindow(props["windowName"])

      
    
    

# ==================================================================================

if __name__ == "__main__":
    try:
        main = Main()
        main.run()
        
    except BaseException as e:
        # print (e)
        traceback.print_exc()
