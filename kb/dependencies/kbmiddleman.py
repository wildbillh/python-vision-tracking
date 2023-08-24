
import cv2, numpy as np
from queue import Queue
from app.dependencies.middleman import ThreadedMiddleMan


class KBMiddleMan (ThreadedMiddleMan):

    def __init__(self, inputQueue: Queue, outputQueue: Queue, inputProps: dict, 
                 outputProps: dict, processProps: dict):
        
        # Call the Base class constructor
        super().__init__(inputQueue=inputQueue, outputQueue=outputQueue, inputProps=inputProps, 
                         outputProps=outputProps, processProps=processProps)
        
        # Get the size our processing frame and output frame
        process_dim_size = self.process_dims if self.process_dims is not None else self.frame_dims
        finish_dim_size = self.finish_dims if self.finish_dims is not None else self.frame_dims

        # Calculate the scaling needed (process to finished) to draw the rectangles 
        self.process_to_final_conversion = None
        if not np.array_equal(process_dim_size, finish_dim_size):
            self.process_to_final_conversion = finish_dim_size[0] / float(process_dim_size[0])


    # --------------------------------------------------------------------------    

    def process (self, frameDict: dict) -> dict:

        """
            Override the parent process() method. 
            1. Do any conversions needed
            2. Call the classifier and get the roi's and levels
            3. Do post-processing
        """

        frame = frameDict["frame"]
        props = frameDict["props"]
        process_frame = None

        # Get a process frame by either resizing or copying the input frame
        if self.process_dims is not None:
            process_frame = cv2.resize(src=frame, dsize=self.process_dims, interpolation=cv2.INTER_AREA)
        else:
            process_frame = np.copy(frame)

        # If the finished frame dimension differs from  the actual frame, convert it
        if not np.array_equal(self.frame_dims, self.finish_dims):
            frame = cv2.resize(src=frame, dsize=self.finish_dims)

        # Set the process frame to gray scale
        process_frame = cv2.cvtColor(process_frame, cv2.COLOR_BGR2GRAY)  
        
        # Get the roi's and levels from the classifier
        objects, levels = self.process_class.process(process_frame)
          
        # The highest level rectangle will be green, all others blue
        max_color = (0,255,0)
        color = (255,0,0)

        # if the classifier found any roi's and levels
        if isinstance(levels, np.ndarray):
            # Get the index of the level with the highest value
            max_index = levels.argmax()
            object = None
            # For each roi, do something
            for i in range(levels.size):
                object = objects[i]   
    
                # If the finished frame size is different from the process frame size, scale objects
                if self.process_to_final_conversion is not None and self.process_to_final_conversion != 1.0:
                    object = (object * self.process_to_final_conversion).astype(int)
                
                # Write the rectangle
                x, y, w, h = object
                frame = cv2.rectangle(frame, (x, y), (x + w, y + h), max_color if i == max_index else color, 3)

        # Return the processed frame and the given frame properties
        return ({"frame": frame, "props": props}) 