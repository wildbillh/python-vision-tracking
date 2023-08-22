
from queue import Queue
import numpy as np
import cv2
from app.dependencies.middleman import ThreadedMiddleMan


class KBMiddleMan (ThreadedMiddleMan):

    def __init__(self, inputQueue: Queue, outputQueue: Queue, inputProps: dict, 
                 outputProps: dict, processProps: dict):
        
        # Call the Base class constructor
        super().__init__(inputQueue=inputQueue, outputQueue=outputQueue, inputProps=inputProps, 
                         outputProps=outputProps, processProps=processProps)

    # --------------------------------------------------------------------------    

    def process (self, frameTuple):

        """
            Override the parent process() method. 
            1. Do any conversions needed
            2. Call the classifier and get the roi's and levels
            3. Do post-processing
        """

        frame, props = frameTuple 
        process_frame = None

        # Get the size of our frame. 
        actual_dim_size = np.array([props["width"], props["height"]])
        
        # Get the size our processing frame and output frame
        process_dim_size = self.process_dims if self.process_dims is not None else actual_dim_size
        finish_dim_size = self.finish_dims if self.finish_dims is not None else actual_dim_size

        # if the process frame is not the size of the finish frame, calculate the mutliplier
        source_to_process_conversion = None 
        if not np.array_equal(process_dim_size, finish_dim_size):
            source_to_process_conversion = finish_dim_size[0] / float(process_dim_size[0])

        # Get a process frame by either resizing or copying the input frame
        if self.process_dims is not None:
            process_frame = cv2.resize(src=frame, dsize=self.process_dims, interpolation=cv2.INTER_AREA)
        else:
            process_frame = np.copy(frame)

        # Set the process frame to gray scale
        process_frame = cv2.cvtColor(process_frame, cv2.COLOR_BGR2GRAY)  
        
        # Get the roi's and levels from the classifier
        objects, levels = self.process_func(process_frame)
         
        # If the finished frame dimension differs from  the actual frame, convert it
        if not np.array_equal(actual_dim_size, finish_dim_size):
            frame = cv2.resize(src=frame, dsize=finish_dim_size)

        color = (0,255,0)
        # if the classifier found any roi's and levels
        if isinstance(levels, np.ndarray):
            object = None
            # For each roi, do something
            for i in range(levels.size):
                object = objects[i]   
                # If the finished frame size is different from the process frame size, scale objects
                object = object if source_to_process_conversion is None else np.multiply(object, source_to_process_conversion, casting='unsafe', dtype=int)
                
                # Write the rectagle
                x, y, w, h = object
                frame = cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

        # Return the processed frame and the given frame properties
        return (frame, props) 