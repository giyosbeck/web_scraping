import logging
import logging.config
import os
from pathlib import Path


def setup_logging():
    """
    Set up logging configuration using dictConfig with rotating file handler.
    Creates logs directory if it doesn't exist and configures logging to write to logs/app.log.
    """
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'rotating_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'standard',
                'level': 'INFO'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'INFO'
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['rotating_file', 'console']
        }
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name):
    """
    Get a configured logger instance.
    
    Args:
        name (str): Name of the logger, typically __name__ of the calling module
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)