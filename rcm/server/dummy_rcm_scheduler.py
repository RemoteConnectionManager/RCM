from  logger_server import logger

def get_queue(self):
    logger.debug("get_queue")
    queueList = []
    queueList.append("visual")
    return queueList
