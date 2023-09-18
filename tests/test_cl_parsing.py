import unittest, io
from app.dependencies.cl_parsing import parse_args
from app.dependencies import constants


class CLParsingTest (unittest.TestCase):
    
    def test_all_args_given(self):
        #Verify the return dict when all arguments are given, except purge
        
        cl_args = [
            f"--{constants.CL_PROPERTY_FILE}", "propertyFile", 
            f"--{constants.CL_SOURCE_FILE}", "sourceFile", 
            f"--{constants.CL_CLASSIFIER_FILE}", "classifierFile", 
            f"--{constants.CL_SKIP_FRAMES}", "30",
            f"--{constants.CL_SHOW_TIME}"]

        args = parse_args(cl_args, ['-m', 'kb'])
        expected = {
            constants.CL_PROPERTY_FILE: 'propertyFile',     
            constants.CL_SOURCE_FILE: "sourceFile",
            constants.CL_CLASSIFIER_FILE: "classifierFile",
            constants.CL_SKIP_FRAMES: 30,
            constants.CL_SHOW_TIME: True, 
            "module": 'kb'}

        self.assertEqual(args, expected)
   

    """    
    # -----------------------------------------------
    
    def test_default_args(self):

        # Verify the return dict when all arguments are defaulted
        args = parse_args([], None) 
        expected = {
            constants.ARGS_LOG_LEVEL: constants.ARGS_DEFAULT_LOG_LEVEL, 
            constants.ARGS_NO_PROBE: False, 
            constants.ARGS_MESSAGE: None,
            constants.ARGS_STDIN_MESSAGE: False,
            constants.ARGS_STDIN_ZIPFILE: False,
            constants.ARGS_PURGE_DB: constants.ARGS_PURGE_DB_DEFAULT
            }
        
        self.assertEqual(args, expected)  
"""