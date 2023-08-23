
import logging
import logging.config
from app.dependencies import constants

logger = logging.getLogger()

config = {   
        
    "logging": {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "single-line": {
                "class": "logging.Formatter",
                "style": "{",
                "datefmt": "%I:%M:%S",
                "format": "{levelname:}: {message:s}"
            }
        },
        "handlers": {
            "console":{
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "single-line",
                "stream" : "ext://sys.stdout"
            }
        },
        "loggers": { },
        "root": {
            "handlers": ["console"],
            "level": constants.DEFAULT_LOG_LEVEL
        }
    }      
}

# --------------------------------------------------

def configure_logger (level: str):
    """ Configures logging with the json above and inserts the 
        passed level
    """
  
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    # If the level is supplied
    if (level is not None and isinstance(level, str) and level in valid_levels):
        config["logging"]["root"]["level"] = level
        # Configure the logger
        logging.config.dictConfig(config['logging'])
    else:
        # Configure the logger
        logging.config.dictConfig(config['logging']) 
        logger.error("Invalid logger level given. Using default")   
            
    
    