
# ------------------------ CL Args ---------------------------

CL_PROPERTY_FILE='properties'
CL_PROPERTY_FILE_DEFAULT = 'app.properties'
CL_SOURCE_FILE='sourceFile'
CL_CLASSIFIER_FILE='classifierFile'
CL_SKIP_FRAMES = 'skipFrames'
CL_SKIP_FRAMES_DEFAULT = 300
CL_SHOW_TIME = 'showTime'
CL_SHOW_TIME_DEFAULT = False

# ---------------------- Properties -------------------------
WINDOW_NAME = 'windowName'
DEFAULT_LOG_LEVEL='INFO'
LOG_LEVEL = 'logLevel'

TIME_COLOR = 'timeColor'
TIME_THICKNESS = 'timeThickness'
QUEUE_SIZE = 'queueSize'
SKIP_FRAME_SIZE = 'skipFrameSize'

# Props
CLASSIFIER_PROPS = 'classifierProps'
VIDEO_SHOW_PROPS = 'videoShowProps'
PROCESSING_PROPS = 'processingProps'

REQUIRED_PROPERTIES = {
    QUEUE_SIZE: int,
    SKIP_FRAME_SIZE: int,
    CLASSIFIER_PROPS: dict,
    VIDEO_SHOW_PROPS: dict,
    CL_CLASSIFIER_FILE: str, 
    CL_SOURCE_FILE: str
}
