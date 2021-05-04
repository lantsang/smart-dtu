'''

File: bluestone_pwm_breathe_main.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import utime
import log
import net
import checkNet

from usr import bluestone_pwm

'''
下面两个全局变量是必须有的，用户可以根据自己的实际项目修改下面两个全局变量的值，
在执行用户代码前，会先打印这两个变量的值。
'''
PROJECT_NAME = "Bluestone pwm breathe sample"
PROJECT_VERSION = "1.0.0"
checknet = checkNet.CheckNetwork(PROJECT_NAME, PROJECT_VERSION)

# 设置日志输出级别
log.basicConfig(level = log.INFO)
system_log = log.getLogger("MAIN")

state = 1

bs_pwm = None

def system_init():
    global bs_pwm
    
    bs_pwm = bluestone_pwm.BluestonePWM()

if __name__ == '__main__':
    utime.sleep(5)
    checknet.poweron_print_once()
    
    system_init()
    
    pwm = bs_pwm.get_id_by_name('pwm0')
    if pwm:
        bs_pwm.start_breathe(pwm, 1)

    while True:
        if state:
            pass
        else:
            break