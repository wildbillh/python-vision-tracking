
# ------------------------ CL Args ---------------------------

CL_PROPERTY_FILE='properties'
CL_PROPERTY_FILE_DEFAULT = './app.properties'
CL_SOURCE_FILE='sourceFile'
CL_SOURCE_FILE_DEFAULT = 'clips/fr-trans2.mp4'
CL_CLASSIFIER_FILE='classifier'
CL_CLASSIFIER_FILE_DEFAULT = 'cascade/cascade-24stage.xml'
CL_SKIP_FRAMES = 'skipFrames'
CL_SKIP_FRAMES_DEFAULT = 300
CL_SHOW_TIME = 'showTime'
CL_SHOW_TIME_DEFAULT = False

# ---------------------- Properties -------------------------
WINDOW_NAME = 'windowName'


TIME_COLOR = 'timeColor'
TIME_THICKNESS = 'timeThickness'
QUEUE_SIZE = 'queueSize'
SKIP_FRAME_SIZE = 'skipFrameSize'

# Props
CLASSIFIER_PROPS = 'classifierProps'
VIDEO_SHOW_PROPS = 'videoShowProps'
PROCESSING_PROPS = 'processingProps'

REQUIRED_PROPERTIES = {
    TIME_COLOR: tuple,
    TIME_THICKNESS: int,
    QUEUE_SIZE: int,
    SKIP_FRAME_SIZE: int,
    CLASSIFIER_PROPS: dict,
    VIDEO_SHOW_PROPS: dict
}
