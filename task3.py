from test_lib.lib1 import hello
from log import logger


def start_script():
    logger.debug('in task3')
    print(hello)
    logger.info('logging in task3')