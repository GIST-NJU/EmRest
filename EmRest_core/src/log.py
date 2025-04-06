import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler


def time_count(logger: logging.Logger = None):
    def decorate(func):
        def inner(*args, **kwargs):
            time_start = time.time()
            result = func(*args, **kwargs)
            time_end = time.time()
            if logger:
                logger.debug(f"Function:{func.__name__}, Cost Time: {time_end - time_start}s")
            else:
                logging.getLogger().debug(f"Function:{func.__name__}:Cost Time: {time_end - time_start}s")
            return result

        return inner

    return decorate


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(exp_name: str, log_dir: str, level: int = logging.DEBUG):
    log_name = f"{exp_name}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_path = os.path.join(log_dir, log_name)
    os.makedirs(log_dir, exist_ok=True)
    # create logger
    logging.root.setLevel(level)

    # create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = RotatingFileHandler(log_path, maxBytes=100 * 1024 * 1024, backupCount=5)

    # create formatter
    formatter = logging.Formatter(fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                                  datefmt='%H:%M:%S')
    # formatter = CustomFormatter()

    # set formatter
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # add handlers to the logger
    logging.root.addHandler(console_handler)
    logging.root.addHandler(file_handler)

    # Disable logging of third-party libraries (e.g. 'requests' library)
    logging.getLogger('requests').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('openapi_parser').setLevel(logging.INFO)
    logging.getLogger('chardet').setLevel(logging.INFO)

    return logging.root
