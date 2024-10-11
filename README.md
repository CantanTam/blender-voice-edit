使用51天问的语音识别模块，识别语音命令后，对 usb 串口输出命令；Blender 插件检测到串口命令后，执行相应的 api，实现语音操作 Blender 的目的。

## 安装使用教程懒人版：
[语音操作Blender【免费插件】【支持linux】\_哔哩哔哩\_bilibili](https://www.bilibili.com/video/BV12w2CYWEUp/?spm_id_from=333.999.0.0&vd_source=e4cbc5ec88a2d9cfc7450c34eb007abe)

## Windows 安装 Python 依赖库：
1. 打开 www.python.org 下载安装安装 Python 最新版本，安装过程中需要把**Add python.exe to PATH**勾选上；
2. `win + R` 调出“运行”窗口；
3. “运行”窗口输入`cmd`并运行；
4. “命令提示符”窗口输入 `pip install pyserial pyautogui` ，等待数分钟完成安装；
5. 文件浏览器打开 `C:\USER\<你的用户名>\AppData\Local\Programs\Python\PythonXXX\Lib\site-packages` 选择所有新安装的依赖库，复制到 `C:\Program Files\Blender Foundation\Blender<版本号>\<版本号>\python\lib\site-packages` 文件夹当中。

## Linux 安装 Python 依赖库：
### Manjaro

```
sudo pacman -S yay
yay -S python-pyautogui python-pyserial
```

### Fedora

```
sudo dnf install python3-pip
pip3 install pyserial pyautogui
```

### Ubutnu

```
sudo apt install python3-pip
pip3 install pyautogui pyserial
```

> 注：以上安装方法由 ChatGPT 提供，Manjaro平台下安装方法可行，但 Fedora 和 Ubuntu 的安装可行性请自行验证。

## 天问语音识别模块代码烧录(仅限Windows平台)：
1. 打开 www.twen51.com ，下载安装 `天问Block` 以及 `ASR-PRO-2M开发板`的驱动；
2. 把 `ASR-PRO-2M开发板` 通过 typeC 数据线连接到 电脑上；
3. 打开 `天问Block` ，如果软件右上角显示 `设备ASRPRO` ，则证明连接成功；
4. 点击软件菜单栏的 **项目—打开项目(含模型)** 打开下载的 `blender_voice` ;
5. 点击软件菜单栏的 **2M编译下载** ，完成代码烧录；
6. 打开 Blender 中的 `VoiceEdit` 插件，`端口`选项中选择新增加的端口，即开启插件进行使用。

## 相关问题：
1. `pyautogui` 的作用是模拟某些按键，而且是全局作用。所以当插件开启，而 Blender 又处于后台运行时，则前台程序可能会出现类似误按键盘的问题；
2. `全选`命令已经输入，但无法运行，所以使用 `选择全部` 来代替；
3. `多选` `平移` `缩放` 是通过 `pyautogui` 模拟长按 `Shift` 键和 `Ctrl` 键来实现的，所以使用完毕后需要取消功能，否则会导致因为长按修饰键而无法正常使用系统的问题；
4. 天问语音智能模块无法中英文混合识别，因为只能使用 `红色` `蓝色` `绿色` 来代替 `x` `y` `z` 键。
