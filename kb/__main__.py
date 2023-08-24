import logging, numpy as np, traceback, signal, sys
from queue import Queue

from app.dependencies.cl_parsing import parse_args
from app.dependencies import constants
from app.dependencies import utils
from app.dependencies.videoshow import VideoShow, ThreadedVideoShow
from app.dependencies.filecapturemanager import FileCaptureManager, ThreadedFileCaptureManager
from app.dependencies.middleman import MiddleMan, ThreadedMiddleMan
from kb.dependencies.kbmiddleman import KBMiddleMan
from app.dependencies.classifier import Classifier
from app.dependencies.loggerconfig import configure_logger

logger = logging.getLogger()



class Main:

    def __init__(self):
        self.capture_manager = None
        self.middle_man = None
        self.video_show = None

    # ------------------------------------------------------------------

    def terminate (self, signum, frame):
        
        logger.info("Received termination signal {}".format(signal.strsignal(signum)))
        logger.info ("Finishing work and attempting graceful exit")
        
        if self.middle_man: 
            self.middle_man.shutdown()

    # --------------------------------------------------------------------
    def run(self):

        # Parse the user cla and the system cla. From the system cla we get the module name
        args = parse_args(sys.argv[1:], sys.orig_argv)

        # get the properties from the file
        properties = utils.importProperties(filename = args[constants.CL_PROPERTY_FILE])

        # Configure the logger with the level from the properties file
        configure_logger(properties[constants.LOG_LEVEL]) 

        # Create the 2 queues
        start_queue = Queue(maxsize=properties[constants.QUEUE_SIZE])
        finish_queue = Queue(maxsize=properties[constants.QUEUE_SIZE])

        # Get a class with a threaded read() function to read from the source
        self.capture_manager = ThreadedFileCaptureManager(queue = start_queue)
        self.capture_manager.open(args["sourceFile"])

        frame_props = self.capture_manager.get_frame_properties()
        frame_rate = frame_props["rate"]
        #frame_dims = [frame_props["height"], frame_props["width"]]
    
        # Get a class with a threaded show() function to write the output
        props = properties[constants.VIDEO_SHOW_PROPS]
        self.video_show = ThreadedVideoShow (queue = finish_queue, props=props)
        self.video_show.setFrameRate(frame_rate)

        # Get a class for processing the frames
        classifier = Classifier(args[constants.CL_CLASSIFIER_FILE], props=properties[constants.CLASSIFIER_PROPS])

        # Build the input and output properties for the class
        mm_input_props = {"inputDone": self.capture_manager.isDone, "terminateInput": self.capture_manager.stop, 
                          "warmupProps": (0.002, 20)}
        mm_output_props = {"outputDone": self.video_show.isDone, 
                           "outputStopWhenQEmpty": self.video_show.shouldStopOnEmptyQueue}
    
        # Get the process props from the properties file and add our process function
        mm_process_props = properties[constants.PROCESSING_PROPS]
        mm_process_props["processClass"] = classifier
        mm_process_props["frameDims"] = np.array([frame_props["width"], frame_props["height"]])
    
        self.middle_man = KBMiddleMan(inputQueue = start_queue, outputQueue = finish_queue, inputProps = mm_input_props, 
                                    outputProps = mm_output_props, processProps = mm_process_props)
    
        # Trap the signals and set up terminate() to end our loop gracefully.
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)

    
        # Start the thread that reads from the source
        self.capture_manager.read()
    
        # Start the thread that shows the images
        self.video_show.show()

        # Call middle_man.run(). It reads from input queue, processes, and writes to output queue.
        # It's not threaded so when complete processing is over.
        self.middle_man.run()
    
        # Show the stats
        logger.info(f'from cm: {self.capture_manager.stats()} frames')
        vs_stats = self.video_show.stats()
        logger.info(f'from vs: {vs_stats[0]} frames, {vs_stats[1]} fps')

        # Explicitly call the constructors so that thread.join() will be called
        del(self.video_show)
        del(self.capture_manager)
    

if __name__ == "__main__":
    try:
        main = Main()
        main.run()
        logging.shutdown()
    except BaseException as e:
        # print (e)
        traceback.print_exc()
