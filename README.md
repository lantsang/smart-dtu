##  前言
本文的主要目的是说明青石SmartDtu到底做了哪些工作？我们在移远硬件平台EC600S上做了哪些支持？为什么说这套平台是硬件开发者的福音？我们的初衷是解放广大硬件开发者的双手，提供一套成熟的嵌入式软硬件解决方案，让开发者尤其是硬件开发者专注于硬件本身。

基础支持指我们的软件和平台支持移远EC600S的基础功能，比如定时器、温湿度、PWM、GPIO、UART和FOTA。

资源管理是指通过软件平台可以通过串口和MQTT指令来管理EC600S系统上的资源，实现远程数据采集和远程控制，目前支持有远程开启定时器采集温湿度，远程控制GPIO引脚的开启和关闭等等。

平台支持是借助腾讯云平台作为中间平台，将EC600S硬件和青石的平台连通起来，既可以满足大量数据的稳定性交互能力，又可以保障数据和通信的安全性。



- **[硬件平台](#jump_1)**
- **[开发环境](#jump_2)**
- **[代码架构](#jump_3)**
- **[定时器](#jump_4)**
- **[温湿度](#jump_5)**
- **[GPIO](#jump_6)**
- **[UART](#jump_7)**
- **[FOTA](#jump_8)**
- **[运行截图](#jump_9)**
- **[版权信息](#jump_10)**

<a id="jump_1"></a>
## 1 硬件平台
我们的代码运行在移远的EC600S平台上，开发语言是QuecPython，这是移远官方基于MicroPython扩展的开发语言，专门用于移远平台的嵌入式开发，在功能接口定义还是目录结构形式都与MicroPython保持高度的一致。两者同样应用于嵌入式场景开发，轻Python开发语言使得开发者上手更快，开发门槛大大降低。
![EC600S平台](https://python.quectel.com/doc/doc/Quecpython_intro/zh/Qp_Hw_EC600X/media/EC600XV1.1_positive.png)

<a id="jump_2"></a>
## 2 开发环境
| 名称   | 工具名称 |   备注   |
| :----- | :--: | :------- |
| visual stutio code |  QuecPython开发  | 开发 |
| QCOM |  串口工具  | 串口调试 |
| QPYcom|  烧录工具和执行环境  | 开发调试 |

<a id="jump_3"></a>
## 3 代码架构
### 3.1 代码结构图
![代码组织结构图](https://bluestone.oss-cn-beijing.aliyuncs.com/images/code_structure.PNG)

1. bluestone_commom.py
这个文件是整个项目的公共文件，主要有一些获取网络状态、设置网络状态、检查文件是否存在和判断路径是否为URL等方法。

2. bluestone_config.py
这个文件主要是用于处理系统正常运行过程中用到的参数，包括从文件中读取参数、向文件中写入参数和默认参数配置项等等。

3. bluestone_daemon.py
守护文件，主要目的是保证嵌入式系统在运行过程中的健康，一旦发生异常中断或者断线无法恢复的情况就会尝试重启系统，目前还在开发中。

4. bluestone_fota.py
主要用来管理应用程序和固件的升级，其中应用程序支持多个文件路径，固件包升级仅支持单个文件。

5. bluestone_gpio.py
主要用来管理系统中所有GPIO引脚的状态，包括读取和写入。

6. bluestone_main.py
系统的入口文件，负责启动网络守护线程、初始化配置文件、数据文件、初始化系统服务、MQTT服务、串口服务、定时器服务和看门狗服务。

7. bluestone_mqtt.py
MQTT客户端管理工具，负责启动MQTT，监听回调并解析回调指令和参数，根据解析出的回调指令和参数执行相对应的命令。

8. bluestone_mqtt_tencent.py
Tencent MQTT客户端管理工具，负责启动MQTT，监听回调并解析回调指令和参数，根据解析出的回调指令和参数执行相对应的命令。

9. bluestone_pwm.py
PMW控制逻辑，负责打开和关闭PMW端口，可以模拟实现呼吸灯。

10. bluestone_socket.py
用于初始化TCP/IP socket，连接客户端并接收和发送指令，未完待续。

11. bluestone_temperature.py
采集板载温湿度传感器的数值。

12. bluestone_timer.py
管理定时器，按照一定参数启动或停止定时器。

13. bluestone_uart.py
管理串口，按照传入的参数启动串口，读取串口参数并解析命令，如果有满足条件的命令就去执行，包括重启系统等。

14. bluestone_config.json
默认配置文件，文件内有关于UART0~2的配置参数和Tencent MQTT的启动参数，用户可以按照自己的实际情况进行修改。
```json
{
	"uart2": {
		"parity": 0,
		"baud_rate": 115200,
		"flow_control": 0,
		"stop_bits": 1,
		"data_bits": 8
	},
	"mqtt_tencent": {
		"product_id": "输入你在腾讯云上的产品编号",
		"pub_topic": "event",
		"product_secret": "输入你在腾讯云上的产品密钥",
		"sub_topic": "control"
	},
	"uart1": {
		"parity": 0,
		"flow_control": 0,
		"baud_rate": 115200,
		"stop_bits": 1,
		"data_bits": 8
	},
	"uart0": {
		"baud_rate": 115200,
		"parity": 0,
		"flow_control": 0,
		"stop_bits": 1,
		"data_bits": 8
	}
}
```

<a id="jump_4"></a>
## 4 定时器
传入指令如下：
```json
{
	"timer1": {
		"status": 1,
		"period": 5000,
		"mode": 1,
		"callback": "aht10"
	}
}
```
- **timer1**: EC600S有四个定时器，分别是timer0,timer1,timer2,timer3，其中timer0被系统占用，仅可以使用timer1~timer3；
- **status**: 定时器任务的状态；0表示关闭，1表示启动；
- **period**: 定时器运行周期，单位是毫秒；服务端支持的周期是5000~30000毫秒；
- **mode**: 定时器运行模式，0表示仅运行一次，1表示周期运行；
- **callback**: 定时器每循环一次要执行的函数名称，目前仅支持"aht10"和"gpio"，分别表示采集温湿度和读取GPIO引脚状态；多个回调函数之间用逗号分隔。

注：定时器参数配置成功后系统会自动重启。

<a id="jump_5"></a>
## 5 温湿度
温湿度的采集是通过定时器执行的，按照如上配置，只要在callback中填写"aht10"即可。

<a id="jump_6"></a>
## 6 GPIO
控制指令如下：
```json
{
	"gpio": {
		"gpio1": 1,
		"gpio2": 1,
		"gpio3": 0,
		"gpio4": 1,
		"gpio5": 1,
		"gpio6": 1,
		"gpio7": 1,
		"gpio8": 1,
		"gpio9": 0,
		"gpio10": 1,
		"gpio11": 0,
		"gpio12": 1,
		"gpio13": 1,
		"gpio14": 1
	}
}
```
- **gpio**: 表示当前指令是用于控制GPIO的；
- **gpio1**: 表示控制GPIO1号引脚，0表示低电平，1表示高电平，以此类推；

<a id="jump_7"></a>
## 7 UART
```json
{
	"uart1": {
		"baud_rate": 115200,
		"data_bits": 8,
		"flow_control": 0,
		"parity": 0,
		"stop_bits": 1
	}
}
```

- **uart1**: 表示当前串口编号，支持uart0,uart1,uart2;
- **baud_rate**: 串口波特率；
- **data_bits**: 串口数据位；
- **flow_control**: 流量控制；
- **parity**: 校验位；
- **stop_bits**: 停止位；

注：串口参数配置成功后系统会自动重启。

<a id="jump_8"></a>
## 8 FOTA
```json
{
	"fota": {
		"mode": 0,
		"url": "http://app.com/download"
	}
}
```

- **fota**: 表示升级配置参数;
- **mode**: 0表示升级应用程序，在这种模式下url可以支持多个，不同url之间以逗号分隔；1表示升级固件包，在这种模式下仅支持一个url地址；
- **url**: 应用程序或固件包的地址，不支持https；

注：升级成功后系统会自动重启。

<a id="jump_9"></a>
## 9 运行截图
### 9.1 首页
![首页](https://bluestone.oss-cn-beijing.aliyuncs.com/images/home.PNG)

### 9.2 产品列表
![产品列表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/product.PNG)

### 9.3 设备列表
![设备列表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/device_list.PNG)

![设备图表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/device_chart.PNG)

![设备温湿度列表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/device_th_list.PNG)

![设备温湿度图表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/device_th_chart.PNG)

![设备GPIO图表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/gpio.PNG)

### 9.4 体验账号
[青石SmartDtu平台](https://dtu.lantsang.net)，登录账号：dtu, 登陆密码：d123qwe

## 10 版权信息
[MIT](https://gitee.com/lantsang/smart-dtu/blob/master/LICENSE)