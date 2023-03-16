import os
import errno
import logging
import datetime

def safe_makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def setup_logger(output_dir):
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s]%(message)s',
                                  datefmt=r'%Y-%m-%d %H:%M:%S')

    dt = datetime.datetime.now()
    log_file = '%04d_%02d_%02d__%02d%02d%02d.log' % (dt.year, dt.month, dt.day, dt.hour, dt.minute,
                                                     dt.second)

    file_handler = logging.FileHandler(os.path.join(output_dir, log_file))
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)
    return logger


def read_img(path):
    with open(path, "rb") as file:
        data = file.read()
        return data
