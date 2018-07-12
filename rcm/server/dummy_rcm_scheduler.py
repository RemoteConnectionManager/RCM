import logging

import rcm_base_server

class rcm_server(rcm_base_server.rcm_base_server):


    def get_queue(self): 
        logger = logging.getLogger("basic")    
        logger.debug("get_queue")
        queueList = []
        queueList.append("visual")
        return queueList
