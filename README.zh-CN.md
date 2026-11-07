# LiveSubTranslate

**基于 Faster-Whisper 的中文视频英语、法语实时字幕生成实验工具**

LiveSubTranslate 是一款基于 Python 的本地语音识别与翻译实验工具，旨在为 YouTube 上的中文电影、电视剧及其他中文视频生成英文（English）或法文（Français）字幕。

用户可以在网页中输入 YouTube 视频链接、选择字幕语言，并通过 macOS 虚拟音频设备 BlackHole 2ch 采集视频播放时的系统音频。英语模式使用 Faster-Whisper 的语音翻译功能；法语模式先使用 Faster-Whisper 识别中文，再通过 NLLB-200 多语言翻译模型生成法文文本。字幕通过 Flask 网页界面自动更新。

> **项目状态：实验性原型。** 当前已经提供英语、法语两种字幕模式的程序流程，但实际输出效果仍在测试中。字幕可能存在延迟、重复、遗漏或翻译错误，尚不能保证与视频对白同步。特别是音频路由不正确时，网页即使显示“正在识别”，也可能没有字幕。

## 1. 项目简介

LiveSubTranslate 旨在为缺少英文或法文字幕的中文视频提供一种自动化辅助观看方式。

与依赖 YouTube 自带字幕的工具不同，本项目直接处理 Mac 上正在播放的声音，不要求视频预先提供中文字幕或英文字幕轨道。网页负责加载允许嵌入的视频、选择目标语言和显示翻译结果；Python 后端负责音频采集、识别与翻译。

### 主要功能

- **中文语音转英文字幕**：利用 Faster-Whisper 将普通话语音直接翻译为英文文本。
- **中文语音转法文字幕**：先识别中文语音，再使用 NLLB-200 翻译为法文文本（实验性功能）。
- **输入 YouTube 链接**：在网页中输入视频 URL 并加载允许嵌入的视频。
- **实时音频采集**：通过 BlackHole 2ch 获取 macOS 系统音频。
- **字幕自动更新**：网页定期请求后端的最新结果，无需手动刷新。
- **本地模型处理**：语音识别和翻译模型在本地 Python 环境运行；首次下载模型及播放 YouTube 视频需要网络。
- **双版本支持**：提供 `app.py` 和低延迟实验版本 `app_fast.py`。
- **可配置 Whisper 模型**：可根据计算机性能调整模型大小。

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
          |
          +---------------------------+
          |                           |
          v                           v
      英语模式                     法语模式
  中文语音直接英译              中文语音转写
                                      |
                                      v
                              NLLB-200 法语翻译
          |                           |
          +-------------+-------------+
                        |
                        v
                     Flask API
                        |
                        v
                网页显示英文/法文字幕
