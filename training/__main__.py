
import argparse, logging, sys, traceback
from app.dependencies.loggerconfig import configure_logger
from app.dependencies.utils import generateNegFile
from training.dependencies.extractnegatives import ExtractNegatives
from training.dependencies.extractpositives import ExtractPositives

parser = argparse.ArgumentParser()

parser.add_argument (
        'program',
        type = str,
        choices = ['extract-negatives', 'extract-positives', 'generate-negative-file']
    )

args = vars(parser.parse_args(sys.argv[1:]))
logger = logging.getLogger()



class Main:
    """
    """
    def run(self):
        """
        """

        logger.info(f'Executing: {args["program"]}')

        # Generate Negative images. Selected areas are copied from left-most area
        if args["program"] == "extract-negatives":
            extract_negatives = ExtractNegatives("clips/kb/good-jump.mp4", "good-jump", 
                                             "training/kb/clips/negative")
            extract_negatives.run(processSize=[1440, 810], finishedSize=[960,540]) 
        
        # Generate positive images and pos.txt file
        elif args["program"] == "extract-positives":
            extract_positives = ExtractPositives("clips/kb/good-jump.mp4", "good-jump", 
                                             "training/kb/clips/positive",
                                             "training/kb/pos.txt")    
            extract_positives.run(processSize=[1680, 945], finishedSize=[960,540])

        # Generate the neg.txt file base on the given folders
        elif args["program"] == "generate-negative-file":
            generateNegFile(["training/kb/clips/negative"], "training/kb/neg.txt")



if __name__ == "__main__":
    try:
        configure_logger('INFO')
        main = Main()
        main.run()
        logging.shutdown()
    except BaseException as e:
        # print (e)
        traceback.print_exc()