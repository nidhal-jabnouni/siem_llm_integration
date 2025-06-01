import logging
import os
import sys

# Calculate the absolute path to the log file
current_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of logger.py
log_file_path = os.path.join(current_dir, '..', '..', 'infrastructure', 'logging', 'log_analysis.log')

# Ensure the logging directory exists
log_dir = os.path.dirname(log_file_path)
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)  # exist_ok=True prevents errors if the directory already exists

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file_path)
    ]
)

logger = logging.getLogger(__name__)