```

本工具不下载 YouTube 视频，也不修改或生成 YouTube 平台官方字幕轨道。字幕是本地网页显示的临时翻译结果。

## 2. 环境要求

### 操作系统

- macOS（当前主要开发和测试平台）
- 已使用 Python 3.12 环境进行开发与测试
- 建议使用 Python 3.11 或 3.12
- Windows 和 Linux 尚未提供经过验证的完整配置方案

### 软件依赖

- Python 3.11 或 3.12
- BlackHole 2ch
- Flask
- Faster-Whisper
- NumPy
- sounddevice
- Transformers、PyTorch 和 SentencePiece（法语模式所需）
- 支持 YouTube 播放的网页浏览器

Python 依赖应由项目的 `requirements.txt` 管理。**使用法语模式前，请确认当前仓库的依赖文件已包含相应的翻译模型依赖。**

首次运行时，Whisper 模型需要下载；首次使用法语模式时，NLLB-200 模型也可能需要下载。播放 YouTube 视频需要网络连接。模型下载、初始化和法语翻译可能占用较多内存与处理时间。

## 3. 安装与配置

### 3.1 安装 BlackHole

BlackHole 是 macOS 虚拟音频驱动，可将系统播放的声音传输给 Python 程序。

官方网站：https://existential.audio/blackhole/

如果已安装 Homebrew，可以在 Terminal 中执行：

```bash
brew install blackhole-2ch
```

安装后，如果音频设备没有出现，可尝试重新启动相关应用或计算机。

### 3.2 配置 macOS 音频输出

打开 macOS 的 **Audio MIDI Setup（音频 MIDI 设置）**；法语系统中通常显示为 **Configuration audio et MIDI**。

1. 点击左下角的 `+`。
2. 选择 `Create Multi-Output Device`（创建多输出设备；法语系统通常为 `Créer un périphérique à sortie multiple`）。
3. 同时勾选 `MacBook Air Speakers`（或实际使用的扬声器）和 `BlackHole 2ch`。
4. 建议将实际扬声器设为主设备，并在适用时为 BlackHole 启用漂移校正。
5. 打开 **系统设置 → 声音 → 输出**（法语系统：`Réglages Système → Son → Sortie`），选择新建的 **Multi-Output Device** 作为系统声音输出。

这样，Mac 可以在播放声音的同时将音频传输给 BlackHole。

> **注意：** `Multi-Output Device`（多输出设备）与 `Aggregate Device`（聚合设备）不是同一种设备。本项目的典型使用场景需要多输出设备。

**重要：确认 BlackHole 正在接收系统音频。** 仅安装 BlackHole，或仅在 LiveSubTranslate 网页中选择 `BlackHole 2ch`，并不代表程序已经接收到 YouTube 声音。开始识别前，请同时确认：

1. macOS 系统声音输出选择的是包含扬声器和 BlackHole 的 `Multi-Output Device`，而不是单独的 Mac 扬声器。
2. LiveSubTranslate 网页中的**音频输入**选择的是 `BlackHole 2ch`。
3. YouTube 视频正在播放有对白的片段，且浏览器、视频播放器和系统没有静音。
4. 如系统提示音频输入或麦克风权限，允许运行 Python 的 Terminal 或相关应用访问。

如果系统声音没有正确传输到 BlackHole，即使网页显示“正在识别”，Whisper 也可能无法生成字幕。具体检测方法见 **5.2 节**。

### 3.3 下载 GitHub 项目

在 Terminal 中执行：

```bash
git clone https://github.com/LATHENTIA-Technologies/LiveSubTranslate.git
cd LiveSubTranslate
```

也可以从 GitHub 下载 ZIP 压缩包，解压后进入项目目录。

> 如果你已经将项目保存在其他位置，例如 `~/Downloads/youtube_live_english_subtitles`，请进入实际项目目录，无需重复克隆。

### 3.4 创建 Python 虚拟环境

在项目目录中执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果当前 `requirements.txt` 尚未包含法语模式所需的 `transformers`、`torch` 和 `sentencepiece`，需要先补齐依赖并更新该文件，再使用法语模式。

## 4. 启动与使用

### 4.1 推荐：运行低延迟实验版本

确保已进入项目目录并激活虚拟环境，然后执行：

```bash
python app_fast.py
```

该版本采用较小的 Whisper 模型、较短的音频窗口和较低的搜索参数，旨在减少字幕生成延迟。

正常启动时，Terminal 会显示类似信息：

```text
 * Running on http://127.0.0.1:8765
