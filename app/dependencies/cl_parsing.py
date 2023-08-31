import argparse
from app.dependencies import constants
from typing import List




def parse_args(args: List[str], systemArgs: List[str]) -> dict:
    
    # Parse the system command line arguments to get the module name
    system_parser = argparse.ArgumentParser()
    system_parser.add_argument(
        "-m",
        dest = "module",
        type = str,
    )

    module = vars(system_parser.parse_known_args(systemArgs)[0])["module"]

    # Parse the user command line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument (
        f'--{constants.CL_PROPERTY_FILE}',
        dest = constants.CL_PROPERTY_FILE,
        help = 'Location of property file',
        default = f'{module}/{constants.CL_PROPERTY_FILE_DEFAULT}',
        type = str
    )


    parser.add_argument (
        f'--{constants.CL_SOURCE_FILE}',
        dest = constants.CL_SOURCE_FILE,
        help = 'Video source file',
        type = str
    )

    parser.add_argument(
        f'--{constants.CL_CLASSIFIER_FILE}',
        dest =constants.CL_CLASSIFIER_FILE,
        help = 'Classifier file used for Cascade',
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

    # Get the user CLA's as a dictionary
    return_dict = vars(parser.parse_args(args))

    # Add the module name to the dictionary
    return_dict["module"] = vars(system_parser.parse_known_args(systemArgs)[0])["module"]
    
    return return_dict