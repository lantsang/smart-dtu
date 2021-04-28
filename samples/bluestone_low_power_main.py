'''

File: bluestone_low_power_main.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import utime
import ujson
import log
import dataCall
import net
import modem
import checkNet
import _thread
import pm

from misc import Power
from machine import UART
from machine import Timer
from machine import WDT

from usr import bluestone_config
from usr import bluestone_common
from usr import bluestone_uart
from usr import bluestone_mqtt_tencent

'''
下面两个全局变量是必须有的，用户可以根据自己的实际项目修改下面两个全局变量的值，
在执行用户代码前，会先打印这两个变量的值。
'''
PROJECT_NAME = "Bluestone low power sample"
PROJECT_VERSION = "1.0.0"
checknet = checkNet.CheckNetwork(PROJECT_NAME, PROJECT_VERSION)

# 设置日志输出级别
log.basicConfig(level = log.INFO)
system_log = log.getLogger("MAIN")

timer0 = None
wdt = None
low_power_lock = None

bs_config = None
bs_data_config = None
bs_uart = None
bs_mqtt = None

def init_one_uart(config, name):
    global bs_config, bs_uart

    uart_config = bs_config.read_config_by_name(config, name)
    if uart_config is None:
        uart_config = ujson.loads('{"baud_rate":115200,"data_bits":8,"parity":0,"stop_bits":1,"flow_control":0}')
        bs_config.update_config(name, uart_config)
    bs_uart.start(name, uart_config)

def init_uart(config):
    global bs_uart, bs_mqtt
    
    bs_uart = bluestone_uart.BlueStoneUart(bs_mqtt)

    init_one_uart(config, 'uart0')
    init_one_uart(config, 'uart1')
    init_one_uart(config, 'uart2')

def init_mqtt_tencent(config):
    global bs_config, bs_mqtt

    mqtt_config = bs_config.read_config_by_name(config, 'mqtt_tencent')
    if mqtt_config is None:
        system_log.error("Cannot start mqtt proxy, please check the configuration for tencent mqtt")
        return
    
    try:
        bs_mqtt = bluestone_mqtt_tencent.BluestoneMqttTencent(mqtt_config["product_id"], mqtt_config["product_secret"], mqtt_config["sub_topic"], mqtt_config["pub_topic"])
        bs_mqtt.init()

        send_device_info()
    except Exception as err:
        system_log.error("Cannot start mqtt proxy, the error is {}".format(err))

def send_device_info():
    global bs_mqtt, bs_data_config

    start_modem()

    data_config = bs_data_config.read_config()
    message = ujson.loads(data_config)
    system_log.info("Device configuration is {}".format(message))
    bs_mqtt.publish(message)

def start_modem():
    global bs_data_config
    
    try:
        system_log.info("Start to read modem info")

        modem_info = {}
        modem_info["imei"] = modem.getDevImei()
        modem_info["devModel"] = modem.getDevModel()
        modem_info["sn"] = modem.getDevSN()
        modem_info["fwVersion"] = modem.getDevFwVersion()
        modem_info["productId"] = modem.getDevProductId()
        
        bs_data_config.update_config('modem', modem_info)
    except Exception as err:
        system_log.error("Cannot get modem info, the error is {}".format(err))

def feed_dog(args):
    global wdt

    system_log.info("Feeding dog...")
    wdt.feed()

def init_wdt():
    global timer0, wdt
    
    wdt = WDT(30)

    period = 5000
    system_log.info("Feeding dog service is running per {} millseconds".format(period))

    timer0 = Timer(Timer.Timer0)
    timer0.start(period = period, mode = timer0.PERIODIC, callback = feed_dog)

def init_low_power():
    global low_power_lock
    
    lock_name = "bluestone_low_power_lock"
    # 创建wakelock锁
    low_power_lock = pm.create_wakelock(lock_name, len(lock_name))
    # 设置自动休眠模式
    pm.autosleep(1)
    
def system_init():
    global bs_config, bs_data_config, bs_mqtt
    
    '''
    如果程序包含网络相关代码，必须执行wait_network_connected() 等待网络就绪（拨号成功）；
    '''
    #TODO: no need to check network connection each time
    system_log.info("Check network connection")
    checknet.wait_network_connected()

    if bs_config == None:
        system_log.info("Init system configuration file")
        bs_config = bluestone_config.BluestoneConfig('bluestone_config.json')
        config = bs_config.init_config()

    if bs_data_config == None:
        system_log.info("Init data configuration file")
        bs_data_config = bluestone_config.BluestoneConfig('bluestone_data.json')
        data_config = bs_data_config.init_config()

    if bs_mqtt == None:
        system_log.info("Init tencent mqtt service")
        init_mqtt_tencent(config)

if __name__ == '__main__':
    utime.sleep(5)
    checknet.poweron_print_once()
    
    system_log.info("Create low power wake lock")
    init_low_power()

    while True:
        system_log.info("Sleep for 60 seconds")
        utime.sleep(60)
        
        res = pm.wakelock_lock(low_power_lock)
        system_log.info("Get lock to weak up")
        
        system_init()
        send_device_info()
        
        # add this line to test the mA
        utime.sleep(60)
        
        res = pm.wakelock_unlock(low_power_lock)