Press CTRL+C to quit
```

请保持此 Terminal 窗口打开。首次启动模型可能需要等待下载和加载。

### 4.2 运行原始版本

如需测试原始版本，可以在**停止正在运行的服务器后**执行：

```bash
python app.py
```

原始版本使用较大的默认模型和较长的音频窗口，可能需要更多处理时间。两个版本如果使用同一个端口 `8765`，请勿同时启动。

### 4.3 打开网页并生成字幕

程序启动后，在浏览器中访问：

http://127.0.0.1:8765

按以下顺序操作：

1. 在网页的 YouTube 链接输入框中粘贴视频 URL，点击**加载视频**。
2. 在字幕语言选项中选择 `English`（英语）或 `Français`（法语）。
3. 在音频输入设备列表中选择 `BlackHole 2ch`。
4. 确认 macOS 系统声音输出已设置为 `Multi-Output Device`。
5. 点击**开始字幕**，并播放有中文对白的视频。
6. 等待程序采集音频、识别语音并生成所选语言的字幕。

字幕会在网页中自动更新，不需要不断刷新网页，也不需要反复执行 Terminal 命令。

如需停止识别，点击网页中的**停止**。关闭 Flask 服务器时，在运行程序的 Terminal 中按：

```text
Control + C
```

> **提示：** 如果网页显示“正在识别”但长时间没有字幕，请先检查 BlackHole 音频输入，不要反复点击“开始字幕”。

### 4.4 Whisper 模型配置

项目支持通过环境变量选择 Whisper 模型。例如：

```bash
WHISPER_MODEL=tiny python app_fast.py
```

或使用 `base` 模型：

```bash
WHISPER_MODEL=base python app_fast.py
```

较小的模型通常速度更快，但可能降低复杂对白、口音和背景噪声条件下的识别与翻译质量。法语模式还需要额外的 NLLB-200 翻译步骤，因此总体延迟可能更高。

### 4.5 原始版与优化版对比

| 配置 | `app.py` | `app_fast.py` |
|---|---|---|
| 默认 Whisper 模型 | `small` | `base` |
| 音频窗口 | 7 秒 | 4 秒 |
| 识别尝试间隔 | 5 秒 | 2 秒 |
| Beam size | 3 | 1 |
| 计算设备 | CPU | CPU |
| 计算精度 | `int8` | `int8` |

以上为当前项目所采用的实验配置；具体行为以实际运行的代码和环境变量为准。

优化版还可尝试通过环境变量调整部分音频参数：

```bash
WINDOW_SECONDS=4 STEP_SECONDS=2 python app_fast.py
```

**重要说明：2 秒的识别间隔不等于 2 秒的实际字幕延迟。** 最终延迟还受到 CPU 性能、模型加载与推理时间、音频缓冲、对白复杂度和法语翻译步骤等因素影响。

## 5. 常见问题

### 5.1 找不到 BlackHole 2ch

请确认：

- BlackHole 已正确安装。
- macOS 的音频 MIDI 设置中可以看到该设备。
- 已重新启动 Python 程序。
- 已点击网页中的**刷新设备**。
- 如有必要，检查系统权限并重新启动相关应用。

### 5.2 网页没有显示英文或法文字幕

首先确认中文视频正在播放有声音的片段；检查 macOS 系统输出是否为包含 BlackHole 的多输出设备，并确认网页的音频输入为 `BlackHole 2ch`，已选择目标语言并点击**开始字幕**。

如果 macOS 提示麦克风或音频输入权限，请允许相关应用访问。

#### 检查 BlackHole 是否接收到音频

保持 YouTube 视频播放且没有静音。在**另一个 Terminal 窗口**中进入项目目录、激活虚拟环境，再运行以下测试；原来的 Flask 服务器可以保持运行。

```bash
python - <<'PY'
import sounddevice as sd
import numpy as np

for i, d in enumerate(sd.query_devices()):
    if "BlackHole" in d["name"] and d["max_input_channels"] > 0:
        print("Testing:", d["name"])
        audio = sd.rec(
            5 * 16000,
            samplerate=16000,
            channels=1,
            device=i,
            dtype="float32"
        )
        sd.wait()
        rms = np.sqrt(np.mean(audio ** 2))
        print("Audio RMS:", round(float(rms), 6))
        break
else:
    print("BlackHole input not found")
