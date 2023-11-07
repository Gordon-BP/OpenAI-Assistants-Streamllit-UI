import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Create a logger
logger = logging.getLogger("streamlit-frontend")
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
    handler.close()
if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(os.environ.get("LOGFILE"))
    console_handler = logging.StreamHandler()

    # Define the log message format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
