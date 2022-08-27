import logging

from constants import PRIMARY_LOG_PATH

logger = logging.getLogger('xtrabackup-assistant')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(filename=PRIMARY_LOG_PATH, mode='a')
file_handler.setFormatter(
    logging.Formatter(fmt='[%(asctime)s] [%(levelname)s] %(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')
)
logger.addHandler(file_handler)
