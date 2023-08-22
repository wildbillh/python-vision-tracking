import logging, time
from queue import Queue
from threading import Thread
from typing import Tuple
from collections.abc import Callable
from app.dependencies.fifothreadpool import FIFOThreadPool
import cv2
import numpy as np

logger = logging.getLogger()

class MiddleMan:
    """
        Reads an input queue, does works, writes the frame to an ouput queue
    """

    def __init__(self, inputQueue: Queue, outputQueue: Queue, inputProps: dict, outputProps: dict, processProps: dict):
        """
            Verify the needed properties where passed and set the instance vars
        """
        # Queues
        self.in_q = inputQueue
        self.out_q = outputQueue

        # Verify the required properties are present
        self.verifyProperties(inputProps=inputProps, outputProps=outputProps, processProps=processProps)

        # --------------- Input properties ---------------
        # Method to call to see if input is still processing
        self.input_is_done_test = inputProps["inputDone"]
        # Method to call to terminate the input
        self.input_shut_down = inputProps["terminateInput"]
        # How long to sleep and how many iterations to try to get the first input in the queue
        self.input_warmup_sleep, self.input_warmup_iterations = inputProps["warmupProps"]
        
        # ----------------- Output properties ------------------------
        # Define the test to see if the output class has stopped 
        self.output_is_done_test = outputProps["outputDone"]
        self.output_stop_when_q_empty_func = outputProps["outputStopWhenQEmpty"]
        self.output_stop_called = False

        # --------------  Process properties ------------------------
        # Number of threads for calling process functions
        self.threads = processProps["threads"] if "threads" in processProps else 2
        # Process function 
        self.process_func = processProps["processFunc"]
        
        
        # The following values can be none or [int, int]
        # Get the actual dimensions of the incoming frames
        self.frame_dims = processProps["frameDims"]
        # Dimensions of classifier image
        self.process_dims = processProps["processDims"]
        # Dimensions of final Image
        self.finish_dims = processProps["finishDims"]
        
        
        self.should_run = True
        # Time to wait for new resources
        self.loop_wait = 0.0001

        self.first_process_call = True

    # ----------------------------------------------------------------

    def verifyProperties(self, inputProps: dict, outputProps: dict, processProps: dict):
        """
            Verify that the required keys are in the given property dictionaries
        """
         
        if not "inputDone" in inputProps:
            raise Exception("Missing inputDone in inputProps")
        if not "terminateInput" in inputProps:
            raise Exception("Missing terminateInput in inputProps")
        if not "warmupProps" in inputProps:
            raise Exception("Missing warmupProps in inputProps")
        
        if not "outputDone" in outputProps:
            raise Exception("Missing outputDone in OutputProps")
        
        if not "processFunc" in processProps:
            raise Exception("Missing processFunc in processProps")
        
        if not "frameDims" in processProps:
            processProps["frameDims"] = None
        
        if not "processDims" in processProps:
            processProps["processDims"] = None
        
        if not "finishDims" in processProps:
            processProps["finishDims"] = None
        
    # ---------------------------------------------------------------------------------------

    def WarmUpInputQueue (self):
        """
            Allow time for input queue to have at least one frame
        """
        
        iter_count = 0    

        while self.in_q.empty():    
            time.sleep(self.input_warmup_sleep) # Give time for start_queue to populate
            iter_count += 1
            
            if iter_count > self.input_warmup_iterations:       
                raise Exception("No data in start_queue after timeout period")  
            
    # --------------------------------------------------------------------------------------
    
    def run (self):
        """
            Start the non threaded run 
        """
        start = time.time()
        
        # If we defined a warmup period for the input queue, execute it
        if self.input_warmup_sleep != 0:
            self.WarmUpInputQueue()
        
        # Count the frames
        frame_count = 0
        # Set a boolean that is set to true if input is complete
        exit_when_queues_empty = False
        
        # Main loop
        while self.should_run: 
            print(self.in_q.qsize(), self.out_q.qsize(), flush=True)
            # If the input queue has frames and the output queue is not full, process a frame
            if not self.in_q.empty() and not self.out_q.full():
           
                frame_tuple = self.in_q.get()
                self.out_q.put(self.process_func(frame_tuple))
                frame_count += 1
            
            else: # Either in queue is empty or out queue is full, so sleep
                time.sleep(self.loop_wait)

             # if exit when empty is set, set exit bool when queues are empty
            if exit_when_queues_empty and self.in_q.empty():
                
                if self.out_q.empty():
                    self.should_run = False 
                # Tell output to quit when q is depleted
                elif not self.output_stop_called:
                    print("Telling output to stop", flush = True)
                    self.output_stop_when_q_empty_func()
                    self.output_stop_called = True
                   

            # Check to see if the input class is complete
            if not exit_when_queues_empty and self.input_is_done_test():
                print ("Quit receieved from Capture Manager", flush=True)
                exit_when_queues_empty = True
                continue

            if self.output_is_done_test():
                print ('Cancel request received from Video Show', flush=True)
                if (self.input_shut_down != None):
                    self.input_shut_down()
                self.should_run = False  
    
        run_time = time.time() - start
        print(f'{frame_count} frames in {run_time}s, fps = {frame_count / run_time}', flush=True)

