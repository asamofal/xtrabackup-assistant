import logging

from constants import PRIMARY_LOG_PATH, ROTATION_LOG_PATH

logger = logging.getLogger('xtrabackup-assistant')
logger.setLevel(logging.INFO)
primary_file_handler = logging.FileHandler(filename=PRIMARY_LOG_PATH, mode='a')
primary_file_handler.setFormatter(
    logging.Formatter(fmt='[%(asctime)s] [%(levelname)s] %(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')
)
logger.addHandler(primary_file_handler)

rotation_logger = logging.getLogger('rotation')
rotation_logger.setLevel(logging.INFO)
rotation_file_handler = logging.FileHandler(filename=ROTATION_LOG_PATH, mode='a')
rotation_file_handler.setFormatter(
    logging.Formatter(fmt='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
)
rotation_logger.addHandler(rotation_file_handler)
