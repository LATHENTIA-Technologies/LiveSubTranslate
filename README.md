# LiveSubTranslate

**基于 Faster-Whisper 的 YouTube 中文语音实时英译字幕工具**

[English](README.md) | 简体中文

> **项目状态：实验性原型（Experimental Prototype）**
>
> LiveSubTranslate 是一款基于 Python 的本地语音翻译工具，可将中文视频中的普通话语音自动翻译为英文，并通过网页界面显示字幕。
>
> 本项目目前仍处于实验阶段。字幕可能存在延迟、遗漏、重复或翻译错误，尚不能保证与视频对白精确同步。

## 1. 项目简介

LiveSubTranslate 旨在为没有英文字幕的中文视频提供一种自动化的辅助观看方式。

该工具通过 macOS 虚拟音频设备 BlackHole 采集系统正在播放的音频，利用 Faster-Whisper 进行中文语音识别与英文翻译，并通过 Flask 网页界面动态显示生成的英文字幕。

与依赖 YouTube 自带字幕的工具不同，LiveSubTranslate 直接处理本地播放的声音，因此不要求视频预先提供中文字幕或英文字幕轨道。

### 主要功能

- **中文语音自动英译**：利用 Faster-Whisper 将普通话语音直接翻译为英文文本。
- **实时音频采集**：通过 BlackHole 2ch 获取 macOS 系统音频。
- **自动字幕更新**：网页定期获取最新翻译结果，无需手动刷新。
- **本地运行**：语音识别与翻译在本地 Python 环境中完成。
- **双版本支持**：提供原始版本与低延迟实验版本。
- **可配置模型**：支持根据计算机性能调整 Whisper 模型大小。

### 技术架构

```text
YouTube 视频 / 中文原声
          |
          v
macOS Multi-Output Device
          |
          v
BlackHole 2ch
          |
          v
Python + sounddevice + NumPy
          |
          v
Faster-Whisper
中文语音识别 + 英文翻译
          |
          v
Flask API
          |
          v
网页自动显示英文字幕
```

本工具不会下载 YouTube 视频，也不会提取、修改或生成 YouTube 官方字幕轨道。

## 2. 环境要求

### 操作系统

- macOS
- 已测试的 Python 环境：Python 3.12
- 建议使用 Python 3.11 或 3.12
- 其他操作系统尚未经过完整测试

### 软件依赖

- Python 3.11 或 3.12
- BlackHole 2ch
- Flask
- Faster-Whisper
- NumPy
- sounddevice
- 支持 YouTube 播放的网页浏览器

Python依赖由 `requirements.txt` 管理。

首次运行时，需要网络连接下载 Whisper 模型。播放 YouTube 视频也需要网络连接。

## 3. 安装与配置

### 3.1 安装 BlackHole

BlackHole 是 macOS 的虚拟音频驱动，用于将系统播放的声音传输给 Python 程序。

官方网站：

https://existential.audio/blackhole/

如果已经安装 Homebrew，可以在 Terminal 中执行：

```bash
brew install blackhole-2ch
```

安装后，如设备未出现，可重新启动相关应用或计算机。

### 3.2 配置 macOS 音频输出

打开 macOS：

**Audio MIDI Setup（音频 MIDI 设置）**

法语系统中的名称为：

**Configuration audio et MIDI**

按照以下步骤操作：

1. 点击左下角的 `+`。
2. 选择 `Create Multi-Output Device`（创建多输出设备）。
3. 勾选 `MacBook Air Speakers`（或实际使用的扬声器）和 `BlackHole 2ch`。
4. 将新建的多输出设备设置为 macOS 系统声音输出。

这样可以在正常听到视频声音的同时，将音频传输给 BlackHole。

**注意：Multi-Output Device（多输出设备）与 Aggregate Device（聚合设备）不是同一种设备。**

### 3.3 下载 GitHub 项目

打开 Terminal，执行：

```bash
git clone https://github.com/LATHENTIA-Technologies/LiveSubTranslate.git
cd LiveSubTranslate
```

也可以从 GitHub 下载 ZIP 压缩包，解压后进入对应文件夹。

### 3.4 创建 Python 虚拟环境

在项目目录中执行：

```bash
python3 -m venv .venv
```

激活虚拟环境：

```bash
source .venv/bin/activate
```

升级 pip：

```bash
python -m pip install --upgrade pip
```

安装依赖：

```bash
python -m pip install -r requirements.txt
```

安装成功后，即可启动程序。

## 4. 启动与使用

### 4.1 推荐：运行低延迟实验版本

```bash
python app_fast.py
```

该版本采用较小的 Whisper 模型、较短的音频窗口和较低的搜索参数，旨在减少字幕生成延迟。

### 4.2 运行原始版本

```bash
python app.py
```

原始版本使用较大的默认模型和较长的音频窗口，可能需要更多处理时间。

### 4.3 打开网页

程序启动后，在浏览器中访问：

http://127.0.0.1:8765

然后：

1. 在音频输入设备列表中选择 `BlackHole 2ch`。
2. 点击「开始英文字幕」。
3. 播放中文视频。
4. 等待程序识别声音并生成英文翻译。
5. 英文字幕会在网页中自动更新。

不需要不断刷新网页，也不需要反复执行 Terminal 命令。

停止字幕识别时，点击「停止」。

关闭服务器时，在运行程序的 Terminal 中按：

```text
Control + C
```

