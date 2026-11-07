# Mac YouTube 中文原声 → 实时英文字幕

## 重要限制
- 这个程序不下载或绕过 YouTube 视频保护。只识别你通过 macOS 音频设备合法播放并路由的声音。
- Whisper `task=translate` 将中文语音直接翻译为英语；它不是先生成中文字幕再逐句翻译。
- 每约 5 秒处理最近 7 秒音频，结果可能延迟，重复或漏句。CPU 速度不足时延迟更大。
- Mac 的 BlackHole 虚拟音频设备是独立安装的；本项目不包含它。
- 仅在你有权播放、处理相应音频的前提下使用，并遵守 YouTube 服务条款。

## 第一步：安装 Python 和 BlackHole
建议 Mac 上已安装 Python 3.11 或 3.12；检查 `python3 --version`。
在 https://existential.audio/blackhole/ 安装 **BlackHole 2ch**。可使用 Homebrew（若已安装）：

```bash
brew install blackhole-2ch
```

打开 **Audio MIDI Setup（音频 MIDI 设置）**，点左下角 `+` → **Create Multi-Output Device**，同时勾选 Mac 扬声器/耳机和 BlackHole 2ch。将 Mac 系统声音输出设为这个 Multi-Output Device。请注意耳机蓝牙设备可能造成同步问题。

## 第二步：安装依赖
在 Terminal 中：

```bash
cd ~/Downloads/youtube_live_english_subtitles
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果文件解压在其他位置，把 `cd` 后路径改为实际路径。

## 第三步：启动

```bash
python app.py
```

首次运行会下载 Whisper small 模型（需要网络）。然后打开：

http://127.0.0.1:8765

在音频输入下拉框选择 **BlackHole 2ch**，点击 **开始英文字幕**，再播放视频。若无声音，检查 macOS 声音输出是否指向 Multi-Output Device，并在 **系统设置 → 隐私与安全性 → 麦克风** 允许 Terminal/Python 使用音频输入（若弹出授权）。

## 常见问题
- **设备列表没有 BlackHole**：重新安装并重启相关应用，再点“刷新设备”。
- **无字幕**：确认音频正在播放、BlackHole 有输入音量，且已按“开始英文字幕”。
- **翻译很慢**：将模型设为 `tiny` 或 `base`，如 `WHISPER_MODEL=base python app.py`（更快但准确率下降）。
- **嵌入播放器不可用**：可能是视频上传者禁用了嵌入。可在另一标签页正常播放 YouTube，当前网页仍能显示英文字幕，但不会直接覆盖另一标签页。
- **Firefox**：不依赖 Firefox 标签页音频捕获API；通过 Mac 音频路由工作。
- **声音重复**：调整多输出设备，避免同时开启重复的监听输出。
