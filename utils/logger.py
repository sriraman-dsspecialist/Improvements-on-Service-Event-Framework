import os
import logging
from datetime import datetime
from utils.config import config

logger_package_string = "Logger: "

# Include all the additional logging information
global logger
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logs_folder = os.path.join(project_root, 'logs')
os.makedirs(logs_folder, exist_ok=True)

logger = logging.getLogger(__name__)
logger.info(f"{logger_package_string}Logger initiated")

syslog = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(message)s')
syslog.setFormatter(formatter)

logger.setLevel(logging.INFO)
logger.addHandler(syslog)

logs_file_path = os.path.join(logs_folder, f'SEF_Improvement_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
file_handler = logging.FileHandler(logs_file_path)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger = logging.LoggerAdapter(logger)
logger.info(f"{logger_package_string}Log file: {logs_file_path}")
