'''

File: bluestone_gpio.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import utime
import log
from machine import Pin

log.basicConfig(level = log.INFO)
_gpio_log = log.getLogger("GPIO")

class BluestoneGPIO(object):
    inst = None

    def __init__(self):
        BluestoneGPIO.inst = self

        # 注：EC600S只有GPIO81(gpio7),GPIO77(gpio6)和GPIO78(gpio5)三个引脚可用，其他的引脚未引出，暂不可用
        self.io_name_list = ["gpio1", "gpio2", "gpio3", "gpio4", "gpio5", "gpio6", "gpio7", "gpio8", "gpio9", "gpio10", "gpio11", "gpio12", "gpio13", "gpio14"]
        self.io_list = [Pin.GPIO1, Pin.GPIO2, Pin.GPIO3, Pin.GPIO4, Pin.GPIO5, Pin.GPIO6, Pin.GPIO7, Pin.GPIO8, Pin.GPIO9, Pin.GPIO10, Pin.GPIO11, Pin.GPIO12, Pin.GPIO13, Pin.GPIO14]
    
    def get_id_by_name(self, name):
        index = self.io_name_list.index(name)
        return self.io_list[index]

    def get_io_name_list(self):
        return self.io_name_list

    def get_io_list(self):
        return self.io_list

    def read(self, port):
        if port not in self.io_list:
            _gpio_log.info("Port {} does not exist".format(port))
            return 0
        
        pin = Pin(port, Pin.IN, Pin.PULL_PD, 0)
        level = pin.read()
        _gpio_log.info("Port {}'s level is {}".format(port, level))
        return level
    
    def read_all(self):
        level_list = {}

        for io_name in self.io_name_list:
            port_name = self.get_id_by_name(io_name)
            level = self.read(port_name)
            level_list[io_name] = level
        
        return level_list
    
    '''
    port:int, 模组编号
    direction:int, IN-输入模式， OUT-输出模式
    pull_mode:int, PULL_DISABLE-浮空模式，PULL_PU-上拉模式， PULL_PD-下拉模式
    level:int, 0-设置引脚为低电平， 1-设置引脚为高电平
    '''
    def read_extension(self, port, direction, pull_mode, level):
        if port not in self.io_list:
            _gpio_log.info("Port {} does not exist".format(port))
            return 0

        pin = Pin(port, direction, pull_mode, level)
        level = pin.read()
        _gpio_log.info("Port {}'s level is {}".format(port, level))
        return level

    def write(self, port, level):
        if port not in self.io_list:
            _gpio_log.info("Port {} does not exist".format(port))
            return 0

        pin = Pin(port, Pin.OUT, Pin.PULL_DISABLE, 0)
        if level:
            _gpio_log.info("Write 1 to port {}".format(port))
            pin.write(1)
        else:
            _gpio_log.info("Write 0 to port {}".format(port))
            pin.write(0)

    '''
    port:int, 模组编号
    direction:int, IN-输入模式， OUT-输出模式
    pull_mode:int, PULL_DISABLE-浮空模式，PULL_PU-上拉模式， PULL_PD-下拉模式
    level:int, 0-设置引脚为低电平， 1-设置引脚为高电平
    '''
    def write_extension(self, port, direction, pull_mode, level):
        if port not in self.io_list:
            _gpio_log.info("Port {} does not exist".format(port))
            return 0
        
        pin = Pin(port, direction, pull_mode, level)
        if level:
            _gpio_log.info("Write 1 to port {}".format(port))
            pin.write(1)
        else:
            _gpio_log.info("Write 0 to port {}".format(port))
            pin.write(0)