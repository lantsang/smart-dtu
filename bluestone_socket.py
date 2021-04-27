'''

File: bluestone_socket.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import utime
import ujson
import log
import _thread
import usocket

from misc import Power
from usr import bluestone_config
from usr import bluestone_common

log.basicConfig(level = log.INFO)
_socket_log = log.getLogger("SOCKET")

class BluestoneSocket(object):
    inst = None

    def __init__(self, protocol, ip, port):
        BluestoneSocket.inst = self

        self.client = None
        self._init_client(protocol, ip, port)
    
    def _init_client(self, protocol, ip, port):
        if protocol == 'tcp':
            self.client = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        elif protocol == 'udp':
            self.client = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)

        socket_addr = (ip, port)
        self.client.connect(socket_addr)
        self.client.setblocking(True)

    def change_ip(self, protocol, ip, port):
        if self.client is not None:
            self.client.close()

        self.init_client(protocol, ip, port)

    def send_data(self, data):
        if not self.client:
            _socket_log.error("The socket client is none, please use it after initialization")
            return
        try:
            self.client.send(data)
            _socket_log.info('Send {} bytes to server'.format(len(data)))
        except Exception as err:
            _socket_log.error("Cannot send data by socket, the error is {}".format(err))

    def receive_data(self):
        try:
            data = self.client.recv(1024)
            _socket_log.info('Receive {} bytes'.format(len(data)))
            _socket_log.info(data.decode())
        except Exception as err:
            _socket_log.error("Cannot receive data from socket, the error is {}".format(err))
    
    def start_send_thread(self, data):
        _thread.start_new_thread(self.send_data, (data))
        
    def close(self):
        if self.client:
            self.client.close()
            _socket_log.info("The socket was closed")
            self.client = None