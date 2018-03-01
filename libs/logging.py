# Logging for TorSpider

import os
import sys
import logging
import configparser
from multiprocessing import current_process
from logging.handlers import TimedRotatingFileHandler

class Logger:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        loglevel = 'INFO'
        log_to_console = False
        try:
            config = configparser.ConfigParser()
            config.read('spider.cfg')
            log_to_console = config['TorSpider'].getboolean('LogToConsole')
            loglevel = config['LOGGING'].get('loglevel')
        except Exception as e:
            pass
        self.logger = self.__get_logger(loglevel, script_dir, log_to_console)

    @staticmethod
    def __get_logger(loglevel, script_dir, log_to_console):
        formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s")
        my_logger = logging.getLogger('TorSpider')
        os.makedirs(os.path.join(script_dir, 'logs'), exist_ok=True)
        filehandler = TimedRotatingFileHandler(
            os.path.join(script_dir, 'logs', 'TorSpider.log'),
            when='midnight', backupCount=7, interval=1)
        filehandler.setFormatter(formatter)
        my_logger.addHandler(filehandler)
        if log_to_console:
            consolehandler = logging.StreamHandler()
            consolehandler.setFormatter(formatter)
            my_logger.addHandler(consolehandler)
        my_logger.setLevel(logging.getLevelName(loglevel))
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        return my_logger


    def log(self, line, level):
        message = '{}: {}'.format(
            current_process().name,
            line)
        message = ' '.join(message.split())  # Remove unnecessary whitespace.
        if level.lower() == 'debug':
            self.logger.debug(message)
        elif level.lower() == 'info':
            self.logger.info(message)
        elif level.lower() == 'warning':
            self.logger.warning(message)
        elif level.lower() == 'error':
            self.logger.error(message)
        elif level.lower() == 'critical`':
            self.logger.critical(message)

logger = Logger()
