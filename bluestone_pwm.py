'''

File: bluestone_pwm.py

Project: bluestone

Author: daniel dong

Email: dongzhenguo@lantsang.cn

Copyright 2021 - 2021 bluestone tech

'''

import utime
import log
import _thread

from misc import PWM

log.basicConfig(level = log.INFO)
_pwm_log = log.getLogger("PWM")

class BluestonePWM(object):
    inst = None

    def __init__(self):
        BluestonePWM.inst = self

        self.pwm_name_list = ["pwm0", "pwm1", "pwm2", "pwm3"]
        self.pwm_list = [PWM.PWM0, PWM.PWM1, PWM.PWM2, PWM.PWM3]

        self.used_pwm_list = {}

    def get_id_by_name(self, name):
        index = self.pwm_name_list.index(name)
        return self.pwm_list[index]

    def _open(self, pwm_id):
        pwm = None
        keys = self.used_pwm_list.keys()
        if pwm_id in keys:
            pwm = self.used_pwm_list[pwm_id]
        if pwm is not None:
            pwm.open()
            _pwm_log.info("PWM {} was opened".format(pwm_id))

    def _close(self, pwm_id):
        pwm = None
        keys = self.used_pwm_list.keys()
        if pwm_id in keys:
            pwm = self.used_pwm_list[pwm_id]
        if pwm is not None:
            pwm.close()
            pwm = None
            _pwm_log.info("PWM {} was closed".format(pwm_id))

    '''
        注：EC100YCN平台，支持PWM0~PWM3，对应引脚如下：
        PWM0 – 引脚号19
        PWM1 – 引脚号18
        PWM2 – 引脚号23
        PWM3 – 引脚号22

        注：EC600SCN平台，支持PWM0~PWM3，对应引脚如下：
        PWM0 – 引脚号52
        PWM1 – 引脚号53
        PWM2 – 引脚号70
        PWM3 – 引脚号69
    '''
    def _init_pwm(self, pwm_id, frequency, duty_cycle):
        # us为计算单位, frequency单位为KHz,也就是1表示1KHz
        cycle_time = int(1 * 1000 / frequency )
        high_time = int(cycle_time * duty_cycle)

        pwm = None
   
        try:
            # ms 周期范围
            if cycle_time > 1000:
                # 周期在 (1K us ~ 1000K us)
                high_time = int(high_time / 1000)
                cycle_time = int(cycle_time / 1000)
                pwm = PWM(pwm_id, PWM.ABOVE_MS, high_time, cycle_time)
                _pwm_log.info("PWM_ABOVE_MS {} 的周期:{}ms, 占空比:{}, 频率:{}KHz".format(pwm_id, cycle_time, duty_cycle, frequency))
            if (cycle_time > 10) and (cycle_time < 15750):
                # 周期在 10us ~ 15.75ms
                #high_time = int(high_time / 10)
                #cycle_time = int(cycle_time / 10)
                pwm = PWM(pwm_id, PWM.ABOVE_10US, high_time, cycle_time)
                _pwm_log.info("PWM_ABOVE_10US {} 的周期:{}us, 占空比:{}, 频率:{}KHz".format(pwm_id, cycle_time, duty_cycle, frequency))
            if (cycle_time > 0) and (cycle_time < 157):
                # 周期在 (0~157us)
                pwm = PWM(pwm_id, PWM.ABOVE_1US, high_time, cycle_time)
                _pwm_log.info("PWM_ABOVE_1US {} 的周期:{}us, 占空比:{}, 频率:{}KHz".format(pwm_id, cycle_time, duty_cycle, frequency))
        except Exception as err:
	        _pwm_log.error("Cannot init pwm, the error is {}".format(err))

        if pwm is not None:
            self.used_pwm_list[pwm_id] = pwm

    '''
    frequency = 1, 表示频率为1K
    duty_cycle = 0.5, 表示占空比为50%
    '''
    def _init(self, pwm_id, frequency = 1, duty_cycle = 0.5):
        if (frequency <= 0) or (frequency > 1000):
            _pwm_log.error("{} 不支持的频率参数，请输入（0~1000）k范围的频率".format(frequency))
            return
        if(duty_cycle < 0.0) or (duty_cycle >= 1):
            _pwm_log.error("{} 不支持的占空比参数，请输入（0~1）范围的频率".format(frequency))
            return

        self._init_pwm(pwm_id, frequency, duty_cycle)

    def start_once(self, pwm_id, frequency = 1, duty_cycle = 0.5):
        self._close(pwm_id)
        utime.sleep_ms(300)

        # 这里的频率必须为>=1的整数
        self._init(pwm_id, int(frequency), duty_cycle)
        self._open(pwm_id)

    def _start_once_breathe(self, pwm_id, frequency = 1, duty_cycle = 0.5):
        self._init(pwm_id, frequency, duty_cycle)
        self._open(pwm_id)

    def _init_pwm_breathe(self, pwm_id, frequency = 1):
        positive_duty_cycle_array = range(1, 30)
        negative_duty_cycle_array = range(30, 1, -1)

        while True:
            for cycle in negative_duty_cycle_array:
                duty_cycle = float(cycle / 30)
                duty_cycle = round(duty_cycle, 2)
                _thread.start_new_thread(self._start_once_breathe, (pwm_id, frequency, duty_cycle))
                utime.sleep_ms(100)
            for cycle in positive_duty_cycle_array:
                duty_cycle = float(cycle / 30)
                duty_cycle = round(duty_cycle, 2)
                _thread.start_new_thread(self._start_once_breathe, (pwm_id, frequency, duty_cycle))
                utime.sleep_ms(100)
             
    def start_breathe(self, pwm_id, frequency = 1):
        _thread.start_new_thread(self._init_pwm_breathe, (pwm_id, frequency))
        