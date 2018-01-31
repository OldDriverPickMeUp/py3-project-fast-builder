import logging

import os

import sys

LOG_LEVEL = os.environ.get('LOG_LEVEL', logging.DEBUG)
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(LOG_FORMAT)

std_err_handler = logging.StreamHandler(sys.stderr)
std_err_handler.setFormatter(formatter)
std_err_handler.setLevel(logging.ERROR)

std_out_handler = logging.StreamHandler(sys.stdout)
std_out_handler.setFormatter(formatter)
std_out_handler.setLevel(LOG_LEVEL)

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, handlers=[std_err_handler, std_out_handler])

logger = logging.getLogger('logger')


def start_script():
    logger.info('text')
    logger.error('erere')


if __name__ == '__main__':
    start_script()
