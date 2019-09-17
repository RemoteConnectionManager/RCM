from  logger_server import logger


class rcm_server(rcm_base_server.rcm_base_server):


    def get_queue(self): 
        logger.debug("get_queue")
        queueList = []
        queueList.append("visual")
        return queueList