# =============================================================================

class ThreadedMiddleMan (MiddleMan):

    def __init__(self, inputQueue: Queue, outputQueue: Queue, inputProps: dict, 
                 outputProps: dict, processProps: dict):
        
        # Call the Base class constructor
        super().__init__(inputQueue=inputQueue, outputQueue=outputQueue, inputProps=inputProps, 
                         outputProps=outputProps, processProps=processProps)
        
        self.daemon = None       

    # ---------------------------------------------------------------------------------

    def run (self):
      
        self.should_run = True
        read_frame_number = 0
        write_frame_number = 0
        start = time.time()
        
        # If we defined a warmup period for the input queue, execute it
        # The code handles this case without the function but it's 
        # convenient for detecting input issues
        if self.input_warmup_sleep != 0:
            self.WarmUpInputQueue()

        #thread_pool = FIFOThreadPool(self.process_func, self.threads)
        thread_pool = FIFOThreadPool(self.process, self.threads)
        exit_when_queues_empty = False
    
        # Main loop
        while self.should_run:

            # check input queue and thread pool insertion availability
            if not self.in_q.empty() and not thread_pool.isFull():

                frame_tuple = self.in_q.get()
                thread_pool.submit(write_frame_number, frame_tuple)
                write_frame_number += 1

            # Check to see if a processed frame is available
            if not self.out_q.full():
                done, processed_tuple = thread_pool.receive(read_frame_number)
                if done and processed_tuple is not None:
                    self.out_q.put(processed_tuple)
                    read_frame_number += 1
           
            # if exit when empty is set, set exit bool when queues are empty
            if exit_when_queues_empty and self.in_q.empty():
                if self.out_q.empty():
                    self.should_run = False
                    continue
                elif not self.output_stop_called:
                    logger.debug("output stop on empty called")
                    self.output_stop_called = True
                    self.should_run = False

            # Check to see if the input class is complete
            if not exit_when_queues_empty and self.input_is_done_test():
                logger.debug ("Input is depleted")
                # Set the bool so that we'll exit when queues are empty
                exit_when_queues_empty = True              

            # Check the ouput to see if the user wants to quit
            if self.output_is_done_test():
                logger.info('Cancel request received from Ouput')
                self.should_run = False 
                # Since the user wants to quit, tell the input to queue
                if (self.input_shut_down != None):
                    self.input_shut_down()
            else:
                time.sleep(self.loop_wait)
            

        thread_pool.shutdown()
        

        logger.info(f'from mm: {write_frame_number} frames, {write_frame_number / (time.time() - start)} fps')
        
        """
        try:
            self.daemon.join()
        except: Exception
        """

    # -----------------------------------------------------------------

    def process (self, frameTuple):
        """
            This method is overwritten by a child class, else it just returns the frame and props
            that were sent to it. 
        """
        
        if self.first_process_call:
            logger.info ("Warning: The process() method is usually overwritten by a child class")
            self.first_process_call = False
        return (frameTuple)