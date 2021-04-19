'''

File: bluestone_mqtt_tencent.py

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
from TenCentYun import TXyun

from usr import bluestone_config
from usr import bluestone_common
from usr import bluestone_gpio
from usr import bluestone_pwm
from usr import bluestone_fota

log.basicConfig(level = log.INFO)
_mqtt_log = log.getLogger("MQTT_Tencent")

class BluestoneMqttTencent(object):
    inst = None

    def __init__(self, product_id, product_secret, sub_topic, pub_topic):
        BluestoneMqttTencent.inst = self

        self.bs_config = None
        self.bs_gpio = None
        self.bs_pwm = None
        self.bs_fota = None

        # 设备名称（参照接入腾讯云应用开发指导）
        self.device_name = bluestone_common.BluestoneCommon.get_sn()

        # 产品标识（参照接入腾讯云应用开发指导）
        self.product_id = product_id

        # 产品密钥（一机一密认证此参数传入None，参照接入腾讯云应用开发指导）
        self.product_secret = product_secret

        self.subscribe_topic = "{}/{}/{}".format(self.product_id, self.device_name, sub_topic)
        self.publish_topic = "{}/{}/{}".format(self.product_id, self.device_name, pub_topic)
        
        _mqtt_log.info("Start a new mqtt client, product id:{}, device name:{}, subscribe topic is {}, publish topic is {}".format(self.product_id, self.device_name, self.subscribe_topic, self.publish_topic))

        self.client = None
        self._is_sub_callback_running = False
        self._is_message_published = False

    def init(self):
        self.bs_config = bluestone_config.BluestoneConfig('bluestone_config.json')
        self.bs_data_config = bluestone_config.BluestoneConfig('bluestone_data.json')
        self.bs_gpio = bluestone_gpio.BluestoneGPIO()
        self.bs_pwm = bluestone_pwm.BluestonePWM()
        self.bs_fota = bluestone_fota.BluestoneFOTA()

        # 创建一个MQTT实例
        self.client = TXyun(self.product_id, self.device_name, None, self.product_secret)
        _mqtt_log.info("The mqtt client is started")

        self.client.setMqtt()  # 设置mqtt
        self.client.setCallback(self._sub_callback) # 设置消息回调
        self.client.subscribe(self.subscribe_topic) # 订阅主题
        self.client.start()

    def _update_gpio_status(self, io_level_list):
        try:
            self.bs_data_config.update_config('gpio', io_level_list)

            message = {}
            message['gpio'] = io_level_list
            _mqtt_log.info("Data configuration is {}".format(message))
            self.publish(message)
        except Exception as err:
            _mqtt_log.error("Cannot update gpio level list, the error is {}".format(err))

    def _handle_callback(self, key, config):
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
            elif key == 'fota':
                mode = self.bs_config.get_int_value(config, "mode")
                if mode == 0:
                    url_list = self.bs_config.get_value(config, "url")
                    self.bs_fota.start_fota_app(url_list)
                elif mode == 1:
                    url = self.bs_config.get_value(config, "url")
                    self.bs_fota.start_fota_firmware(url)
        except Exception as err:
            _mqtt_log.error(err)

    def _sub_callback_internal(self, topic, msg):
        try:
            message = msg.decode()
            _mqtt_log.info("Subscribe received, topic={}, message={}".format(topic.decode(), message))
            restart = False

            config_setting = ujson.loads(message)
            config_keys = config_setting.keys()
            for key in config_setting:
                config = config_setting[key]
                exist = self.bs_config.check_key_exist(key)
                if exist:
                    self.bs_config.update_config(key, config)
                    self.bs_data_config.update_config(key, config)
                    restart = self.bs_config.mqtt_check_key_restart(key)
                if restart:
                    restart = False
                    _mqtt_log.info("New configuration was received from mqtt, restarting system to take effect")
                    Power.powerRestart()
                else:
                    self._handle_callback(key, config)
        except Exception as err:
	        _mqtt_log.error(err)
        finally:
            self._is_sub_callback_running = False

    # 云端消息响应回调函数
    def _sub_callback(self, topic, msg):
        if self._is_sub_callback_running:
            _mqtt_log.error("Subscribe callback function is running, skipping the new request")
            return

        self._is_sub_callback_running = True
        _thread.start_new_thread(self._sub_callback_internal, (topic, msg))

    def _mqtt_publish(self, message):
        if self.client is not None:
            self.client.publish(self.publish_topic, message)
            self._is_message_published = True;
            _mqtt_log.info("Publish topic is {}, message is {}".format(self.publish_topic, message))

    def is_message_published(self):
        return self._is_message_published

    def publish(self, message):
        network_state = bluestone_common.BluestoneCommon.get_network_state()
        if network_state != 1:
            _mqtt_log.error("Cannot publish mqtt message, the network state is {}".format(network_state))
            return

        self._is_message_published = False
        _thread.start_new_thread(self._mqtt_publish, ([ujson.dumps(message)]))

    def connect(self):
        if self.client is not None:
            self.client.start()
            _mqtt_log.info("MQTT connected")

    def disconnect(self):
        if self.client is not None:
            self.client.disconnect()
            _mqtt_log.info("MQTT disconnected")

    def close(self):
        self.disconnect()
        self.client = None
        _mqtt_log.info("MQTT closed")

        

    