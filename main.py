#main.py
# 导入所需的模块
import time, network
from maix import GPIO
from machine import UART
from fpioa_manager import fm
from board import board_info

# 定义一个名为wifi的类
class wifi():
    # 初始化类变量
    uart = None
    eb = None
    nic = None

    # 初始化Wi-Fi配置
    def init():
        # 设置引脚映射
        fm.register(15, fm.fpioa.GPIOHS0) 
        __class__.en = GPIO(GPIO.GPIOHS0,GPIO.OUT)

        # 注册UART引脚映射
        fm.register(14,fm.fpioa.UART2_TX) 
        fm.register(13,fm.fpioa.UART2_RX)
        __class__.uart = UART(UART.UART2, 115200, timeout=1000, read_buf_len=8192)

    # 控制Wi-Fi使能
    def enable(en):
        __class__.en.value(en)

    # 发送AT命令
    def _at_cmd(cmd="AT\r\n", resp="OK\r\n", timeout=20):
        __class__.uart.write(cmd) # "AT+GMR\r\n"
        time.sleep_ms(timeout)
        tmp = __class__.uart.read()
        # 如果收到响应
        if tmp and tmp.endswith(resp):
            return True
        return False

    # 发送AT命令并返回结果
    def at_cmd(cmd="AT\r\n", timeout=20):
        __class__.uart.write(cmd) # "AT+GMR\r\n"
        time.sleep_ms(timeout)
        tmp = __class__.uart.read()
        return tmp

    # 重置Wi-Fi连接
    def reset(force=False, reply=5):
        if force == False and __class__.isconnected():
            return True
        # 初始化Wi-Fi配置
        __class__.init()
        for i in range(reply):
            print('reset...')
            # 禁用然后启用Wi-Fi
            __class__.enable(False)
            time.sleep_ms(50)
            __class__.enable(True)
            time.sleep_ms(500) # at start > 500ms
            if __class__._at_cmd(timeout=500):
                break
        __class__._at_cmd()
        # 设置UART参数
        __class__._at_cmd('AT+UART_CUR=921600,8,1,0,0\r\n', "OK\r\n")
        __class__.uart = UART(UART.UART2, 921600, timeout=1000, read_buf_len=10240)
        try:
            # 尝试建立网络连接
            __class__.nic = network.ESP8285(__class__.uart)
            time.sleep_ms(500) # 等待准备连接
        except Exception as e:
            print(e)
            return False
        return True

    # 连接到指定的Wi-Fi网络
    def connect(ssid="wifi_name", pasw="pass_word"):
        if __class__.nic != None:
            return __class__.nic.connect(ssid, pasw)

    # 获取当前Wi-Fi网络配置信息
    def ifconfig(): # should check ip != 0.0.0.0
        if __class__.nic != None:
            return __class__.nic.ifconfig()

    # 检查Wi-Fi是否已连接
    def isconnected():
        if __class__.nic != None:
            return __class__.nic.isconnected()
        return False

# 检查模块是否作为主程序运行
if __name__ == "__main__":

    # 定义要连接的Wi-Fi网络的名称和密码
    SSID = "ssid"
    PASW = "password"

    # 设置要连接的服务器的地址和端口号
    ADDR = ("192.168.xx.xx", 8080)

    # 定义检查并连接Wi-Fi网络的函数
    def check_wifi_net(reply=5):
        # 如果当前未连接到Wi-Fi网络
        if wifi.isconnected() != True:
            # 尝试连接Wi-Fi网络，最多尝试reply次
            for i in range(reply):
                try:
                    # 重置Wi-Fi连接
                    wifi.reset()
                    # 尝试通过AT命令连接Wi-Fi网络
                    print('try AT connect wifi...', wifi._at_cmd())
                    # 使用预定义的SSID和密码连接Wi-Fi网络
                    wifi.connect(SSID, PASW)
                    # 如果成功连接到Wi-Fi网络，跳出循环
                    if wifi.isconnected():
                        break
                # 捕获异常并打印错误信息
                except Exception as e:
                    print(e)
        # 返回Wi-Fi连接状态
        return wifi.isconnected()

    # 如果Wi-Fi未连接，调用check_wifi_net函数进行连接
    if wifi.isconnected() == False:
        check_wifi_net()

    # 打印当前网络状态和网络配置信息
    print('network state:', wifi.isconnected(), wifi.ifconfig())

# 导入所需的模块
import socket, time, sensor, image
import lcd
from maix import KPU

# 初始化LCD屏幕
lcd.init()
# 重置传感器
sensor.reset()
# 设置图像格式为RGB565
sensor.set_pixformat(sensor.RGB565)
# 设置帧大小为QVGA
sensor.set_framesize(sensor.QVGA)
# 跳过2000帧
sensor.skip_frames(time=2000)
# 初始化时钟
clock = time.clock()

# 定义锚点
anchor = (0.1075, 0.126875, 0.126875, 0.175, 0.1465625, 0.2246875, 0.1953125, 0.25375, 0.2440625, 0.351875, 0.341875, 0.4721875, 0.5078125, 0.6696875, 0.8984375, 1.099687, 2.129062, 2.425937)
# 初始化KPU模型
kpu = KPU()
# 加载人脸检测模型
kpu.load_kmodel("/sd/KPU/yolo_face_detect/face_detect_320x240.kmodel")
# 初始化Yolo2模型
kpu.init_yolo2(anchor, anchor_num=9, img_w=320, img_h=240, net_w=320, net_h=240, layer_w=10, layer_h=8, threshold=0.7, nms_value=0.2, classes=1)

