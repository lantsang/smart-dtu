'''

File: bluestone_mqtt.py

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
from umqtt import MQTTClient

from usr import bluestone_config
from usr import bluestone_common
from usr import bluestone_gpio
from usr import bluestone_pwm
from usr import bluestone_fota

log.basicConfig(level = log.INFO)
_mqtt_log = log.getLogger("MQTT")

class BluestoneMqtt(object):
    inst = None

    def __init__(self, client_id, server, port, user, password, sub_topic, pub_topic):
        BluestoneMqtt.inst = self

        self.bs_config = None
        self.bs_gpio = None
        self.bs_pwm = None
        self.bs_fota = None

        self.sn = bluestone_common.BluestoneCommon.get_sn()
        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.password = password

        self.subscribe_topic = sub_topic
        self.publish_topic = pub_topic
        
        self.client = None
        self._is_sub_callback_running = False
        self._is_message_published = False

    def _init_mqtt(self):
        self.bs_config = bluestone_config.BluestoneConfig('bluestone_config.json')
        self.bs_data_config = bluestone_config.BluestoneConfig('bluestone_data.json')
        self.bs_gpio = bluestone_gpio.BluestoneGPIO()
        self.bs_pwm = bluestone_pwm.BluestonePWM()
        self.bs_fota = bluestone_fota.BluestoneFOTA()

        # 创建一个MQTT实例
        self.client = MQTTClient(
            client_id = self.client_id,
            server = self.server,
            port = self.port,
            user = self.user,
            password = self.password,
            keepalive = 30)
        _mqtt_log.info("Start a new mqtt client, id:{}, server:{}, port:{}".format(self.client_id, self.server, self.port))

        self.client.set_callback(self._sub_callback) # 设置消息回调
        self.client.connect() # 建立连接

        #sub_topic = self.subscribe_topic.format(self.sn)
        _mqtt_log.info("Subscribe topic is {}".format(self.subscribe_topic))
        self.client.subscribe(self.subscribe_topic) # 订阅主题

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
                    if not restart:
                        restart = self.bs_config.mqtt_check_key_restart(key)
                self._handle_callback(key, config)
            if restart:
                restart = False
                _mqtt_log.info("New configuration was received from mqtt, restarting system to take effect")
                Power.powerRestart()  
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
        #pub_topic = self.publish_topic.format(self.sn)
        #message = {"Config":{},"message":"MQTT hello from Bluestone"}
        
        if self.client is not None:
            self.client.publish(self.publish_topic, message)
            self._is_message_published = True;
            _mqtt_log.info("Publish topic is {}, message is {}".format(self.publish_topic, message))

    def _wait_msg(self):
        while True:
            if self.client is not None:
                self.client.wait_msg()
            utime.sleep_ms(300)

    def is_message_published(self):
        return self._is_message_published
        
    def start(self):
        self._init_mqtt()

        _thread.start_new_thread(self._wait_msg, ())

    def publish(self, message):
        network_state = bluestone_common.BluestoneCommon.get_network_state()
        if network_state != 1:
            _mqtt_log.error("Cannot publish mqtt message, the network state is {}".format(network_state))
            return

        #_mqtt_log.info("Publish message is {}".format(message))
        #self._mqtt_publish(ujson.dumps(message))
        self._is_message_published = False
        _thread.start_new_thread(self._mqtt_publish, ([ujson.dumps(message)]))

    def connect(self):
        if self.client is not None:
            self.client.connect()
            _mqtt_log.info("MQTT connected")

    def disconnect(self):
        if self.client is not None:
            self.client.disconnect()
            _mqtt_log.info("MQTT disconnected")

    def close(self):
        self.disconnect()
        self.client = None
        _mqtt_log.info("MQTT closed")

        

    