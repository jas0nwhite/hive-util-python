# -*- coding: utf-8 -*-
"""
Timer context object
"""


class Timer(object):

    def __init__(self, message=None, verbose=True):
        self.__message = message
        self.__verbose = verbose

    def __enter__(self):
        import time

        self.__start_time = time.time()

    def __exit__(self, *_):
        import time
        if self.__verbose:
            if self.__message is not None:
                print(f'{self.__message}: ', end='')
            else:
                print('Elapsed time: ')

            print(f'{time.time() - self.__start_time:.6f} seconds', flush=True)
