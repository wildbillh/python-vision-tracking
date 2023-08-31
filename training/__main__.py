
import argparse, logging, sys, traceback
from app.dependencies.loggerconfig import configure_logger
from training.dependencies.extractnegatives import ExtractNegatives
from training.dependencies.extractpositives import ExtractPositives

parser = argparse.ArgumentParser()

parser.add_argument (
        'program',
        type = str,
        choices = ['extract-negatives', 'extract-positives']
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

        if args["program"] == "extract-negatives":
            extract_negatives = ExtractNegatives("clips/kb/fr-trans2.mp4", "fr-trans2", 
                                             "training/kb/clips/negative")
            extract_negatives.run(processSize=[1440, 810], finishedSize=[960,540]) 
        
        elif args["program"] == "extract-positives":
            extract_positives = ExtractPositives("clips/kb/fr-trans2.mp4", "fr-trans2", 
                                             "training/kb/clips/positive",
                                             "training/kb/pos.txt")
            extract_positives.run(processSize=[1440, 810], finishedSize=[960,540])

if __name__ == "__main__":
    try:
        configure_logger('INFO')
        main = Main()
        main.run()
        logging.shutdown()
    except BaseException as e:
        # print (e)
        traceback.print_exc()