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

    def send_data(self):
        message = 'GET  /News  HTTP/1.1\r\nHost:  www.tongxinmao.com\r\nAccept-Encoding:deflate\r\nConnection: keep-alive\r\n\r\n'
        
        ret = self.client.send(message.encode("utf8"))
        _socket_log.info('Send %d bytes' % ret)

        # 接收服务端消息
        data = self.client.recv(1024)
        _socket_log.info('Receive %d bytes' % len(data))
        _socket_log.info(data.decode())

        self.client.close() #关闭连接

    def start(self):
        _thread.start_new_thread(self.send_data, ())