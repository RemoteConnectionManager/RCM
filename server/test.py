import dummy_rcm_server



import rcm_protocol_server

if __name__ == '__main__':


    print "testing rcm_protocol_server .................................."

    r=rcm_protocol_server.rcm_protocol(dummy_rcm_server)
    r.config('mia build platform ')

