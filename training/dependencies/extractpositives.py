import cv2, logging, numpy as np, os
from app.dependencies.filecapturemanager import FileCaptureManager
from app.dependencies.videoshow import SelectionVideoShow
from app.dependencies.utils import removeROIs
from typing import Tuple


logger = logging.getLogger()

class ExtractPositives:
    """
        Class for extracting negative frames from a video file
    """

    def __init__(self, videoSource: str, targetClipPrefix: str, 
                 targetClipFolder: str, targetFile: str):
        """
        """
        self.video_source = videoSource
        self.target_prefix = targetClipPrefix
        self.target_folder = targetClipFolder
        self.target_file = targetFile
        self.scale_factor = 1.0

     # --------------------------------------------------------------------------------------------
    
    def run(self, processSize: list = [960, 540], finishedSize: list = [960,540], frameCount: int = 5):
        """
        """  
        
        # Open the target File
        flags = 'a'
        if os.path.isfile(self.target_file):
            logger.info(f'File: {self.target_file} exists. Appending...')

        pos_file = open(self.target_file, flags)

        
        should_scale_final_image = not np.allclose(processSize,finishedSize)
        self.scale_factor = finishedSize[0] / float (processSize[0])
    
        cv2.startWindowThread()

        # Get the source
        fcm = FileCaptureManager()
        fcm.open(self.video_source)

        # Get the display 
        props = {"windowName": "extract-negatives"}
        vs = SelectionVideoShow (props=props)

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
                    
                
                    
                    if should_scale_final_image:
                        processed_frame = cv2.resize(processed_frame, finishedSize)  
                        selections = self.scaleSelections(selections)
                    
                    if not cv2.imwrite(filename, processed_frame):
                        raise Exception (f'Could not write file: {filename}')
                    
                    pos_file.write (self.generateEntry(filename, selections)) 
                    
            
            should_run, frame, frame_props = fcm.read()
            
        
        pos_file.close()
        cv2.destroyWindow(props["windowName"])

    
    # -----------------------------------------------------------------------
    
    def generateEntry (self, filename, selections):
        """
        """
        str = f'{filename} {len(selections)}'
        for selection in selections:
            str += f' {selection[0]} {selection[1]} {selection[2] - selection[0]} {selection[3] - selection[1]}'
        str += '\n'

        return str


    # ------------------------------------------------------------------
    
    def scaleSelections (self, selections: list[Tuple]) -> list[Tuple]:
        """
        """
        scaled_selection = []
        for selection in selections:
            
            scaled_selection.append ((int(selection[0] * self.scale_factor),
                         int(selection[1] * self.scale_factor),
                         int(selection[2] * self.scale_factor),
                         int(selection[3] * self.scale_factor)))
        
        return scaled_selection