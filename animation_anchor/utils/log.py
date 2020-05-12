import inspect
import logging
import sys

import functools
import cv2

def draw(frame, landmarks):
    frame = frame.copy()
    return cv2.rectangle(frame, tuple(landmarks[0]), tuple(landmarks[1]), (0, 255, 0), 3)


def _make_log_method(fn):
    @functools.wraps(fn)
    @classmethod
    def method(cls, *args, **kwargs):
        cls._log(fn, *args, **kwargs)

    return method


class LOG:
    """
    Usage:
        >>> LOG.debug('My message: %s', debug_str)
        13:12:43.673 - :<module>:1 - DEBUG - My message: hi
        >>> LOG('custom_name').debug('Another message')
        13:13:10.462 - custom_name - DEBUG - Another message
    """

    _custom_name = None
    handler = None
    level = None

    debug = _make_log_method(logging.Logger.debug)
    info = _make_log_method(logging.Logger.info)
    warning = _make_log_method(logging.Logger.warning)
    error = _make_log_method(logging.Logger.error)
    exception = _make_log_method(logging.Logger.exception)

    @classmethod
    def init(cls):
        """ Initializes the class, sets the default log level and creates
        the required handlers.
        """

        cls.level = logging.getLevelName('INFO')
        log_message_format = (
            '{asctime} | {levelname:8} | p:{process:5}, t:{threadName:8} | {name} | {message}'
        )

        formatter = logging.Formatter(log_message_format, style='{')
        formatter.default_msec_format = '%s.%03d'
        cls.handler = logging.StreamHandler(sys.stdout)
        cls.handler.setFormatter(formatter)

        # Enable logging in external modules
        cls.create_logger('').setLevel(cls.level)

    @classmethod
    def create_logger(cls, name):
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.addHandler(cls.handler)
        logger.setLevel(cls.level)
        return logger

    @classmethod
    def set_level(cls, level):
        cls.level = logging.getLevelName(level)

    def __init__(self, name):
        LOG._custom_name = name

    @classmethod
    def _log(cls, func, *args, **kwargs):
        if cls._custom_name is not None:
            name = cls._custom_name
            cls._custom_name = None
        else:
            # Stack:
            # [0] - _log()
            # [1] - debug(), info(), warning(), or error()
            # [2] - caller
            try:
                stack = inspect.stack()

                # Record:
                # [0] - frame object
                # [1] - filename
                # [2] - line number
                # [3] - function
                # ...
                record = stack[2]
                mod = inspect.getmodule(record[0])
                module_name = mod.__name__ if mod else ''
                name = module_name + ':' + record[3] + ':' + str(record[2])
            except Exception:
                name = 'default'

        func(cls.create_logger(name), *args, **kwargs)


LOG.init()

if __name__ == '__main__':
    LOG.set_level("DEBUG") # global setting
    LOG.debug("whatever you want to log")
