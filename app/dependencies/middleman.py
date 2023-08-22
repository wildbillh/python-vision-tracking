import logging, sys, time
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

    def process (self, frameTuple):
        """
            This method is overwritten by a child class, else it just returns the frame and props
            that were sent to it. 
        """
        
        if self.first_process_call:
            logger.info ("Warning: The process() method is usually overwritten by a child class")
            self.first_process_call = False
        return (frameTuple)
    
    # -----------------------------------------------------------------------
    # The _functions below are not too practical in the non threaded version of the class.
    # The purpose for them is to allow the same run() method to be used in the non-threaded 
    # and threaded class

    def _prepare(self):
        self.last_process_tuple = None
        self.read_frame_number = self.write_frame_number = 0

    # -----------------------------------------------------------------------
    
    def _submit (self, frame_tuple):

        self.last_process_tuple = self.process(frame_tuple)
        self.write_frame_number += 1
        return

    # -----------------------------------------------------------------------

    def _receive (self):
        self.read_frame_number += 1
        return (True, self.last_process_tuple)
    
    # -----------------------------------------------------------------------
    
    def _isFull(self):
        return False
    
    # -----------------------------------------------------------------------
    
    def _shutdown (self):
        pass

    # ---------------------------------------------------------------------------------

    def run (self):
        """
            This method does the real work of managing queues and threadpools. The end result
            is that the self.process() method is called on a frame and when complete, the frame is 
            written to the output queue.
            Note that by using the _methods(), the same run() method can be used by threaded and 
            non-thread versions
        """
      
        self.should_run = True
        start = time.time()
        
        # If we defined a warmup period for the input queue, execute it
        # The code handles this case without the function but it's 
        # convenient for detecting input issues
        if self.input_warmup_sleep != 0:
            self.WarmUpInputQueue()

        #thread_pool = FIFOThreadPool(self.process_func, self.threads)
        #thread_pool = FIFOThreadPool(self.process, self.threads)
        self._prepare()
        exit_when_queues_empty = False
    
        # Main loop
        while self.should_run:
           
            # check input queue and thread pool insertion availability
            if not self.in_q.empty() and not self._isFull(): #self._isFull():
                frame_tuple = self.in_q.get()
                self._submit(frame_tuple)

            # Check to see if a processed frame is available
            if not self.out_q.full():           
                done, processed_tuple = self._receive()

                # If success, write the processed frame to the output queue
                if done and processed_tuple is not None:
                    self.out_q.put(processed_tuple)
           
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

        self._shutdown()
        logger.info(f'from mm: {self.write_frame_number} frames, {self.write_frame_number / (time.time() - start)} fps')



# =============================================================================

class ThreadedMiddleMan (MiddleMan):

    def __init__(self, inputQueue: Queue, outputQueue: Queue, inputProps: dict, 
                 outputProps: dict, processProps: dict):
        
        # Call the Base class constructor
        super().__init__(inputQueue=inputQueue, outputQueue=outputQueue, inputProps=inputProps, 
                         outputProps=outputProps, processProps=processProps)
        
        self.daemon = None       

    # -----------------------------------------------------------------------

    def _prepare (self):

        self.thread_pool = FIFOThreadPool(self.process, self.threads) 
        self.read_frame_number = self.write_frame_number = 0   

    # -----------------------------------------------------------------------
    
    def _submit (self, frame_tuple):

        self.thread_pool.submit(self.write_frame_number, frame_tuple)
        self.write_frame_number += 1
        return

    # -----------------------------------------------------------------------
    
    def _receive (self):

        done, process_tuple = self.thread_pool.receive(self.read_frame_number)
        if done and process_tuple is not None:
            self.read_frame_number += 1

        return (done, process_tuple)
    
    # -----------------------------------------------------------------------
    
    def _isFull(self):
        return self.thread_pool.isFull()
    
    # -----------------------------------------------------------------------
    
    def _shutdown (self):
        self.thread_pool.shutdown()
        

    

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