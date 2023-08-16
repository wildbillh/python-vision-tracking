import argparse
from app.dependencies import constants
from typing import List




def parse_args(_args: List[str]) -> dict:

    parser = argparse.ArgumentParser()

    parser.add_argument (
        f'--{constants.CL_PROPERTY_FILE}',
        dest = constants.CL_PROPERTY_FILE,
        help = 'Location of property file',
        default = constants.CL_PROPERTY_FILE_DEFAULT,
        type = str
    )


    parser.add_argument (
        f'--{constants.CL_SOURCE_FILE}',
        dest = constants.CL_SOURCE_FILE,
        help = 'File to read from',
        default = constants.CL_SOURCE_FILE_DEFAULT,
        type = str
    )

    parser.add_argument(
        f'--{constants.CL_CLASSIFIER_FILE}',
        dest =constants.CL_CLASSIFIER_FILE,
        help = 'Classifier file used for Cascade',
        default = constants.CL_CLASSIFIER_FILE_DEFAULT,
        type = str
    )

    parser.add_argument(
        f'--{constants.CL_SKIP_FRAMES}',
        dest = constants.CL_SKIP_FRAMES,
        help = 'How many frames to fast forward or rewind to',
        default = constants.CL_SKIP_FRAMES_DEFAULT,
        type = int
    )

    parser.add_argument(
        f'--{constants.CL_SHOW_TIME}',
        dest = constants.CL_SHOW_TIME,
        help = 'How many frames to fast forward or rewind to',
        default = constants.CL_SHOW_TIME,
        type = bool
    )

    

    return vars(parser.parse_args(_args))