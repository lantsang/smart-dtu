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
- **[使用流程](#jump_9)**
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
## 9 系统使用
下面将从新建产品到设备数据等8个环节来演示系统使用方法。  
[青石SmartDtu平台](https://dtu.lantsang.net)，登录账号：dtu, 登陆密码：d123qwe

### 9.1 新建产品
1.点击左侧菜单栏进入产品列表页</br>

![进入产品列表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E8%BF%9B%E5%85%A5%E4%BA%A7%E5%93%81%E5%88%97%E8%A1%A8.png)

2.点击新建打开新建产品窗口,填写产品信息</br>

![点击新建](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E7%82%B9%E5%87%BB%E6%96%B0%E5%BB%BA.png)
![填写产品信息](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E5%A1%AB%E5%86%99%E4%BA%A7%E5%93%81%E4%BF%A1%E6%81%AF.png)

3.产品创建成功</br>

![新建成功](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E6%96%B0%E5%BB%BA%E4%BA%A7%E5%93%81%E6%88%90%E5%8A%9F.png)

### 9.2 设备硬件配置
#### 9.2.1 驱动安装
进入移远[官方下载](https://python.quectel.com/download)页面，下载 `USB驱动` ，如下图：

![移远USB驱动下载页面](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E9%A9%B1%E5%8A%A8.png)

注意操作系统，目前来看是没有找到 `Mac` 和 `Linux` 下的驱动，暂不知道是没有提供还是根本不需要。

双击安装即可。
* **验证是否安装成功**

将电脑与开发板连接，会发现**电源状态灯**亮起（为**红色**），之后**长按**开机按钮，大约 `5秒` 后松手，稍等 `5秒` 左右，发现**NET状态灯**开始闪烁（移远COM端口驱动，间隔大约**2秒**），进入电脑的 `设备管理器` ，查看 `端口(COM 和 LPT)` 项，发现如下图所示设备即表示安装成功！

![移远COM端口驱动](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E9%A9%B1%E5%8A%A8%E5%AE%89%E8%A3%85%E6%88%90%E5%8A%9F.png)
> **温馨提示：** 在官方文档中，这里写的比较简陋，只说了将开发板与电脑连接后就能看到设备，实际发现如果不开机，是看不到设备的！还有，**官方文档中的配图显示有三个设备，实际发现只有两个**，并没有配图中提到的**指令交互串口**，产生这个现象的原因是设备在出厂的时候烧录的固件不是 `Python` 固件，在烧录完 `Python` 固件后就能看到

#### 9.2.2 QPYcom图形化工具安装
进入移远[官方下载](https://python.quectel.com/download)页面，下载 `QPYcom 图形化工具` ，如下图：
![QPYcom图形化工具下载页面](https://bluestone.oss-cn-beijing.aliyuncs.com/images/QPYcom%20%E5%9B%BE%E5%BD%A2%E5%8C%96%E5%B7%A5%E5%85%B7.png)
这个下载完成后是一个压缩包，解压后双击 `QPYcom.exe` 可执行文件即可。

> **温馨提示**：这个软件运行完成后会在相同路径下生成一些其他文件，如： `Config.ini` 等，建议将其按照习惯整理到一个空文件夹下。

`QPYcom` 软件运行结果如下所示：

![QPYcom软件截图](https://bluestone.oss-cn-beijing.aliyuncs.com/images/QPYcom%20%E7%95%8C%E9%9D%A2.png)

#### 9.2.3 设备配置
选择串口为图中串口

![选择串口](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E9%80%89%E6%8B%A9%E4%B8%B2%E5%8F%A3.png)

打开下载页，点击创建按钮新建项目

![新建项目](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E5%88%9B%E5%BB%BA%E9%A1%B9%E7%9B%AE.png)

进入移远[官方下载](https://python.quectel.com/download)页面，下载 `固件包` ，

![固件包下载](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E5%9B%BA%E4%BB%B6%E5%8C%85%E9%A1%B5%E9%9D%A2.png)

下载后解压为`QPY_V0004_EC600S_FW.zip`文件，选择固件

![选择固件](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E9%80%89%E6%8B%A9%E5%9B%BA%E4%BB%B6.png)
![选择固件完成](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E9%80%89%E6%8B%A9%E5%9B%BA%E4%BB%B6%E5%AE%8C%E6%88%90.png)

点击下载固件，将固件包下载至开发板

![下载固件](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E4%B8%8B%E8%BD%BD%E5%9B%BA%E4%BB%B6.png)

进入[控制程序下载](https://gitee.com/lantsang/smart-dtu)页面，下载 `控制程序` ，解压，

![控制程序下载](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E6%8E%A7%E5%88%B6%E7%A8%8B%E5%BA%8F%E4%B8%8B%E8%BD%BD.png)

将bluestone_config.json文件中的product_id和product_secret替换为新建产品的产品id与密钥（从产品列表页获取）

![产品id密钥](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E4%BA%A7%E5%93%81id%E5%AF%86%E9%92%A5.png)
![产品id密钥替换](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E4%BA%A7%E5%93%81id%E5%AF%86%E9%92%A5%E6%9B%BF%E6%8D%A2.png)

导入图中所选代码文件

![添加脚本](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E6%B7%BB%E5%8A%A0%E8%84%9A%E6%9C%AC.png)
![选择脚本](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E5%AF%BC%E5%85%A5%E5%BA%94%E7%94%A8%E7%A8%8B%E5%BA%8F.png)
![选择所选文件](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%A8%8B%E5%BA%8F%E5%AE%8C%E6%88%90.png)

点击下载脚本，将控制程序下载至开发板

![下载脚本](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E4%B8%8B%E8%BD%BD%E8%84%9A%E6%9C%AC.png)

点击文件，关闭串口后重新打开，如图所示启动设备

![运行设备](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E8%BF%90%E8%A1%8C.png)

### 9.3 新建设备
本系统采用动态注册逻辑，配置好设备参数之后，只要设备上线，即可注册至系统，无需手动创建或导入设备

### 9.4 设备管理
点击左侧菜单栏中`设备列表`,进入设备列表页面后点击设备行内`管理`按钮即可管理设备

![管理设备](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E7%AE%A1%E7%90%86%E8%AE%BE%E5%A4%87.png)
#### 9.4.1 编辑设备
如图，点击编辑按钮即可编辑设备，目前仅支持修改设备备注

![编辑设备](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E7%BC%96%E8%BE%91%E8%AE%BE%E5%A4%87.png)
#### 9.4.2 删除设备

点击删除按钮，即可删除设备

![删除设备](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E5%88%A0%E9%99%A4%E8%AE%BE%E5%A4%87.png)

>注：由于使用动态注册，若删除后设备仍然存在，收到设备信号后设备将会重新注册，所以删除设备前请确保设备已物理删除

#### 9.4.3 状态重置

点击状态重置按钮，可将设备状态重置为未激活状态

![状态重置](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E7%8A%B6%E6%80%81%E9%87%8D%E7%BD%AE.png)

#### 9.4.4 设备禁用
点击设备启用禁用的滑块开关，可更改设备的启用状态，设备禁用后，将不再收取该设备的消息

![禁用设备](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E7%A6%81%E7%94%A8%E8%AE%BE%E5%A4%87.png)

### 9.5 设备温湿度管理
点击左侧菜单栏中`设备列表`,进入设备列表页面后点击设备行内`温湿度`按钮即可进行设备温湿度管理

![设备温湿度管理](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E6%B8%A9%E6%B9%BF%E5%BA%A6%E7%AE%A1%E7%90%86.png)

>注：设备状态为离线或未激活时无法进行温湿度管理

#### 9.5.1 查看设备温湿度数据

![数据列表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E6%B8%A9%E6%B9%BF%E5%BA%A6%E6%95%B0%E6%8D%AE%E5%88%97%E8%A1%A8.png)

#### 9.5.2 查看温湿度变化趋势

点击左上数据图表按钮，可切换至图表显示，查看设备温湿度变化趋势

![温湿度图表](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E6%B8%A9%E6%B9%BF%E5%BA%A6%E5%9B%BE%E8%A1%A8.png)

#### 9.5.3 温湿度采集配置
更改采集相关参数后同步设置，可调整设备是否上报或设备上报周期（最小60s,最大15min）

![采集配置](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E6%B8%A9%E6%B9%BF%E5%BA%A6%E9%87%87%E9%9B%86%E9%85%8D%E7%BD%AE.png)


### 9.6 设备GPIO管理
点击左侧菜单栏中`设备列表`,进入设备列表页面后点击设备行内`GPIO`按钮即可进行设备温湿度管理

![设备GPIO管理](https://bluestone.oss-cn-beijing.aliyuncs.com/images/GPIO%E7%AE%A1%E7%90%86.png)

>注：设备状态为离线或未激活时无法进行GPIO管理

点击单个GPIO滑块开关或者点击一键开启、一键关闭按钮，即可更改设备GPIO状态

![GPIO开关](https://bluestone.oss-cn-beijing.aliyuncs.com/images/GPIO%E5%BC%80%E5%85%B3.png)


### 9.7 设备UART管理
点击左侧菜单栏中`设备列表`,进入设备列表页面后点击设备行内`UART`按钮即可进行设备温湿度管理

![设备UART管理](https://bluestone.oss-cn-beijing.aliyuncs.com/images/UART%E7%AE%A1%E7%90%86.png)

>注：设备状态为离线或未激活时无法进行UART管理

#### 9.7.1 设备UART数据

![设备UART数据](https://bluestone.oss-cn-beijing.aliyuncs.com/images/UART%E5%88%97%E8%A1%A8.png)

#### 9.7.2 设备UART串口配置
更改串口相关参数后同步设置，可实现设备UART串口配置的修改

![UART串口配置](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E4%B8%B2%E5%8F%A3%E9%85%8D%E7%BD%AE.png)

### 9.8 设备数据

#### 9.8.1 设备历史数据
点击左侧菜单栏中`设备数据`，可查看设备所有历史消息数据

![设备历史数据](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E8%AE%BE%E5%A4%87%E6%95%B0%E6%8D%AE.png)

#### 9.8.2 首页统计
数量概况

![数量概况](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E8%AE%BE%E5%A4%87%E6%95%B0%E9%87%8F%E6%A6%82%E5%86%B5.png)

数量变化趋势

![数量变化趋势](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E8%AE%BE%E5%A4%87%E5%8F%98%E5%8C%96%E8%B6%8B%E5%8A%BF.png)

排行榜

![排行榜](https://bluestone.oss-cn-beijing.aliyuncs.com/images/%E8%AE%BE%E5%A4%87%E6%8E%92%E8%A1%8C%E6%A6%9C.png)

<a id="jump_10"></a>
## 10 版权信息
[MIT](https://gitee.com/lantsang/smart-dtu/blob/master/LICENSE)