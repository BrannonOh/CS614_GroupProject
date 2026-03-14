import logging
import os
from datetime import datetime

def setup_logger():
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Log filename with timestamp (YYMMDD_HHMMSS)
    log_filename = f"logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO, # log normal program events
        format="%(asctime)s | %(levelname)s | %(message)s", # Example: 2026-03-02 20:17:09,123 | <Log Level Type> | <Message>
        handlers=[
            logging.FileHandler(log_filename),    # saves log to file
            logging.StreamHandler()               # also prints to terminal
        ]
    )
    
    return logging.getLogger(__name__) # create and return a logger that is associated with the current Python module

logger = setup_logger()