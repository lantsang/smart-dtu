'''

File: bluestone_temperature.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import log

from machine import I2C

import utime as time

"""

1. calibration

2. Trigger measurement

3. read data

"""

# API 手册 http://qpy.quectel.com/wiki/#/zh-cn/api/?id=i2c
# AHT10 说明书
# https://server4.eca.ir/eshop/AHT10/Aosong_AHT10_en_draft_0c.pdf

log.basicConfig(level = log.INFO)
_i2c_log = log.getLogger("AHT10")

class BluestoneTemperature(object):
    inst = None

    def __init__(self):
        BluestoneTemperature.inst = self

        self.i2c_dev = None
        self.i2c_addr = None

        # Initialization command
        self.AHT10_CALIBRATION_CMD = 0xE1

        # Trigger measurement
        self.AHT10_START_MEASURMENT_CMD = 0xAC

        # reset
        self.AHT10_RESET_CMD = 0xBA

    def aht10_init(self, addr=0x38):
        self.i2c_dev = I2C(I2C.I2C1, I2C.STANDARD_MODE) # 返回i2c对象
        self.i2c_addr = addr
        self._sensor_init()
        pass

    def _sensor_init(self):
        # calibration
        self._write_data([self.AHT10_CALIBRATION_CMD, 0x08, 0x00])
        time.sleep_ms(300) # at last 300ms
        pass

    def _ath10_reset(self):
        self._write_data([self.AHT10_RESET_CMD])
        time.sleep_ms(20) # at last 20ms

    def _write_data(self, data):
        self.i2c_dev.write(self.i2c_addr, bytearray(0x00), 0, bytearray(data), len(data))
        pass

    def _read_data(self, length):
        r_data = [0x00 for i in range(length)]
        r_data = bytearray(r_data)
        self.i2c_dev.read(self.i2c_addr, bytearray(0x00), 0, r_data, length, 0)
        return list(r_data)

    def _aht10_transformation_temperature(self, data):
        r_data = data

        # 根据数据手册的描述来转化温度
        humidity = (r_data[0] << 12) | (r_data[1] << 4) | ((r_data[2] & 0xF0) >> 4)
        humidity = (humidity/(1 << 20)) * 100.0
        _i2c_log.info("Current humidity is {}%".format(humidity))

        temperature = ((r_data[2] & 0xf) << 16) | (r_data[3] << 8) | r_data[4]
        temperature = (temperature * 200.0 / (1 << 20)) - 50
        _i2c_log.info("Current temperature is {}°C".format(temperature))

        return (temperature, humidity)

    def start_measure(self):
        # Trigger data conversion
        self._write_data([self.AHT10_START_MEASURMENT_CMD, 0x33, 0x00])
        time.sleep_ms(200) # at last delay 75ms

        # check has success
        r_data = self._read_data(6)

        # check bit7
        if (r_data[0] >> 7) != 0x0:
            _i2c_log.info("Conversion has error")
        else:
            return self._aht10_transformation_temperature(r_data[1:6])