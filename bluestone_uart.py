'''

File: bluestone_uart.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import net
import utime
import ujson
import log
import _thread

from misc import Power
from machine import UART

from usr import bluestone_common
from usr import bluestone_config
from usr import bluestone_gpio
from usr import bluestone_pwm
from usr import bluestone_fota

log.basicConfig(level = log.INFO)
_uart_log = log.getLogger("UART")

class BlueStoneUart(object):
    inst = None

    def __init__(self, mqtt_client):
        BlueStoneUart.inst = self

        if mqtt_client:
            self.bs_mqtt = mqtt_client
        else:
            self.bs_mqtt = None
        self.bs_config = None
        self.bs_data_config = None
        self.bs_gpio = None
        self.bs_pwm = None
        self.bs_fota = None
        self.uart_config = {}
        self.uart_name_list = ['uart0', 'uart1', 'uart2']
        
        self._init()

    def _init(self):
        self.bs_config = bluestone_config.BluestoneConfig('bluestone_config.json')
        self.bs_data_config = bluestone_config.BluestoneConfig('bluestone_data.json')

    def send_message(self, name, payload):
        uart_name = "{}".format(name)
        message = {uart_name:{}}
        message[uart_name]["config"] = self.uart_config[uart_name]
        message[uart_name]["payload"] = payload

        _uart_log.info("Uart message is {}".format(message))
        if self.bs_mqtt:
            self.bs_mqtt.publish(message)

    def _update_gpio_status(self, io_level_list):
        self.bs_data_config.update_config('gpio', io_level_list)

    def _handle_cmd(self, key, config):
        try:
            if key == 'gpio':
                io_level_list = self.bs_gpio.read_all()
                io_name_list = self.bs_gpio.get_io_name_list()
                for gpio_key in config.keys():
                    if gpio_key not in io_name_list:
                        continue;
                    level = self.bs_config.get_int_value(config, gpio_key)
                    if level is not None:
                        id = self.bs_gpio.get_id_by_name(gpio_key)
                        self.bs_gpio.write(id, level)
                        io_level_list[gpio_key] = level
                self._update_gpio_status(io_level_list)
            elif key.startswith('pwm'):
                id = self.bs_pwm.get_id_by_name(key)
                is_breathe = self.bs_config.get_int_value(config, "breathe")
                frequency = self.bs_config.get_int_value(config, "frequency")
                duty = self.bs_config.get_float_value(config, "duty")
                if is_breathe:
                    self.bs_pwm.start_breathe(id, frequency)
                else:
                    self.bs_pwm.start_once(id, frequency, duty)
            elif key == 'system':
                modemFun = self.bs_config.get_int_value(config, "modemFun")
                if modemFun == 4:
                    bluestone_common.BluestoneCommon.set_network_state(modemFun)
                    _uart_log.info("Enter airplane mode")
                    net.setModemFun(modemFun)
                    utime.sleep_ms(2000)
                elif modemFun == 1:
                    _uart_log.info("Exit airplane mode")
                    net.setModemFun(modemFun)
                    utime.sleep_ms(2000)
            elif key == 'fota':
                mode = self.bs_config.get_int_value(config, "mode")
                if mode == 0:
                    url_list = self.bs_config.get_value(config, "url")
                    self.bs_fota.start_fota_app(url_list)
                elif mode == 1:
                    url = self.bs_config.get_value(config, "url")
                    self.bs_fota.start_fota_firmware(url)
        except Exception as err:
            _uart_log.error("Cannot handle command for uart, the error is {}".format(err))

    def _uart_read(self, name, uart):
        _uart_log.info("UART {} start with {}".format(name, uart))
        config = None
        loop = True
        restart = False
    
        while loop:
            num = uart.any()
            utime.sleep_ms(50)
            num2 = uart.any()
            if num != num2:
                continue

            if num:
                _uart_log.info("UART ready data length is {}".format(num))
                msg = uart.read(num)
                # 初始数据是字节类型（bytes）,将字节类型数据进行编码
                utf8_msg = msg.decode()
                _uart_log.info("UART read message is {}".format(utf8_msg))

                is_json = bluestone_common.BluestoneCommon.is_json(utf8_msg)
                if not is_json:
                    self.send_message(name, utf8_msg)
                    continue
                try:
                    config_setting = ujson.loads(utf8_msg)
                    config_keys = config_setting.keys()
                    if 'payload' in config_keys: # uart write payload, ignore it
                        continue
                    for key in config_setting:
                        config = config_setting[key]
                        exist = self.bs_config.check_key_exist(key)
                        if exist:
                            self.bs_config.update_config(key, config)
                        self._handle_cmd(key, config)
                    if name in config_keys:
                        config = config_setting[name] # 保证重启逻辑的数据正确性
                        loop = False
                        restart = False
                    else:
                        restart = self.bs_config.check_key_restart(key)
                        if restart:
                            loop = False
                    self.send_message(name, config_setting)
                except Exception as err:
	                _uart_log.error("Cannot handle read command for uart, the error is {}".format(err))
            else:
                continue
            utime.sleep_ms(300)

        if restart:
            restart = False
            _uart_log.info("New configuration was received from uart, restarting system to take effect")
            Power.powerRestart()
        else:
            self.restart_uart(name, config)
    
    def uart_read(self, name, config):
        uart = self.init_uart(name, config)
        self._uart_read(name, uart)
    
    def uart_write(self, name, payload):
        try:
            config_data = self.bs_config.read_config()
            config = ujson.loads(config_data)
            uart_config = self.bs_config.get_value(config, name)
            
            uart = self.init_uart(name, uart_config)
            uart.write(payload)
            utime.sleep_ms(1000)
            _uart_log.info("Write payload {} to {}".format(ujson.dumps(payload), name))
        except Exception as err:
            _uart_log.error("Cannot write payload to {}, the error is {}".format(name, err))
        
    def restart_uart(self, name, config):
        _uart_log.info("Try to close {}".format(name))
        uart.close()
        _uart_log.info("{} was closed".format(name))

        if name in self.uart_name_list:
            self.uart_read(name, config)
    
    def init_uart(self, name, config):
        _uart_log.info("Config is {}".format(config))

        port = 0
        if name == 'uart0':
            port = UART.UART0
        elif name == 'uart1':
            port = UART.UART1
        else:
            port = UART.UART2

        baud_rate = self.bs_config.get_int_value(config, "baud_rate")
        data_bits = self.bs_config.get_int_value(config, "data_bits")
        parity = self.bs_config.get_int_value(config, "parity")
        stop_bits = self.bs_config.get_int_value(config, "stop_bits")
        flow_control = self.bs_config.get_int_value(config, "flow_control")

        self.uart_config[name] = {"baud_rate":baud_rate, "data_bits":data_bits, "parity":parity, "stop_bits":stop_bits, "flow_control":flow_control}

        return UART(port, baud_rate, data_bits, parity, stop_bits, flow_control)

    def start(self, name, config):
        self.bs_gpio = bluestone_gpio.BluestoneGPIO()
        self.bs_pwm = bluestone_pwm.BluestonePWM()
        self.bs_fota = bluestone_fota.BluestoneFOTA()

        if name in self.uart_name_list:
            _thread.start_new_thread(self.uart_read, (name, config))