### 4.4 Whisper 模型配置

项目支持通过环境变量选择模型。

例如，使用更小的模型：

```bash
WHISPER_MODEL=tiny python app_fast.py
```

使用 `base` 模型：

```bash
WHISPER_MODEL=base python app_fast.py
```

较小的模型通常计算速度更快，但可能降低复杂对白、口音和背景噪声条件下的识别与翻译质量。

### 4.5 原始版与优化版对比

| 配置 | app.py | app_fast.py |
|---|---|---|
| 默认模型 | small | base |
| 音频窗口 | 7秒 | 4秒 |
| 识别尝试间隔 | 5秒 | 2秒 |
| Beam size | 3 | 1 |
| 计算设备 | CPU | CPU |
| 计算精度 | int8 | int8 |

优化版还可以通过环境变量调整部分音频参数：

```bash
WINDOW_SECONDS=4 STEP_SECONDS=2 python app_fast.py
```

**重要说明：2秒的识别间隔不等于2秒的实际字幕延迟。** 最终延迟还受到CPU性能、模型推理时间、音频缓冲和对白复杂度等因素影响。

## 5. 常见问题

### 5.1 找不到 BlackHole 2ch

请确认：

- BlackHole已经正确安装。
- macOS能够识别该音频设备。
- 已重新启动Python程序。
- 已点击网页中的「刷新设备」。

### 5.2 网页没有显示英文字幕

首先确认中文视频正在正常播放，并检查macOS系统输出是否设置为包含BlackHole的多输出设备。

然后确认网页中的音频输入选择了 `BlackHole 2ch`，并且已经点击「开始英文字幕」。

如果macOS提示麦克风或音频输入权限，请允许相关应用访问。

### 5.3 英文字幕更新非常慢

建议优先运行：

```bash
python app_fast.py
```

如果仍然较慢，可以尝试：

```bash
WHISPER_MODEL=tiny python app_fast.py
```

低延迟版本会在Terminal中输出识别耗时，便于判断瓶颈是否来自模型推理。

### 5.4 如何检查程序是否正常识别？

保持程序运行，另外打开一个Terminal窗口：

```bash
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
```

返回信息可能包含：

```json
{
  "running": true,
  "error": "",
  "latest": {
    "seq": 6,
    "text": "Where are you going?"
  },
  "seq": 6
}
```

其中：

- `running`：程序是否处于运行状态。
- `error`：程序报告的错误信息。
- `latest.text`：最近一次生成的英文翻译。
- `seq`：字幕内容更新序号。

如果 `seq` 持续增加，说明后台正在产生新的字幕内容。

需要注意，`running: true` 并不意味着字幕一定正在正常更新。

### 5.5 YouTube视频无法嵌入播放

部分YouTube视频禁止第三方网页嵌入。

可以尝试在另一个浏览器标签页中播放有权访问的视频，并通过BlackHole采集音频。

但此时英文字幕仍显示在本地网页中，不会自动覆盖到另一个YouTube标签页上。

### 5.6 如何更换YouTube视频？

当前实验版本的 `templates/index.html` 包含预设的YouTube嵌入地址。

可以修改其中的iframe `src`，替换为允许嵌入的视频地址。

目前尚未实现通过网页输入YouTube链接的功能。

## 6. 已知限制

LiveSubTranslate目前仍属于实验性软件，存在以下限制。

**字幕延迟**

语音识别和翻译在CPU上运行，生成的字幕可能明显落后于视频对白，尚不能保证严格的实时同步。

**翻译准确性**

电影中的背景音乐、多人同时说话、口音、方言、成语和文化负载表达可能影响翻译质量。

**字幕重复与遗漏**

由于采用音频窗口处理方式，部分语音可能被重复识别，也可能出现漏句。

**语言支持**

当前版本主要支持普通话语音到英文文本的直接翻译。其他目标语言尚未实现。

**平台兼容性**

当前安装说明主要针对macOS与BlackHole。Windows和Linux尚未提供经过验证的配置方案。

**本地服务**

项目使用Flask开发服务器，适合本地测试，不应直接暴露到公共互联网。

**版权与隐私**

用户应确保有权访问和处理相关音频，并遵守适用法律及平台服务条款。

本仓库不应包含受版权保护的电影片段、私人录音、访问令牌或其他敏感数据。

## 7. 后续开发方向

未来可以考虑：

- 支持用户直接输入YouTube视频链接。
- 优化语音分段和字幕去重。
- 实现带时间戳的字幕。
- 支持SRT和VTT字幕导出。
- 建立字幕延迟与翻译质量评估方法。
- 增加中文到法语等其他目标语言的翻译功能。
- 改善不同操作系统的兼容性。

## 8. License（许可证）

本项目的开源许可证以GitHub仓库根目录中的 `LICENSE` 文件为准。

如果仓库采用 **MIT License**，则允许其他开发者在遵守许可证条件的前提下使用、修改、复制和分发本项目代码。

MIT许可证通常要求保留原有版权声明和许可证文本。

本项目使用的第三方依赖，包括 Faster-Whisper、Flask、BlackHole 等，仍受各自许可证约束。

**注意：** 在正式添加MIT许可证文件之前，不应将本项目声明为已经采用MIT许可证。

---

**LiveSubTranslate — Experimental Open-Source Prototype**

基于Python、Faster-Whisper、BlackHole和Flask的中文语音实时英译字幕实验工具。