# 初始化68关键点检测的KPU模型
lm68_kpu = KPU()
# 打印提示信息
print("ready load model")
# 加载68关键点检测模型
lm68_kpu.load_kmodel("/sd/KPU/face_detect_with_68landmark/landmark68.kmodel")

# 定义函数来扩展框的大小
def extend_box(x, y, w, h, scale):
    x1_t = x - scale * w
    x2_t = x + w + scale * w
    y1_t = y - scale * h
    y2_t = y + h + scale * h
    x1 = int(x1_t) if x1_t > 1 else 1
    x2 = int(x2_t) if x2_t < 320 else 319
    y1 = int(y1_t) if y1_t > 1 else 1
    y2 = int(y2_t) if y2_t < 240 else 239
    cut_img_w = x2 - x1 + 1
    cut_img_h = y2 - y1 + 1
    return x1, y1, cut_img_w, cut_img_h

while True:
    # send pic
    sock = socket.socket()
    sock.connect(ADDR)
    sock.send('hello\n')

    send_len, count, err = 0, 0, 0
    # 无限循环，实现实时人脸检测
    while True:
        # 记录当前时间
        clock.tick()
        # 检查错误计数是否达到阈值
        if err >= 10:
            # 如果错误计数达到阈值，打印错误信息并跳出循环
            print("socket broken")
            break
        # 从相机中获取当前图像
        img = sensor.snapshot()

    # 运行Yolo2人脸检测模型
        kpu.run_with_output(img)
        # 获取检测到的人脸的位置和尺寸信息
        dect = kpu.regionlayer_yolo2()
        # 计算处理帧率
        fps = clock.fps()
        # 如果检测到人脸
        if len(dect) > 0:
            # 打印检测到的人脸的位置和尺寸信息
            print("dect:", dect)
            # 检查人脸是否低头
            if (dect[0][3]) <= 118:
                # 如果人脸未低头，打印“正常”
                print('正常')
            else:
                # 如果人脸低头
                # 在LCD屏幕上显示当前图像
                lcd.display(img)
                # 跳过一定时间的帧
                sensor.skip_frames(time=200)
                # 导入用于播放音频的模块
                import wav_play 
            # 处理每个检测到的人脸
for l in dect:
    # 扩展人脸框
    x1, y1, cut_img_w, cut_img_h = extend_box(l[0], l[1], l[2], l[3], scale=0.08)
    # 裁剪人脸
    face_cut = img.cut(x1, y1, cut_img_w, cut_img_h)
    # 在原图像上画出人脸框
    a = img.draw_rectangle(l[0], l[1], l[2], l[3], color=(0, 255, 0))
    # 将裁剪的人脸图像调整为128x128大小
    face_cut_128 = face_cut.resize(128, 128)
    # 将图像转换为AI模型可接受的格式
    face_cut_128.pix_to_ai()
    # 运行68关键点检测模型并获取输出
    out = lm68_kpu.run_with_output(face_cut_128, getlist=True)
    # 打印输出信息长度
    print("out:", len(out))
    # 对每个关键点在图像上画出圆圈
    for j in range(68):
        x = int(KPU.sigmoid(out[2 * j]) * cut_img_w + x1)
        y = int(KPU.sigmoid(out[2 * j + 1]) * cut_img_h + y1)
        a = img.draw_circle(x, y, 2, color=(0, 0, 255), fill=True)
    # 释放内存
    del (face_cut_128)
    del (face_cut)

# 在图像上显示帧率
a = img.draw_string(0, 0, "%2.1ffps" % (fps), color=(0, 60, 255), scale=2.0)
# 在LCD上显示图像
lcd.display(img)
# 对图像进行压缩
img = img.compress(quality=60)
# 将图像转换为字节流
img_bytes = img.to_bytes()
# 打印发送的字节长度
print("send len: ", len(img_bytes))

try:
    # 将图像字节流分块发送
    block = int(len(img_bytes) / 2048)
    for i in range(block):
        send_len = sock.send(img_bytes[i * 2048:(i + 1) * 2048])
        #time.sleep_ms(500)
    # 发送剩余部分
    send_len2 = sock.send(img_bytes[block * 2048:])
    # 检查发送是否成功
    if send_len == 0:
        raise Exception("send fail")
except OSError as e:
    # 检查连接是否关闭
    if e.args[0] == 128:
        print("connection closed")
        break
except Exception as e:
    # 处理发送异常
    print("send fail:", e)
    time.sleep(1)
    err += 1
    continue
# 更新发送计数
count += 1
# 打印发送次数和帧率
print("send:", count)
print("fps:", clock.fps())
#time.sleep_ms(500)

# 关闭KPU模型
kpu.deinit()
# 关闭68关键点检测模型
lm68_kpu.deinit()
# 打印关闭信息
print("close now")
# 关闭socket连接
sock.close()

