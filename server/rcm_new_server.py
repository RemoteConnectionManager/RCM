import rcm_server



import rcm_protocol_server
import rcm_protocol_parser

if __name__ == '__main__':
    r=rcm_protocol_server.rcm_protocol(rcm_server)
    c=rcm_protocol_parser.CommandParser(r)
    c.handle()