PY
```

**结果说明：**

- `Audio RMS: 0.0`：测试期间没有检测到音频信号。如果视频正在播放有声音的片段，应优先检查 macOS 的声音输出路由。
- `Audio RMS` 明显大于零：BlackHole 检测到了音频信号；如果仍无字幕，应继续检查 Whisper 的识别过程。
- `BlackHole input not found`：程序未找到 BlackHole 输入设备，需要检查安装和设备配置。

RMS 是音频信号强度的参考指标，并不直接代表语音识别质量。请尽量在持续有人说话的片段进行测试。

#### 检查 Flask API 状态

如果 BlackHole 已有音频输入，但字幕仍未出现，可在另一个 Terminal 中执行：

```bash
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
```

注意：`running: true` 仅表示识别任务处于运行状态，不代表字幕已经成功生成。如果 `latest` 长时间为 `null`、`seq` 始终为 `0`，说明还没有产生字幕结果。还应检查运行 `app_fast.py` 的 Terminal 中是否有模型加载、音频采集、识别耗时或错误日志。

### 5.3 英文或法文字幕更新非常慢

建议优先运行：

```bash
python app_fast.py
```

如果仍然较慢，可以尝试：

```bash
WHISPER_MODEL=tiny python app_fast.py
```

低延迟版本可在 Terminal 中输出识别耗时，便于判断性能瓶颈。法语模式还需经过 NLLB-200 翻译，可能比英文模式慢。模型首次加载也可能需要额外时间。

### 5.4 如何检查程序是否正常识别？

保持程序运行，在另一个 Terminal 中执行：

```bash
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
```

成功生成字幕时，返回信息可能包含以下字段（仅为示例）：

```json
{
  "running": true,
  "error": "",
  "language": "en",
  "latest": {
    "seq": 6,
    "text": "Where are you going?"
  },
  "seq": 6
}
```

其中：

- `running`：识别任务是否处于运行状态。
- `error`：后端报告的错误信息。
- `language`：当前目标字幕语言，例如 `en` 或 `fr`。
- `latest.text`：最近一次生成的字幕文本。
- `seq`：字幕更新序号。

如果 `seq` 随着有对白的播放持续增加，通常表示后台正在生成新字幕。`running: true` 本身不保证字幕正常更新。

### 5.5 YouTube 视频无法嵌入播放

部分 YouTube 视频不允许在第三方网页中嵌入播放。

可以尝试在另一个浏览器标签页中播放有权访问的视频，并通过 BlackHole 采集系统音频。但此时字幕仍显示在 LiveSubTranslate 的本地网页中，**不会自动覆盖到另一个 YouTube 标签页上**。

### 5.6 如何更换 YouTube 视频？

新版网页支持直接输入 YouTube 链接：

1. 在视频链接输入框中粘贴新的 YouTube URL。
2. 点击**加载视频**。
3. 等待视频加载完成。
4. 选择字幕语言，确认音频设备并开始识别。

无需手动修改 `templates/index.html` 中的 iframe 地址。部分视频可能因嵌入权限或浏览器限制而无法加载。

### 5.7 端口 8765 已被占用

如果启动时出现：

```text
Address already in use
Port 8765 is in use by another program.
```

通常表示已有一个 Flask 服务器正在运行。先回到原来的 Terminal，按 `Control + C` 停止旧服务器，再运行新版本。

也可以使用以下命令查看监听端口的进程：

```bash
lsof -nP -iTCP:8765 -sTCP:LISTEN
```

确认该进程确实是此前启动的 LiveSubTranslate 后，再决定是否停止它。不要在同一个端口同时启动 `app.py` 和 `app_fast.py`。

## 6. 已知限制

LiveSubTranslate 目前仍属于实验性软件，存在以下限制。

**字幕延迟**

语音识别和翻译在本地运行，字幕可能明显落后于视频对白，尚不能保证严格的实时同步。法语模式由于增加翻译步骤，可能产生额外延迟。

**翻译准确性**

背景音乐、多人同时说话、口音、方言、成语和文化负载表达都可能影响识别和翻译质量。

**字幕重复与遗漏**

由于采用滑动音频窗口处理方式，部分语音可能被重复识别，也可能出现漏句。

**语言支持**

当前程序面向普通话语音，提供英文和法文两种目标字幕模式。英文通过 Faster-Whisper 直接翻译；法文通过中文转写与 NLLB-200 翻译生成。两种模式仍需持续测试，不能保证所有视频均可成功生成字幕。

**音频路由依赖**

macOS 必须将视频声音正确输出到 BlackHole。仅启动识别线程或在网页中选择 BlackHole 并不意味着已捕获到音频。

**YouTube 嵌入限制**

部分视频可能不允许在本地网页中嵌入播放。此限制由视频及平台的播放设置决定。

**平台兼容性**

当前说明主要针对 macOS 和 BlackHole。Windows 与 Linux 尚无经过验证的配置方案。

**本地服务**

项目使用 Flask 开发服务器，适合本地实验，不应直接暴露到公共互联网。

**版权与隐私**

用户应确保有权访问和处理相关音频，并遵守适用法律及平台服务条款。仓库不应包含受版权保护的电影片段、私人录音、访问令牌或其他敏感数据。

## 7. 后续开发方向

未来可以考虑：

- 优化 YouTube 链接解析及嵌入播放兼容性。
- 改善 BlackHole 音频配置引导和自动诊断。
- 优化语音分段、字幕去重和延迟控制。
- 改进中文到法语的翻译质量与处理速度。
- 实现带时间戳的字幕及更精确的同步机制。
- 支持 SRT 和 VTT 字幕导出。
- 建立字幕延迟、语音识别和翻译质量的评估方法。
- 探索更多目标语言。
- 改善 Windows 和 Linux 的兼容性。

## 8. License（许可证）

本项目的开源许可证以 GitHub 仓库根目录中的 `LICENSE` 文件为准。

如果仓库采用 **MIT License**，其他开发者可在遵守许可证条件的前提下使用、修改、复制和分发项目代码。MIT 许可证要求保留相应的版权声明和许可证文本。

本项目使用的第三方依赖，包括 Faster-Whisper、Flask、BlackHole、Transformers 和 NLLB-200 模型等，仍受各自许可证及使用条款约束。

> 在正式添加 MIT 许可证文件之前，不应将本项目声明为已经采用 MIT 许可证。

---

**LiveSubTranslate — Experimental Open-Source Prototype**

基于 Python、Faster-Whisper、NLLB-200、BlackHole 和 Flask 的中文语音英法双语字幕实验工具。
