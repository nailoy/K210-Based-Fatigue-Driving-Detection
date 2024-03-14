# 导入所需的库
from fpioa_manager import *
from maix import I2S, GPIO
import audio

########### 设置 ############
WIFI_EN_PIN = 15
AUDIO_PA_EN_PIN = 2

# 禁用wifi
fm.register(WIFI_EN_PIN, fm.fpioa.GPIO0, force=True)
wifi_en = GPIO(GPIO.GPIO0, GPIO.OUT)
wifi_en.value(0)

# 开启音频PA
if AUDIO_PA_EN_PIN:
    fm.register(AUDIO_PA_EN_PIN, fm.fpioa.GPIO1, force=True)
    wifi_en = GPIO(GPIO.GPIO1, GPIO.OUT)
    wifi_en.value(1)

# 注册I2S(I2S0)引脚
fm.register(31, fm.fpioa.I2S0_OUT_D1, force=True)
fm.register(32, fm.fpioa.I2S0_SCLK, force=True)
fm.register(30, fm.fpioa.I2S0_WS, force=True)

# 初始化I2S(I2S0)
wav_dev = I2S(I2S.DEVICE_0)

# 初始化音频
player = audio.Audio(path="/sd/1.wav")
player.volume(100)

# 读取音频信息
wav_info = player.play_process(wav_dev)
print("wav文件头信息：", wav_info)

# 根据音频信息配置I2S
wav_dev.channel_config(wav_dev.CHANNEL_1, I2S.TRANSMITTER, resolution=I2S.RESOLUTION_16_BIT,
                       cycles=I2S.SCLK_CYCLES_32, align_mode=I2S.RIGHT_JUSTIFYING_MODE)
wav_dev.set_sample_rate(wav_info[1])

# 循环播放音频
while True:
    ret = player.play()
    if ret == None:
        print("格式错误")
        break
    elif ret == 0:
        print("结束")
        break
player.finish()
