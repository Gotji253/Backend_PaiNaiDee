import logging
import sys

# Configuration
LOG_LEVEL = "INFO"  # Default log level, can be configured via environment variable later
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
# Example for JSON logging if preferred in the future:
# LOG_FORMAT_JSON = '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "module": "%(module)s", "funcName": "%(funcName)s", "lineno": "%(lineno)d", "message": "%(message)s"}'


def setup_logging():
    """
    Configures basic logging for the application.
    """
    # Get the root logger
    logger = logging.getLogger() # Root logger
    logger.setLevel(LOG_LEVEL)

    # Create a handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(LOG_LEVEL)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)

    # Add the handler to the logger
    # Check if handlers are already present to avoid duplication if called multiple times
    if not logger.handlers:
        logger.addHandler(handler)

    # Configure specific loggers if needed, e.g., uvicorn, sqlalchemy
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Quieten uvicorn access logs if too noisy
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO) # Or WARNING for less SQL noise

# Call setup_logging() when this module is imported, or call it explicitly in main.py
# For now, let's make it so it needs to be called explicitly.

# Example usage:
# import logging
# logger = logging.getLogger(__name__)
# logger.info("This is an info message.")
# logger.error("This is an error message.")

# To be called from main.py at startup:
# from app.core.logging import setup_logging
# setup_logging()
