import concurrent.futures
from typing import Tuple


class FIFOThreadPool:
    """
        Simple class which uses a pool of threads to submit work. 
    """
    def __init__(self,  func, maxThreads, *funcArgs, **funcKwargs):
        """
            func: the function to execute on submit()
            maxThreads: Max number of threads in the pool
            funcArgs: additional args to send to the function
            funcKwargs: same as above 
        """
        self.max_threads = maxThreads
        self.executor = concurrent.futures.ThreadPoolExecutor(maxThreads)
        self.futures_dict = {}
        self.func = func
        self.func_args = funcArgs
        self.func_kwargs = funcKwargs
        

    # -------------------------------------------------------------    

    def submit(self, index:any, data:any) -> bool:
        """
            Submit data with the given index.
            Returns True is submission is successful
        """

        if len(self.futures_dict) >= self.max_threads:
            return False

        # Execute the function in the thread and store the future in the dictionary
        self.futures_dict[index] = self.executor.submit(self.func, data, *self.func_args, **self.func_kwargs)
        
        return True
    
    # ------------------------------------------------------------

    def receive (self, index:any) -> Tuple[bool, any]:
        # See if data for the desired index is available
        # if so returns (True, data)
        # if still running, returns (False, None)
        # if canceled or never submitted returns (True, None)

        if index not in self.futures_dict:
            return(True, None)
        
        # Get the desired future/thread
        future = self.futures_dict[index]

        # If it's running, nothing to do. Tell them to call later  
        if future.running():
            return (False, None)
        
        # Remove from the dictionary
        self.futures_dict.pop(index, None)

        # If it's completed successfully return the data   
        if future.done:
            return (True, future.result())
        else: # This indicates a cancelled thread
            return (True, None)

    # -----------------------------------------------------------------
    
    def isFull (self) -> bool:
        """
            True if the max threads already in use
        """
        return (len(self.futures_dict) >= self.max_threads)
          
    # -----------------------------------------------------------------
    
    def shutdown(self) -> None:
        self.executor.shutdown()