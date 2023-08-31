import cv2, logging, numpy as np
from app.dependencies.filecapturemanager import FileCaptureManager
from app.dependencies.videoshow import SelectionVideoShow
from app.dependencies.utils import removeROIs


logger = logging.getLogger()

class ExtractNegatives:
    """
        Class for extracting negative frames from a video file
    """

    def __init__(self, videoSource: str, targetPrefix: str, targetFolder: str):
        """
        """
        self.video_source = videoSource
        self.target_prefix = targetPrefix
        self.target_folder = targetFolder
        

    # --------------------------------------------------------------------------------------------
    
    def run(self, processSize: list = [960, 540], finishedSize: list = [960,540], frameCount: int = 5):
        """
        """  
        should_scale_final_image = np.allclose(processSize,finishedSize)
        logger.info(should_scale_final_image)
        cv2.startWindowThread()

        # Get the source
        fcm = FileCaptureManager()
        fcm.open(self.video_source)

        # Get the display 
        props = {"windowName": "extract-negatives"}
        vs = SelectionVideoShow (props=props, interimProcessFunc=removeROIs)

        should_run, frame, frame_props = fcm.read()
        
        while should_run and not vs.shouldQuit():
            
            # for each frame display the image with the classifier rectangles.
            # if 'r' is pressed reclassify the current image

            if (frame_props["frame"] % frameCount) == 0:

                resized_frame = cv2.resize(src=frame, dsize=processSize)
                processed_frame, selections = vs.show(resized_frame)
            
                if selections:
                    # capture the modified frame
                    filename = f'{self.target_folder}/{self.target_prefix}-{frame_props["frame"]}.jpg'
                    print(f'Writing frame: {filename}')
                
                    print(processed_frame.shape, selections, flush=True)
                    if should_scale_final_image:
                        cv2.resize(processed_frame, finishedSize)

                    print(cv2.imwrite(filename, processed_frame), flush=True) 
            
            should_run, frame, frame_props = fcm.read()
            
        
        cv2.destroyWindow(props["windowName"])