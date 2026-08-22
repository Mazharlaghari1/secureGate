import logging
import sys

def setup_logging():
    """
    Sets up application-wide structured logging to stdout.
    """
    logger = logging.getLogger("event_access")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    # Set PyMongo and Uvicorn log levels if needed, to avoid noise
    logging.getLogger("pymongo").setLevel(logging.WARNING)
