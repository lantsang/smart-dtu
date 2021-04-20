'''

File: bluestone_main.py

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
import ntptime
import _thread

from misc import Power
from machine import UART
from machine import Timer
from machine import WDT

from usr import bluestone_config
from usr import bluestone_common
from usr import bluestone_uart
from usr import bluestone_gpio
from usr import bluestone_mqtt
from usr import bluestone_mqtt_tencent
from usr import bluestone_socket
from usr import bluestone_temperature
from usr import bluestone_timer

'''
下面两个全局变量是必须有的，用户可以根据自己的实际项目修改下面两个全局变量的值，
在执行用户代码前，会先打印这两个变量的值。
'''
PROJECT_NAME = "Bluestone smart DTU"
PROJECT_VERSION = "1.0.0"
checknet = checkNet.CheckNetwork(PROJECT_NAME, PROJECT_VERSION)

# 设置日志输出级别
log.basicConfig(level = log.INFO)
system_log = log.getLogger("MAIN")

state = 1
retry_count = 0
timer0 = None
wdt = None
bs_config = None
bs_data_config = None
bs_uart = None
bs_mqtt = None
bs_aht10 = None
bs_gpio = None
bs_timer = None
bs_fota = None

timer_name_list = ["timer0", "timer1", "timer2", "timer3"]
timer_list = [Timer.Timer0, Timer.Timer1, Timer.Timer2, Timer.Timer3]
timer_job_name_list = []
is_timer_job_running = False

def init_one_uart(config, name):
    global bs_uart

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

def init_mqtt(config):
    global bs_mqtt

    mqtt_config = bs_config.read_config_by_name(config, 'mqtt')
    if mqtt_config is None:
        mqtt_config = {"client_id":"E3N2EXDG5Xbluestone001", "server":"E3N2EXDG5Xbluestone001.iotcloud.tencentdevices.com","port":1883,"user":"E3N2EXDG5Xbluestone001;12010126;0OSIF;1653152124","pwd":"a70277555e5190b6f6307ca373e3b434e0330841e80047b74c547312df704e9e;hmacsha256","sub_topic":"E3N2EXDG5X/bluestone001/control","pub_topic":"E3N2EXDG5X/bluestone001/event"}
        bs_config.update_config("mqtt", mqtt_config)
    
    try:
        #mqtt_config["client_id"] = "Bluestone_{}".format(bluestone_common.BluestoneCommon.get_sn())
        bs_mqtt = bluestone_mqtt.BluestoneMqtt(mqtt_config["client_id"], mqtt_config["server"], int(mqtt_config["port"]), mqtt_config["user"], mqtt_config["pwd"], mqtt_config["sub_topic"], mqtt_config["pub_topic"])
        bs_mqtt.start()

        send_device_info()
    except Exception as err:
        system_log.error("Cannot start mqtt proxy, the client_id is {}, please check the configuration".format(mqtt_config["client_id"]))

def init_mqtt_tencent(config):
    global bs_mqtt

    mqtt_config = bs_config.read_config_by_name(config, 'mqtt_tencent')
    if mqtt_config is None:
        system_log.error("Cannot start mqtt proxy, please check the configuration for tencent mqtt")
        return
        # mqtt_config = {"product_id":"FKL718DQJZ", "product_secret":"6c5fdda634b6b54a10d6a70fd22db067","sub_topic":"control","pub_topic":"event"}
        # bs_config.update_config("mqtt_tencent", mqtt_config)
    
    try:
        #mqtt_config["client_id"] = "Bluestone_{}".format(bluestone_common.BluestoneCommon.get_sn())
        bs_mqtt = bluestone_mqtt_tencent.BluestoneMqttTencent(mqtt_config["product_id"], mqtt_config["product_secret"], mqtt_config["sub_topic"], mqtt_config["pub_topic"])
        bs_mqtt.init()

        send_device_info()
    except Exception as err:
        system_log.error("Cannot start mqtt proxy, the error is {}, please check the configuration".format(err))

def init_socket(config):
    socket_config = bs_config.read_config_by_name(config, 'socket')
    if socket_config is None:
        socket_config = {"protocol":"tcp","server":"www.tongxinmao.com","port":80}
        bs_config.update_config('socket', socket_config)
    bs_socket = bluestone_socket.BluestoneSocket(socket_config["protocol"], socket_config["server"], socket_config["port"])
    bs_socket.start()

def send_device_info():
    global bs_mqtt

    # 同步ntp时间
    ntptime.settime()

    start_modem()
    start_aht10()
    start_gpio()

    data_config = bs_data_config.read_config()
    message = ujson.loads(data_config)
    system_log.info("Device configuration is {}".format(message))
    bs_mqtt.publish(message)

def start_modem():
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

def start_aht10():
    global bs_aht10

    try:
        system_log.info("Start to read temperature and humidity, the time is {}".format(utime.localtime()))

        (temperature, humidity) = bs_aht10.start_measure()
        message = {"temperature":{},"humidity":{}}
        message["temperature"] = temperature
        message["humidity"] = humidity

        system_log.info("The temperature and humidity data has been read, the time is {}".format(utime.localtime()))
        
        bs_data_config.update_config('aht10', message)
    except Exception as err:
        system_log.error("Cannot get temperature and humidity, the error is {}".format(err))

def start_gpio():
    global bs_gpio

    try:
        system_log.info("Start to read gpio level list")
        io_level_list = bs_gpio.read_all()
        bs_data_config.update_config('gpio', io_level_list)
    except Exception as err:
        system_log.error("Cannot get gpio level list, the error is {}".format(err))

def start_one_job(args):
    global timer_job_name_list, bs_mqtt, bs_data_config, is_timer_job_running

    if is_timer_job_running:
        system_log.error("The timer job is running, skipping the new one")
        return
    
    is_timer_job_running = True

    if "aht10" in timer_job_name_list:
        start_aht10();
    if "gpio" in timer_job_name_list:
        start_gpio()
    
    data_config = bs_data_config.read_config()
    message = ujson.loads(data_config)
    system_log.info("Data configuration is {}".format(message))
    bs_mqtt.publish(message)

    while True:
        is_message_published = bs_mqtt.is_message_published()
        if is_message_published:
            break
        utime.sleep_ms(300)
        
    is_timer_job_running = False

def start_timer_job(timer_id, period, mode, func_name):
    global bs_timer

    bs_timer.start(timer_id, period, mode, start_one_job)

def stop_timer_job(timer_id):
    global bs_timer

    bs_timer.stop(timer_id)

def get_timer_by_name(name):
    index = timer_name_list.index(name)
    return timer_list[index]

def check_timer(config, timer_name):
    global timer_job_name_list

    timer_config = bs_config.read_config_by_name(config, timer_name)
    system_log.info("Timer {}'s config is {}".format(timer_name, ujson.dumps(timer_config)))
    if timer_config is not None:
        bs_config.update_config(timer_name, timer_config)
        job_status = bs_config.get_int_value(timer_config, "status")
        if job_status:
            timer_id = get_timer_by_name(timer_name)
            stop_timer_job(timer_id)

            period = bs_config.get_int_value(timer_config, "period")
            mode = bs_config.get_int_value(timer_config, "mode")
            callback = bs_config.get_value(timer_config, "callback")
            if callback:
                timer_job_name_list = callback.split(',')
                start_timer_job(timer_id, period, mode, timer_job_name_list)

def init_timer(config):
    global bs_timer
    bs_timer = bluestone_timer.BluestoneTimer()

    # timer0 is reserved for WDT
    #check_timer(config, 'timer0')
    check_timer(config, 'timer1')
    check_timer(config, 'timer2')
    check_timer(config, 'timer3')

def network_state_changed(args):
    global bs_mqtt

    pdp = args[0]
    state = args[1]
    if state == 1:
        system_log.info("Network %d connected!" % pdp)

        bs_mqtt.disconnect()
        utime.sleep_ms(1000)
        bs_mqtt.connect()

        # set network state to 1, 1 means normal
        bluestone_common.BluestoneCommon.set_network_state(1)
    else:
        system_log.error("Network %d not connected!" % pdp)

def check_network():
    while True:
        try:
            utime.sleep_ms(2000)
            #system_log.info("Check network connection")
            checknet.wait_network_connected()
            retry_count = 0
        except Exception as err:
            retry_count += 1
            system_log.error("Cannot connect to network, will retry it after {} millseconds for {} time".format(2000, retry_count))

            if retry_count >= 10:
                net.setModemFun(4) #进入飞行模式
                system_log.info("Enter airplane mode")
                utime.sleep_ms(2000)

                net.setModemFun(1)  #退出飞行模式
                system_log.info("Exit airplane mode")
                utime.sleep_ms(2000)
    #system_log.info("The network cannot be automatically recovered, restarting system to try again")
    #Power.powerRestart()

def start_network():
    '''
    如果程序包含网络相关代码，必须执行wait_network_connected() 等待网络就绪（拨号成功）；
    '''
    try:
        system_log.info("Check network connection")
        checknet.wait_network_connected()
        dataCall.setCallback(network_state_changed)
        _thread.start_new_thread(check_network, ())
    except Exception as err:
        _thread.start_new_thread(check_network, ())

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

def init_service():
    global bs_aht10, bs_gpio

    bs_aht10 = bluestone_temperature.BluestoneTemperature()
    bs_aht10.aht10_init()

    bs_gpio = bluestone_gpio.BluestoneGPIO()

if __name__ == '__main__':
    utime.sleep(5)
    checknet.poweron_print_once()

    start_network()

    system_log.info("Init system configuration file")
    bs_config = bluestone_config.BluestoneConfig('bluestone_config.json')
    config = bs_config.init_config()

    system_log.info("Init data configuration file")
    bs_data_config = bluestone_config.BluestoneConfig('bluestone_data.json')
    data_config = bs_data_config.init_config()

    system_log.info("Init aht10 and gpio services")
    init_service()

    #system_log.info("Init mqtt service")
    #init_mqtt(config)

    system_log.info("Init tencent mqtt service")
    init_mqtt_tencent(config)

    #system_log.info("Init socket service")
    #init_socket(config)

    system_log.info("Init uart service")
    init_uart(config)

    system_log.info("Init timer service")
    init_timer(config)

    system_log.info("Init wdt service")
    init_wdt()

    while True:
        if state:
            pass
        else:
            break