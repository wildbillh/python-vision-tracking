
import ast, cv2, logging, numpy as np, os
from jproperties import Properties
from typing import Dict, Tuple
from app.dependencies import constants

logger = logging.getLogger()

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
            logger.warning(f'Property {key} not found in defaults. Ignoring')

    return new

# --------------------------------------------------------------------

def removeROIs (frame: np.ndarray, rectList: list[Tuple[int,int,int,int]], sourceDirection: str ='LEFT') -> np.ndarray:
    """
		Given rectangle dimensions of a frame selection, replace the roi with an
		equivalent copy in the given source direction
    """

    # Get a copy of the frame
    frame_copy = frame.copy()
    frame_h, frame_w, frame_color = frame_copy.shape

    if sourceDirection not in ['LEFT', 'RIGHT', 'TOP', 'BOTTOM']:
        logger.warning ("Invalid source direction given. Assuming LEFT")
        sourceDirection = "LEFT"

    for rect in rectList:
        x1, y1, x2, y2 = rect

        # Get width and height of rectangle
        width = x2-x1
        height = y2 - y1

        if sourceDirection == 'LEFT':
            if x1 < width:
                logger.warning("Unable to perform left-wise ROI remove, trying right-wise")
                sourceDirection = "RIGHT"
            else:
                frame_copy[y1:y2, x1:x2, 0:3] = frame[y1:y2, (x1 - width):x1, 0:3]
                continue

        if sourceDirection == 'RIGHT':
            if x2 + width > frame_w:
                logger.warning("Unable to perform right-wise ROI remove")
            else:
                frame_copy[y1:y2, x1:x2, 0:3] = frame[y1:y2, x2:(x2 + width), 0:3]
            continue    

        if sourceDirection == 'TOP':
            if y1 < height:
                logger.warning("Unable to perform top-wise ROI remove, trying bottom-wise")  
                sourceDirection = 'BOTTOM'
            else: 
                frame_copy[y1:y2, x1:x2, 0:3] = frame[(y1 - height):y1, x1:x2, 0:3]
                continue

        if sourceDirection == 'BOTTOM': # BOTTOM
            if y2 + height > frame_h:
                logger.warning("Unable to perform bottom-wise ROI remove")
                continue
            else: 
                frame_copy[y1:y2, x1:x2, 0:3] = frame[y2:(y2 + height), x1:x2, 0:3]

    return frame_copy

# --------------------------------------------------------------------------

def scaleImages (sourceDir:str, targetDir:str, size:list) -> int:
    """
        Take the images from the source directory, scale them and write to the target Directory
    """
    count = 0
    file_list = os.listdir(sourceDir)
    for file in file_list:
        img = cv2.imread(f'{sourceDir}/{file}')
        img = cv2.resize(img, size)

        cv2.imwrite(f'{targetDir}/{count}.jpg', img)
        count += 1

    return count

# -------------------------------------------------------------------------------

def getScaledImagesFromVideo (filename: str, targetDir: str, targetPrefix: str, size:list, frameScale: int = 1):
    """
        Reads all of the images from a video file, scales them and write to the target dir
        if frameScale is > 1, writes every nth frame
    """
    cap = cv2.VideoCapture(filename)
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f'Converting from {original_width}x{original_height} to {size[0]}x{size[1]}')

    count = 0
    write_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % frameScale == 0:
            frame = cv2.resize(frame, size)
            cv2.imwrite(f'{targetDir}/{targetPrefix}-{count}.jpg', frame)
            write_count += 1
        
        count += 1

    cap.release()
    return write_count

# -------------------------------------------------------------------------------

def generateNegFile(sourceDir: str, targetFile: str):
    """
        Generates a negative file for training based on the files in the sourceDir
    """
    count = 0
    flags = 'w'

    if os.path.isfile(targetFile):
        logger.info(f'File: {targetFile} exists. Appending....')
        flags = 'a'

    with open(targetFile, flags) as f:

        for filename in os.listdir(sourceDir):
            f.write(f'{sourceDir}/{filename}\n')
            count +=1

    logger.info(f'Wrote {count} files to {targetFile}')
    return count
