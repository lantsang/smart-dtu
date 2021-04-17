'''

File: bluestone_common.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import uos
import ure
import modem
import log
import _thread

log.basicConfig(level = log.INFO)
_common_log = log.getLogger("COMMON")

class BluestoneCommon(object):
    inst = None
    _network_state = 1
    _lock = _thread.allocate_lock()

    def __init__(self):
        BluestoneCommon.inst = self

    @staticmethod
    def get_network_state():
        return BluestoneCommon._network_state

    @staticmethod
    def set_network_state(state = 1):
        BluestoneCommon._lock.acquire()
        BluestoneCommon._network_state = state
        BluestoneCommon._lock.release()

    @staticmethod
    def get_imei():
        return modem.getDevImei()

    @staticmethod
    def get_sn():
        return modem.getDevSN()

    @staticmethod
    def check_file_exist(file_name):
        if not file_name:
            return False
        
        file_list = uos.listdir('usr')
        if file_name in file_list:
            return True
        else:
            return False

    @staticmethod
    def is_url(url):
        #pattern = ure.compile('http[s]://.+')
        return ure.match('https?://.+', url)

    @staticmethod
    def get_range(start, end, step = 1):
        result = []
        index = start
        while True:
            if start < end:
                if index <= end:
                    result.push(index)
                else:
                    break
                index = index + step
            else:
                if index >= end:
                    result.push(index)
                else:
                    break
                index = index - step
        return result
