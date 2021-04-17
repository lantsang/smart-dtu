'''

File: bluestone_daemon.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import dataCall
import checkNet
import utime
import ujson
import log
import _thread

from misc import Power
from usr import bluestone_config

log.basicConfig(level = log.INFO)
_daemon_log = log.getLogger("DAEMON")

class BlueStoneDaemon(object):
    inst = None

    def __init__(self):
        BlueStoneDaemon.inst = self

    def start(self):
        self.bs_config = bluestone_config.BluestoneConfig('config.json')
        
        #_thread.start_new_thread(self.check_network, ())