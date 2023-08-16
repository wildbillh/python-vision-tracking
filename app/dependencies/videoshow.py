import cv2
import time
from threading import Thread
from queue import Queue
from typing import Dict, Tuple, Union
from app.dependencies import constants
from app.dependencies.utils import mergeWithDefault


class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """
    QUIT = 'q'
    WRITE_FILE = 'f'
    REWIND = 'l'
    FAST_FOWARD = 'l'


    def __init__(self, props={}):
        

        default_props = {"throttleOutput": True, "clipCaptureDir": "clips/capture", "showTime": False, "windowName": "Object Detection", "show": True}
        # Merge with whatever is sent in
        self.props = mergeWithDefault(props, default_props)

        self.window_name = props["windowName"]
        self.capture_dir = props["clipCaptureDir"]
        self.show_time = props["showTime"]
        self.throttle_output = props["throttleOutput"]
        self.show_output = props["showOutput"]

    
        self.delay_ms = 0
        self.process_delay = 5
        self.last_load = time.time() 
        

    # -----------------------------------------------------------------

    def __del__(self):
        self.destroy()

    #--------------------------------------------------------------------
    
    def get_props (self):
        """
            Return the dictionary of properties
        """
        return self.props()

    # --------------------------------------------------------------

    def setFPS (self, fps: int) -> None:
        """
            Set the fps of the output by adding sleeps just prior to imshow
        """
        if fps == 0:
            self.throttle_output = False
        else:
            self.delay_ms = 1000.0 / fps

    # -------------------------------------------------------------

    def showSingleFrame (self, frame, frameProps: dict = {}, waitTimeMs: int = 1000) -> None:
        
        if self.show_time:
            text = f'{(frameProps["time"] / 1000):.3f} : {frameProps["frame"]}'
            text = text.rjust(15)

            frame = cv2.putText(img=frame, text=text, org=(00, int(frameProps["height"] - 50)),
                                    fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=2.0,
                                    color=self.properties[constants.TIME_COLOR],
                                    thickness=self.properties[constants.TIME_THICKNESS]) 
        # Show the frame
        cv2.imshow(self.window_name, frame)
        cv2.waitKey(waitTimeMs)  


    # -------------------------------------------------------------------------------------
    
    def show(self, frame, frameProps: dict = {}) -> Tuple[bool, Union[str, None]]:
        """
            Show the given frame in the named window. Check the keypresses for
            special operations
        """

        if not self.show_output:
            return (True, None)
            
        if self.show_time:
            text = f'{(frameProps["time"] / 1000):.3f} : {frameProps["frame"]}'
            text = text.rjust(15)

            frame = cv2.putText(img=frame, text=text, org=(00, int(frameProps["height"] - 50)),
                                    fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=2.0,
                                    color=self.properties[constants.TIME_COLOR],
                                    thickness=self.properties[constants.TIME_THICKNESS])
            
        # If an fps is given we may need to sleep before the showing the frame.
        if self.throttle_output and self.delay_ms > 0:
            interval_ms = (time.time() - self.last_load) / 1000
            if interval_ms < (self.delay_ms - self.process_delay):
                time.sleep((self.delay_ms - self.process_delay - interval_ms) / 1000)
        
        # Show the frame   
        cv2.imshow(self.window_name, frame)
        
        # Either add or subtract to get a new process delay, based on the found interval
        now = time.time()
        if (now - self.last_load) * 1000 > self.delay_ms:
            self.process_delay += 1
        else:
            self.process_delay -= 1
        self.last_load = now    
        
        # Check for a keypress
        keypress = cv2.pollKey()
        
        # if no keypress return
        if keypress == -1:
            return (True, None)
            
        keypress = keypress & 0xFF

        # Quit indicated. Set the stop boolean
        if keypress == ord(VideoShow.QUIT):
            return (False, None)

        # Write the current frame as a jpg
        elif keypress == ord(VideoShow.WRITE_FILE):
            # Generate a file with the current time
            filename = f'{self.captureDir}/{int(time.time() * 1000)}.jpg'
            if cv2.imwrite(filename, frame):
                print(f'Captured frame to: {filename}', flush=True)
            else:
                print(f'Write of file: {filename} failed')

            return (True, None)

        # Return the value of the key pressed of rewind or ff
        elif keypress == ord(VideoShow.REWIND) or keypress == VideoShow.FAST_FOWARD:
            return (True, chr(keypress))


    # ------------------------------------------------------------------------------------

    def destroy (self):
        cv2.destroyWindow(self.window_name) 


# =============================================================================================


class ThreadedVideoShow (VideoShow):
    """
        Threaded version that reads from a queue
    """

    def __init__(self, queue: Queue, props):
        """
            Calls the super constructor and sets from instance vars
        """
        # Call the base class constructor
        super().__init__(props)

        self.should_run = True
        self.q = queue
    
        self.daemon = None
        self.empty_queue_seconds = 0.002



# -----------------------------------------------------------------------------------

    def show (self, emptyQueueSleepMs: int = 2):
        """
            Setup a thread to read from a queue and show with imshow
        """
        
        self.empty_queue_seconds = emptyQueueSleepMs / 1000.0
        self.daemon = Thread(target=self._runThreadedShow,  daemon=True)
        self.daemon.start()

    
    # --------------------------------------------------------------------------------

    
    def _runThreadedShow (self):
        """
            This method runs as a thread. It continually gets frame from the queue
            and calls imshow on them. If the imshow window errors or returns 
            a user quit code, calls stop()
        """
        
        frame = None
        total_sleep_time = 0.0
        
        while self.should_run:
            try:
                frame, props = self.q.get()
                
                if self.show_output:
                    success, action = super().show(frame)
                    if not success:   
                        #self.should_run = False
                        self.stop()

            except Exception:
                time.sleep(self.empty_queue_seconds)
        

    # ------------------------------------------------------------------------------------

    def stop (self):
        """
            Stop the thread by setting the should_run bool to False
        """
        self.should_run = False
        if self.daemon != None:
            try:
                self.daemon.join()
            except Exception:
                pass
            self.daemon = None

    # -----------------------------------------------------------------------------------

    def isDone (self) -> bool:
        """
            Returns true if the thread is not running
        """ 
        return not self.should_run
    
    
    # --------------------------------------------------------------------------------

    def waitForQueuedObjects (self, fps):
        """
            Called when the source of frames is depleted and we want to finish off any
            frames left in the queue
        """
        print("waiting for remaining queue objects to show")
        # Continure processing until the queue is empty or maxIterations reached
        maxIterations = self.q.maxsize
        count = 0
        sleepSeconds = 1.0 / fps
        while self.should_run and count < maxIterations and not self.q.empty():
            time.sleep(sleepSeconds)
            count += 1        