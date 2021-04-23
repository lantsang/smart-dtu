'''

File: bluestone_config.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import uos
import log
import ujson
import _thread

from usr import bluestone_common

log.basicConfig(level = log.INFO)
_config_log = log.getLogger("CONFIG")

class BluestoneConfig(object):
    inst = None

    def __init__(self, file_name):
        self.lock = _thread.allocate_lock()

        self.config_file_name = file_name
        self.config_path = 'usr:/{}'.format(self.config_file_name)
        self.restart_key_list = ['mqtt_tencent', 'socket', 'timer0', 'timer1', 'timer2', 'timer3']
        self.key_list = ['uart0', 'uart1', 'uart2', 'mqtt_tencent', 'socket', 'timer0', 'timer1', 'timer2', 'timer3', 'gpio']
        BluestoneConfig.inst = self

    def check_key_restart(self, key):
        if key is None:
            return False
        if key in self.restart_key_list:
            return True
        return False

    def check_key_exist(self, key):
        if key is None:
            return False
        if key in self.key_list:
            return True
        return False

    def get_value(self, config, key):
        if (config is None) or (key is None):
            return None
        keys = config.keys()
        if keys is None:
            return None
        if key in keys:
            return config[key]
        return None

    def get_int_value(self, config, key):
        value = self.get_value(config, key)
        if value is not None:
            return int(config[key])
        return 0

    def get_float_value(self, config, key):
        value = self.get_value(config, key)
        if value is not None:
            return float(config[key])
        return 0.0

    def init_config(self):
        config = None

        exist = bluestone_common.BluestoneCommon.check_file_exist(self.config_file_name)
        if exist:
            config = self.read_config()
            _config_log.info("Read config from {}, the content is {}".format(self.config_path, config))
        else:
            self.create_config()
            _config_log.info("Config {} does not exist, creating a new one".format(self.config_path))
    
        return config

    def create_config(self):
        path = self.config_path.replace(':', '')

        self.lock.acquire()
        with open(path, 'w') as f:
            f.write("{}")
        self.lock.release()

    def read_config(self):
        path = self.config_path.replace(':', '')
        content = None

        self.lock.acquire()
        with open(path) as f:
            content = f.read()
        self.lock.release()

        return content

    def read_config_by_name(self, config, name):
        if config is None:
            config = '{}'
        current_config = None
        system_config = ujson.loads(config)
        if name in system_config.keys():
            current_config = system_config[name]
        return current_config

    def update_config(self, name, params):
        path = self.config_path
        path = path.replace(':', '')

        content = self.read_config()
        config = ujson.loads(content)

        self.write_config(config, name, params)

    def write_config(self, config, name, params):
        if config == None:
            config = {}
        config[name] = params

        path = self.config_path.replace(':', '')
        new_config = ujson.dumps(config)

        self.lock.acquire()
        with open(path, 'w') as f:
            _config_log.info("New config is {}".format(new_config))
            f.write(new_config)
        self.lock.release()
        