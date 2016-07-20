import logging
import logging.handlers
import os

logging.IMPORTANT = 25
logging.addLevelName(logging.IMPORTANT, "IMPORTANT")
logging.Logger.important = lambda inst, msg, *args, **kwargs: inst.log(logging.IMPORTANT, msg, *args, **kwargs)
logging.important = lambda msg, *args, **kwargs: logging.log(logging.IMPORTANT, msg, *args, **kwargs)

#Setup log file name and log levels
log_file_name = "testLogFile.log"
log_level_console = logging.IMPORTANT
log_level_file = logging.DEBUG

#Create the logger
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)

#Define the log formats
formatter_file=logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
formatter_console=logging.Formatter('%(message)s')

#Create the handler for the file
##logger_file=logging.FileHandler(log_file_name)
logger_file=logging.handlers.TimedRotatingFileHandler(log_file_name,when='S', interval = 5, backupCount=0)
logger_file.setLevel(log_level_file)
logger_file.setFormatter(formatter_file)
logger.addHandler(logger_file)

#Create the handler for the console
logger_console=logging.StreamHandler()
logger_console.setLevel(log_level_console)
logger_console.setFormatter(formatter_console)
logger.addHandler(logger_console)


sn=4

logging.important("Serial Number: %d",sn)
logging.debug("Test output 1")
logging.info("Test output 2")
logging.warning("Test output 3")


logging.shutdown()




