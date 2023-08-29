import cv2, logging, time
from threading import Thread
from queue import Queue
from typing import Tuple, Union
from app.dependencies import constants
from app.dependencies.utils import mergeWithDefault

logger = logging.getLogger()

class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """
    QUIT = 'q'
    WRITE_FILE = 'f'
    REWIND = 'l'
    FAST_FOWARD = 'l'
    PAUSE = 'p'
    ESCAPE = 27


    def __init__(self, props={}):
        
        default_props = {"clipCaptureDir": "clips/capture", "showTime": False, 
                         "windowName": "Object Detection", "showOutput": True,
                         "timeColor": (10,255,10), "timeThickness": 2}
        
        # Merge with whatever is sent in
        self.props = mergeWithDefault(props, default_props)

        self.window_name = self.props["windowName"]
        self.capture_dir = self.props["clipCaptureDir"]
        self.show_time = self.props["showTime"]
        self.show_output = self.props["showOutput"]
        
        self.fps = 0
        self.delay_ms = 1000.0 / self.fps if self.fps > 0 else 0
        self.process_delay = 3


        # Stats
        self.first_load_time = 0
        self.last_load_time = 0
        self.frame_count = 0
        
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

    def setFrameRate (self, fps: int) -> None:
        """
            Set the fps of the output by adding sleeps just prior to imshow
        """
        self.fps = fps
        self.delay_ms = 1000.0 / fps if fps > 0 else 0

    # -------------------------------------------------------------

    def showSingleFrame (self, processedDict: dict, waitTimeMs: int = 1000) -> None:
        
        if self.show_time:
            self.showTimeInWindow(processedDict["frame"], processedDict["props"]) 

        # Show the frame
        cv2.imshow(self.window_name, processedDict["frame"])
        keypress = cv2.waitKey(waitTimeMs)  
        if keypress == ord(VideoShow.QUIT):
            return (False, None)
        return (True, chr(keypress))

    # ---------------------------------------------------------------------------------

    def showTimeInWindow (self, frame, frameProps):

        if frameProps:    
            text = f'{(frameProps["time"] / 1000):.3f} : {frameProps["frame"]}'
            text = text.rjust(15)
            frame = cv2.putText(img=frame, text=text, org=(0, 30),
                                    fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=2.0,
                                    color=self.props[constants.TIME_COLOR],
                                    thickness=self.props[constants.TIME_THICKNESS],
                                    bottomLeftOrigin=False)  
        return frame

    # -------------------------------------------------------------------------------------
    
    def show(self, processedDict: dict) -> Tuple[bool, Union[str, None]]:
        """
            Show the given frame in the named window. Check the keypresses for
            special operations
        """

        # Don't do anything if show_output is False
        if not self.show_output:
            return (True, None)
        
       
        # Write the time and frame on the window is show_time is set
        if self.show_time and processedDict["props"]:
            frame = self.showTimeInWindow(processedDict["frame"], processedDict["props"])
            
            
        # If this is the first loop set the load times
        if self.first_load_time == 0:
            self.first_load_time = self.last_load_time = time.time()
            
       
        # If an fps is given we may need to sleep before the showing the frame.
        if self.delay_ms > 0:
            interval_ms = (time.time() - self.last_load_time) / 1000
            if interval_ms < (self.delay_ms - self.process_delay):
                time.sleep((self.delay_ms - self.process_delay - interval_ms) / 1000)
        

        # Show the frame   
        cv2.imshow(self.window_name, processedDict["frame"])
        self.frame_count += 1
        

        # Calculate the delay in ms since the last load
        now = time.time()
        delay = (now - self.last_load_time) * 1000
        
        # If the delay was greater, add to the process_delay
        if delay > self.delay_ms:
            self.process_delay += 1
        else:
            self.process_delay -= 1

        # Set the new value for last_load_time    
        self.last_load_time = now    
        
        # Check for a keypress
        keypress = cv2.pollKey()
        
        # if no keypress return
        if keypress == -1:
            return (True, None)
            
        keypress = keypress & 0xFF

        # Quit indicated. Set the stop boolean
        if keypress == ord(VideoShow.QUIT):
            return (False, None)
        
        elif keypress == ord(VideoShow.PAUSE):
            while True:
                if cv2.waitKey(0) & 0xFF == ord(VideoShow.PAUSE):
                    break

        # Write the current frame as a jpg
        elif keypress == ord(VideoShow.WRITE_FILE):
            # Generate a file with the current time
            filename = f'{self.captureDir}/{int(time.time() * 1000)}.jpg'
            if cv2.imwrite(filename, frame):
                logger.info(f'Captured frame to: {filename}')
            else:
                logger.info(f'Write of file: {filename} failed')

            return (True, None)

        # Return the value of the key pressed of rewind or ff
        elif keypress == ord(VideoShow.REWIND) or keypress == VideoShow.FAST_FOWARD:
            return (True, chr(keypress))

    # --------------------------------------------------------------------------------------------

    def stats (self):
        return (self.frame_count, self.frame_count / (self.last_load_time - self.first_load_time) if self.last_load_time > 0 else (0,0))


    # ------------------------------------------------------------------------------------

    def destroy (self):
        try:
            cv2.destroyWindow(self.window_name)
        except Exception:
            pass
        


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
        self.empty_queue_seconds = 0.001
        self.stop_on_empty_queue = False



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
                processedDict = self.q.get()
                #print(processedDict, flush=True)
                           
                if self.show_output:
                    success, action = super().show(processedDict)

                    if not success:   
                        self.stop()

            except Exception:
                time.sleep(self.empty_queue_seconds)

            if self.stop_on_empty_queue and self.q.empty():
                self.should_run = False

        logger.debug("End of vs loop")
        self.stop()
        

    # ------------------------------------------------------------------------------------

    def stop (self):
        """
            Stop the thread by setting the should_run bool to False
        """
        
        self.should_run = False
        if self.daemon != None:
            logger.debug('vs.stop() called')
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
    
    # -------------------------------------------------------------------------------

    def shouldStopOnEmptyQueue (self):
        logger.debug("Stop on empty called")
        self.stop_on_empty_queue = True

# =======================================================================================

class SelectionVideoShow (VideoShow):
    """
        Class for selecting one or more rectangles of an image
    """
        
    def __init__ (self, props: dict = {}):

        super().__init__(props)
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.getSelection)

        self.image_history = []
        self.mouse_points = None
        self.current_idx = 0
        self.should_run = True

    # -----------------------------------------------------------------------------------

    def getSelection (self, event, x, y, flags, param):
        """
            Mouse Event handler. Draws interim and final rectangles
        """

        # Get the current image out of the history list
        image = self.image_history[self.current_idx][0]
    
        # Store the starting point of the rectangle
        if event == cv2.EVENT_LBUTTONDOWN:
            self.mouse_points = [(x, y)]
        
        # Store the new rectangle and write it to the window
        elif event == cv2.EVENT_LBUTTONUP:
            
            # Append the final point to the rect
            self.mouse_points.append((x, y))
            
            # Make a copy of the image, draw the new rect and store the image and rectangle coords
            new_image = image.copy()
            cv2.rectangle(new_image, self.mouse_points[0], self.mouse_points[1], (0, 255, 0), 2)
            self.image_history.append((new_image, (self.mouse_points[0],self.mouse_points[1])))
            self.current_idx += 1
            cv2.imshow(self.window_name, new_image)

        # draw the interim rectangle
        elif event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON:
            clone = image.copy()
            cv2.rectangle(clone, self.mouse_points[0], (x, y), (0, 255, 0), 2)
            cv2.imshow(self.window_name, clone)

    # -----------------------------------------------------------------------------------------
    
    def show (self, _image):
        """
            Override the show() method of the base class
        """
        
        # Store the given image into our history list
        self.image_history.append((_image, None))

        while self.should_run:
        
            # Show the image
            image = self.image_history[self.current_idx][0]
            cv2.imshow(self.window_name, image)

            keypress = cv2.waitKey(0)
            # if escape key is hit, delete the latest historical image and coords
            if keypress == VideoShow.ESCAPE:
                if len(self.image_history) > 1:                
                    self.image_history.pop(len(self.image_history) -1) 
                    self.current_idx -= 1
            else:
                self.should_run = False

        # We're exiting, so get the list of rectangles and close the windows
        rects = []
        for i in range(1, len(self.image_history)):
            rects.append(self.image_history[i][1])

        cv2.destroyWindow(self.window_name)
        return rects
       