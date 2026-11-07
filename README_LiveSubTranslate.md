# LiveSubTranslate

**Experimental local Chinese-to-English and Chinese-to-French subtitle overlay for YouTube videos on macOS.**

LiveSubTranslate is an experimental Python-based application that generates English or French subtitles from spoken Mandarin in Chinese movies, TV series, and other YouTube videos.

Users can enter their own YouTube video URL, select the desired subtitle language (English or French), and display automatically generated subtitles over an embedded YouTube player.

The application uses Faster-Whisper for speech recognition and direct English translation, and an additional multilingual translation model (NLLB-200) for French translation. Audio is captured locally through BlackHole 2ch on macOS.

> **Status: Experimental prototype.** Subtitles may be delayed, incomplete, duplicated, or inaccurate. Real-time synchronization is not guaranteed.

## Features

- Local speech translation from Mandarin audio to English text using Whisper's `task="translate"`.
- Audio capture through [BlackHole 2ch](https://existential.audio/blackhole/) on macOS.
- Web interface for selecting an audio input and starting/stopping recognition.
- Subtitle overlay that polls the local Flask server for updates automatically—no manual page refresh is needed.
- Two back-end configurations: original (`app.py`) and faster experimental settings (`app_fast.py`).

## Requirements

- macOS with Python 3.11 or 3.12 (other versions have not been tested here).
- [Homebrew](https://brew.sh/) (optional, for installing BlackHole).
- BlackHole 2ch virtual audio driver.
- Internet access for the initial Whisper model download and YouTube playback.
- A video you are authorized to access and process.

## Installation

### 1. Install and configure BlackHole

If you use Homebrew:

```bash
brew install blackhole-2ch
```

Open **Audio MIDI Setup** (in French: **Configuration audio et MIDI**). Click **+** and create a **Multi-Output Device** (*Périphérique à sorties multiples*). Enable both your Mac speakers (or suitable headphones) and **BlackHole 2ch**. Select this Multi-Output Device as the macOS sound output. This lets you hear the audio while routing a copy to BlackHole.

> A **Multi-Output Device** is not the same as an **Aggregate Device** (*Périphérique agrégé*).

### 2. Clone and install Python dependencies

```bash
git clone https://github.com/LATHENTIA-Technologies/LiveSubTranslate.git
cd LiveSubTranslate
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you downloaded the repository as a ZIP instead, extract it, open Terminal, and `cd` into the extracted directory before creating the virtual environment.

### 3. Run the application

**Recommended for a first speed test:**

```bash
python app_fast.py
```

**Original configuration:**

```bash
python app.py
```

Open **http://127.0.0.1:8765** in your browser. Select **BlackHole 2ch** in the audio input menu, click **Start English Subtitles** (the current interface labels this button in Chinese: `开始英文字幕`), and play the video. Keep the Terminal process running.

To stop the server, press **Ctrl+C** in Terminal.

## How it works

```text
YouTube / system audio
        |
        v
macOS Multi-Output Device
        |
        v
BlackHole 2ch (audio input)
        |
        v
sounddevice + NumPy audio buffer
        |
        v
faster-whisper (Mandarin speech -> English translation)
        |
        v
Flask /api/status
        |
        v
Browser subtitle overlay (automatic polling)
```

The application does not extract subtitle files from YouTube, download the video, or modify the YouTube player itself. It processes audio made available through the selected local input device.

## Models and performance

The two scripts have different default settings:

| Setting | `app.py` | `app_fast.py` |
| --- | --- | --- |
| Default Whisper model | `small` | `base` |
| Audio window | 7 s | 4 s |
| Minimum time between processing attempts | 5 s | 2 s |
| Beam size | 3 | 1 |
| CPU compute type | `int8` | `int8` |

To choose a smaller model for faster but potentially less accurate results:

```bash
WHISPER_MODEL=tiny python app_fast.py
```

Or use the `base` model explicitly:

```bash
WHISPER_MODEL=base python app_fast.py
```

The faster script also supports adjusting its audio window and processing interval:

```bash
WINDOW_SECONDS=4 STEP_SECONDS=2 python app_fast.py
```

**Important:** A 2-second processing interval is *not* a promise of 2-second subtitle latency. CPU inference time, buffering, silence detection, audio routing, and playback all affect the actual delay. The scripts process audio serially and may skip or repeat speech. `app_fast.py` prints the measured transcription time in Terminal for troubleshooting.

## Troubleshooting

**BlackHole is missing from the input list:** Confirm that BlackHole is installed, restart the application, and use **Refresh Devices** (`刷新设备`).

**No English subtitles:** Confirm that the video is playing, macOS output is set to the Multi-Output Device, **BlackHole 2ch** is selected as the app input, and the app has microphone/audio-input permission in macOS privacy settings if prompted.

**Subtitles are very slow:** Try `python app_fast.py` or `WHISPER_MODEL=tiny python app_fast.py`. Check the `Transcription ...s` timing printed in Terminal. Smaller models may reduce accuracy.

**Check the current recognition state:** With the app running, open another Terminal window and run:

```bash
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
```

The `latest.text` field is the most recent English translation; `seq` increments when the stored subtitle text changes. `running: true` alone does not prove that recognition is progressing.

**YouTube embed does not work:** Some videos prohibit embedding. You can play authorized audio in a separate browser tab and keep the local subtitle page open, but the overlay will remain on the local page rather than over the external YouTube tab.

**A different video is needed:** The current prototype's `templates/index.html` contains a **hard-coded YouTube embed URL**. Change the iframe `src` to an embeddable video URL you are authorized to use. A user-editable URL field is not implemented yet.

## Project layout

```text
LiveSubTranslate/
├── app.py                # Original backend
├── app_fast.py           # Experimental lower-latency backend
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html        # Browser interface and subtitle overlay
├── README.md
├── .gitignore
└── LICENSE               # Add if you choose an open-source license
```

## Limitations and responsible use

- Mandarin-to-English translation only; Whisper's `translate` task does not directly provide arbitrary target languages.
- CPU-based transcription may lag substantially behind live dialogue.
- Overlapping windows can produce repeated or omitted phrases; subtitle timing is approximate.
- Movie dialogue, background music, accents, and idiomatic language can reduce translation quality.
- macOS + BlackHole is the currently documented setup; Windows and Linux are not supported by these instructions.
- The app is intended for local development, not for exposing Flask's development server to the public internet.
- Respect copyright, applicable law, platform terms, and the privacy of any audio you process. Do not include copyrighted movie clips, private recordings, API tokens, or virtual environments in the repository.

## Possible future improvements

- User-editable YouTube URL.
- Better speech segmentation and deduplication.
- Timestamped subtitles and export to SRT/VTT.
- Latency and translation-quality benchmarks.
- Optional translation into languages other than English.

## License

Choose and add a license file (for example, MIT) before describing the repository as MIT-licensed. Third-party dependencies retain their own licenses.
