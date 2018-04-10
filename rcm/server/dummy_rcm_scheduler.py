import logging

def get_queue(self): 
    logger = logging.getLogger("basic")    
    logger.debug("get_queue")
    queueList = []
    queueList.append("visual")
    return queueList
