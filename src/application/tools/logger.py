
import logging
import sys
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('src\infrastructure\logging\log_analysis.log')
    ]
)

logger = logging.getLogger(__name__)