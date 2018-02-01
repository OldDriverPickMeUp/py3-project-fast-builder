from test_lib.lib1 import hello
import logging


def start_script():
    logging.debug('in task3')
    print(hello)
    raise Exception('asdasasd')
    logging.info('logging in task3')