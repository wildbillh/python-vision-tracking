import ast
import cv2
import numpy as np
from jproperties import Properties
from typing import Dict, Type
from app.dependencies import constants

USE_CUDA = False


def setUseCuda ():
    """
        Set the value of the global
    """
    global USE_CUDA
    USE_CUDA = (cv2.cuda.getCudaEnabledDeviceCount() > 0)

# ---------------------------------------------------------------------    

def getImageRectangle(img: np.ndarray, filename=None) -> np.ndarray:
    """ Get a region of interest and write to a file if the filename is sent
    """

    r = cv2.selectROI("clipper", img)
    cropped = img[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]

    if filename != None:
        cv2.imwrite(cropped, filename)

    return cropped


# ----------------------------------------------------------------------

def resizeByWidth(height, width, desired_width):
    if width <= desired_width:
        return height, width

    scale_factor = width / desired_width
    return int(width / scale_factor), int(height / scale_factor)


# -----------------------------------------------------------------

def importProperties(filename='./app.properties') -> dict:
    """
        Reads the properties file and returns as a dictionary
    """
    configs = Properties()
    with open(filename, 'rb') as config_file:
        configs.load(config_file, "utf-8")

    items = configs.items()
    properties_dict = {}
    for item in items:
        # Try to evaluate the returned property.
        # If it fails we assume it's a string
        try:
            properties_dict[item[0]] = ast.literal_eval(item[1].data)
        except BaseException: 
            print(item, type(item))
            properties_dict[item[0]] = str(item[1].data)

    verifyRequiredProperties(properties_dict)

    return properties_dict


# ----------------------------------------------------------------------

def verifyRequiredProperties(properties: Dict):
    """
        Verifies the required properties and types are found
    """

    # for each entry in the required_props dictionary
    for key_name in constants.REQUIRED_PROPERTIES.keys():
        # if the key is not there throw an exception
        if key_name not in properties:
            raise Exception(f'Did not find property {key_name} in properties')
        # If the type is not correct, throw an exception
        elif not isinstance(properties[key_name], constants.REQUIRED_PROPERTIES[key_name]):
            raise Exception(f'key {key_name} was expected to be of type {constants.REQUIRED_PROPERTIES[key_name]}')

# -------------------------------------------------------------

def mergeWithDefault (source: dict, default: dict) -> dict:
    """
        Returns a new dictionary with any keys in the source
        replacing those in the default
    """

    # If no properties were provided, return the default
    if not source:
        return default
    
    new = default.copy()
    for key in source.keys():
        if key in new:
            new[key] = source[key]
        else:
            print(f'Property {key} not found in defaults. Ignoring')

    return new