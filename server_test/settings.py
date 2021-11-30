import logging
import time
import logging.handlers
import os


# ----------- log 정보들 -----------------
class LoggerAdapter(logging.LoggerAdapter):
    def __init__(self, prefix, logger):
        super(LoggerAdapter, self).__init__(logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        return '[%s] %s' % (self.prefix, msg), kwargs


LOG_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "logs")
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

stream_hander = logging.StreamHandler()
stream_hander.setFormatter(formatter)
logger.addHandler(stream_hander)

# file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'server.log'))
# 50M 파일 한개
file_max_byte = 1024 * 1024 * 50
now = time.localtime()
file_handler = logging.handlers.RotatingFileHandler(os.path.join(LOG_DIR, '%04d_%02d_%02d_server.log' %
                                                                 (now.tm_year, now.tm_mon, now.tm_mday)),
                                                    maxBytes=file_max_byte, backupCount=20)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 로거에서 고정적으로 넣을 문구 작성
logger = LoggerAdapter("TEST", logger)

"""
더 많은 셋팅들 값이 생긴 다면 여기다가 작성
"""
