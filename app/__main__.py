import traceback
from queue import Queue
import time
import sys

from app.dependencies.cl_parsing import parse_args
from app.dependencies import constants
from app.dependencies import utils
from app.dependencies.videoshow import VideoShow, ThreadedVideoShow
from app.dependencies.filecapturemanager import FileCaptureManager, ThreadedFileCaptureManager
from app.dependencies.middleman import MiddleMan, ThreadedMiddleMan
from app.dependencies.classifier import Classifier


def main():

    
    # Parse the CLA
    args = parse_args(sys.argv[1:])

    # get the properties from the file
    properties = utils.importProperties(filename = args[constants.CL_PROPERTY_FILE])

    # Create the 2 queues
    start_queue = Queue(maxsize=64)
    finish_queue = Queue(maxsize=64)

    # Get a class with a threaded read() function to read from the source
    capture_manager = ThreadedFileCaptureManager(queue = start_queue)
    capture_manager.open("clips/fr-trans2.mp4")

    frame_rate = capture_manager.get_frame_properties()["rate"]
    
    # Get a class with a threaded show() function to write the output
    props = properties[constants.VIDEO_SHOW_PROPS]
    #props["showOutput"] = False
    video_show = ThreadedVideoShow (queue = finish_queue, props=props)
    video_show.setFrameRate(0)

    # Get a class for processing the frames
    classifier = Classifier(args[constants.CL_CLASSIFIER_FILE], props=properties[constants.CLASSIFIER_PROPS])

    # Get a class which reads from the input queue, process the frame and writes to the output queue
    #middle_man = ThreadedMiddleMan(inputQueue = start_queue, outputQueue = finish_queue, threads = 5)
    
    # Build the input and output properties for the class
    mm_input_props = {"inputDone": capture_manager.isDone, "terminateInput": capture_manager.stop, "warmupProps": (0.002, 20)}
    mm_output_props = {"outputDone": video_show.isDone}
    mm_process_props = {"processFunc": classifier.process, "threads": 5}
    
    middle_man = ThreadedMiddleMan(inputQueue = start_queue, outputQueue = finish_queue, inputProps = mm_input_props, 
                                    outputProps = mm_output_props, processProps = mm_process_props)

    start = time.time()
    
    # Start the thread reading from the source
    capture_manager.read()
    # Start the thread that shows the images
    video_show.show()

    
    #middle_man.setProcessProperties (classifier.process)

    # Call middle_man.run who will read from input queue, process, and write to output queue
    middle_man.run()
    
    vs_stats = video_show.stats()
    print (f'from cm: {capture_manager.stats()} frames')
    print (f'from vs: {vs_stats[0]} frames, {vs_stats[1]} fps')

    # Explicitly call the constructors so that thread.join() will be called
    del(video_show)
    del(capture_manager)
    

if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        # print (e)
        traceback.print_exc()
