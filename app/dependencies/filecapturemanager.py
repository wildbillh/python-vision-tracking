import cv2, logging, time, numpy as np
from queue import Queue
from threading import Thread
from typing import Tuple, Union
from app.dependencies.capturemanager import CaptureManager

logger = logging.getLogger()

class FileCaptureManager (CaptureManager):

    def __init__(self, skipFrameSize: int = 150):
        super().__init__()
        self.skip_frame_size = skipFrameSize

    # ----------------------------------------------------------------
    
    
    def read(self) -> Tuple[bool, Union[np.ndarray, None], Union[dict, None]]:
        """
            Read the next frame and metadata
        """
        if not self.cap:
            raise Exception("Source not initialized")

        ret, frame = self.cap.read()

        if ret:
            self.frame_count += 1
            return (True, frame, self.get_frame_properties())
        else:
            return (False, None, None)
        
    # --------------------------------------------------------------

    def fast_forward(self, skipFrames = 0):
        """
            Fast forward the desired number of frames
        """
        skip_frames = skipFrames if skipFrames != 0 else self.skip_frame_size
        self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                     skip_frames + self.cap.get(cv2.CAP_PROP_POS_FRAMES))
    
    # -----------------------------------------------------------------
         
    def rewind(self, skipFrames = 0):
        """
            Go back the desired number of frames
        """
        
        skip_frames = skipFrames if skipFrames != 0 else self.skip_frame_size
        self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                     self.cap.get(cv2.CAP_PROP_POS_FRAMES) - skip_frames)   
        
class ThreadedFileCaptureManager (FileCaptureManager):

    def __init__(self, queue: Queue, skipFrameSize: int = 150):
        
        self.q = queue
        self.should_run = True
        self.daemon = None

        super().__init__(skipFrameSize)


    def __del__(self):
        self.stop()

    def read(self) -> Tuple[bool, Union[np.ndarray, None], Union[dict, None]]:
        """
            Read the next frame and metadata
        """
        if not self.cap:
            raise Exception("Source not initialized")
        
        self.daemon = Thread(target=self._runThreadedRead,  daemon=True)
        self.daemon.start()
            
    # -------------------------------------------------------------------
    
    def _runThreadedRead (self):
        """
            Continually read from the capture device and deposit to the queue
        """
        while self.should_run:
            if not self.q.full():
                success, frame, props = super().read()
                if success:
                    self.q.put((frame, props))
                else:
                    self.stop()
            else:
                time.sleep(0.003)

    # -------------------------------------------------------------------
    
    def stop (self):
        """
            Stop the thread and join it to main
        """
        
        self.should_run = False
        
        if self.daemon is not None:
            try:
                self.daemon.join()
            except: BaseException
            self.daemon = None

    # --------------------------------------------------------------------
    def isDone (self):
        """
            Publish the bool that determines stat
        """
        return not self.should_run