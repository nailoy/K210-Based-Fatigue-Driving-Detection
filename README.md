# 基于K210的疲劳驾驶检测模块

## 1. 项目简介
本项目基于Maix版K210开发
官方说明文档：https://wiki.sipeed.com/soft/maixpy/zh/index.html
Maix IDE下载链接：https://dl.sipeed.com/MAIX/MaixPy/ide/
路径如下：download_station_file>MAIX>MaixPy>ide>v0.2.5

## 2. 程序说明
main.py: 主程序代码
wav_play.py: 播放音频代码，1.wav是预录制的音频
后缀名为*.kmodel为模型文件

## 3. 目标展望
能够流畅识别驾驶员面部表情，通过闭眼或者打哈欠来判断驾驶员是否进入疲劳状态。
通过和Esp8266串口通信传输数据到服务端（例如App、网页或者微信小程序），在后台进行对驾驶员的监控。