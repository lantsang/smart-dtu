'''

File: bluestone_timer.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import log
import utime
import ujson
from machine import Timer

log.basicConfig(level = log.INFO)
_timer_log = log.getLogger("TIMER")

class BluestoneTimer(object):
    inst = None

    def __init__(self):
        BluestoneTimer.inst = self
        self._avaliable_timer_list = [Timer.Timer0, Timer.Timer1, Timer.Timer2, Timer.Timer3]

    def timer_test_callback(self, args):
        _timer_log.info("Oha, timer callback is comming, {}".format(args))
         
    def start(self, id, period, mode, callback_func):
        if id not in self._avaliable_timer_list:
            _timer_log.info("Cannot start a new timer, the timer id {} is invalid".format(id))
            return

        if period is None:
            period = 1000
        if mode is None:
            mode = Timer.PERIODIC

        timer = Timer(id)
        timer.start(period = period, mode = mode, callback = callback_func)
        _timer_log.info("Start a new timer, id={}, period={}, mode={}".format(id, period, mode))

    def stop(self, id):
        if id not in self._avaliable_timer_list:
            _timer_log.info("Cannot stop a timer, the timer id {} is invalid".format(id))
            return
        
        timer = Timer(id)
        timer.stop()
        _timer_log.info("Timer {} was stopped".format(id))

    def stop_all(self):
        for id in self._avaliable_timer_list:
            self.stop(id)


