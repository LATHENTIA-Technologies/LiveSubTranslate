# LiveSubTranslate

**Experimental English and French subtitle generation for Mandarin-language YouTube videos using Faster-Whisper.**

LiveSubTranslate is a local Python-based speech recognition and translation prototype designed to generate English or French subtitles for Chinese movies, TV series, and other YouTube videos containing spoken Mandarin.

Users can paste a YouTube URL into the web interface, choose **English** or **Français**, and view automatically updated subtitle text over an embedded YouTube player. On macOS, the application captures playback audio through **BlackHole 2ch**. English mode uses Faster-Whisper's speech translation capability; French mode transcribes Mandarin with Faster-Whisper and translates the recognized text using **NLLB-200**. A local Flask server supplies subtitle updates to the browser.

> **Status: Experimental prototype.** Both English and French processing paths are implemented in the current prototype, but end-to-end subtitle output is still being tested. Subtitles may be delayed, duplicated, omitted, or inaccurate; synchronization with dialogue is not guaranteed. If system audio is not routed to BlackHole correctly, the interface may indicate that recognition is running without producing subtitles.

## 1. Project overview

LiveSubTranslate aims to make Mandarin-language videos more accessible when English or French subtitles are unavailable.

Unlike tools that rely on YouTube's existing caption tracks, LiveSubTranslate processes audio playing locally on the Mac. The video therefore does not need an existing Chinese or translated caption track. The browser interface loads embeddable videos, selects the target language, and displays the resulting text; the Python backend captures audio, performs speech recognition, and handles translation.

### Key features

- **Mandarin-to-English subtitles:** Direct speech translation with Faster-Whisper.
- **Mandarin-to-French subtitles:** Mandarin transcription followed by NLLB-200 translation (experimental).
- **User-entered YouTube URLs:** Load an embeddable video through the web interface without editing HTML.
- **System-audio capture:** Receive macOS playback audio through BlackHole 2ch.
- **Automatic subtitle updates:** The browser polls the Flask API; no manual refresh is required.
- **Local model inference:** Speech recognition and translation run in the local Python environment; internet access is needed to download models initially and to stream YouTube videos.
- **Two backend configurations:** `app.py` and the lower-latency experimental version `app_fast.py`.
- **Configurable Whisper model:** Adjust model size to suit the computer's performance.

### Technical architecture

```text
YouTube video / Mandarin audio
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
       +-----+-------------------+
       |                         |
       v                         v
  English mode               French mode
Direct speech-to-English    Mandarin transcription
       |                         |
       |                         v
       |                 NLLB-200 translation
       |                         |
       +------------+------------+
                    |
                    v
                 Flask API
                    |
                    v
       Browser English/French subtitle overlay
```

The application does **not** download YouTube videos or extract, alter, or create official YouTube caption tracks. Its subtitles are temporary translation results displayed in the local web interface.

## 2. Requirements

### Operating system

- macOS (primary development and testing platform).
- Developed and tested in a Python 3.12 environment; Python 3.11 or 3.12 is recommended.
- No fully validated setup is currently documented for Windows or Linux.

### Software dependencies

- Python 3.11 or 3.12.
- [BlackHole 2ch](https://existential.audio/blackhole/).
- Flask, Faster-Whisper, NumPy, and `sounddevice`.
- `transformers`, PyTorch (`torch`), and `sentencepiece` for French mode.
- A browser capable of playing YouTube videos.

Python packages should be managed through the project's `requirements.txt`. **Before using French mode, verify that the checked-out version of `requirements.txt` includes its translation dependencies.**

The Whisper model may need to be downloaded on first use; French mode may additionally download an NLLB-200 model. Model downloads, initialization, and French translation can require substantial memory and processing time. YouTube playback requires an internet connection.

## 3. Installation and configuration

### 3.1 Install BlackHole

BlackHole is a virtual macOS audio driver that allows Python to capture audio routed from system playback.

Official website: https://existential.audio/blackhole/

If you use Homebrew, run:

```bash
brew install blackhole-2ch
```

If the device does not appear after installation, restart the relevant applications or your Mac.

### 3.2 Configure macOS audio output

Open **Audio MIDI Setup** (called **Configuration audio et MIDI** on French-language macOS).

1. Click the `+` button in the lower-left corner.
2. Select **Create Multi-Output Device** (French: **Créer un périphérique à sortie multiple**).
3. Enable both your **Mac speakers** (or your actual playback device) and **BlackHole 2ch**.
4. Prefer the physical playback device as the master device, and enable drift correction for BlackHole where applicable.
5. Go to **System Settings → Sound → Output** (French: **Réglages Système → Son → Sortie**) and select the newly created **Multi-Output Device** as the Mac's sound output.

This configuration lets you hear the video while also sending audio to BlackHole.

> **Important:** A **Multi-Output Device** is not the same as an **Aggregate Device**. The usual setup for this project requires a Multi-Output Device.

**Make sure BlackHole is actually receiving system audio.** Installing BlackHole, or selecting it in LiveSubTranslate, does not by itself route YouTube audio to the application. Before starting recognition, check all of the following:

1. The Mac's **system output** is the Multi-Output Device containing both the speakers and BlackHole—not the speakers alone.
2. The LiveSubTranslate **audio input** is set to **BlackHole 2ch**.
3. The YouTube video is playing a passage with audible dialogue; neither the browser, video, nor system audio is muted.
4. If macOS requests microphone or audio-input permission, grant it to the Terminal or application running Python.

If audio is not routed to BlackHole, Whisper may produce no subtitles even when the page says recognition is running. See **Section 5.2** for an audio-level test.

### 3.3 Download the GitHub project

In Terminal, run:

```bash
git clone https://github.com/LATHENTIA-Technologies/LiveSubTranslate.git
cd LiveSubTranslate
```

Alternatively, download and extract the repository ZIP file and open that directory in Terminal.

> If you already have a local project directory, such as `~/Downloads/youtube_live_english_subtitles`, enter that directory instead; there is no need to clone it again.

### 3.4 Create a Python virtual environment

From the project directory, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the current `requirements.txt` does not yet list `transformers`, `torch`, and `sentencepiece`, add and install those dependencies before using French mode, and update the dependency file accordingly.

## 4. Running and using the application

### 4.1 Recommended: lower-latency experimental backend

With the project directory open and the virtual environment activated, run:

```bash
python app_fast.py
```

This configuration uses a smaller Whisper model, a shorter audio window, and reduced search settings to help lower processing delay.

A successful server start should display something similar to:

```text
 * Running on http://127.0.0.1:8765
Press CTRL+C to quit
```

Keep this Terminal window open. Initial model downloads and loading may take additional time.

### 4.2 Original backend

To test the original configuration, **stop the running server first**, then run:

```bash
python app.py
```

The original configuration uses a larger default Whisper model and longer audio windows. Do not run both backends on port `8765` at the same time.

### 4.3 Open the web interface and generate subtitles

Open http://127.0.0.1:8765 in your browser, then:

1. Paste a YouTube video URL into the input field and click **Load Video** (the displayed button may be in Chinese).
2. Choose **English** or **Français** as the subtitle language.
3. Select **BlackHole 2ch** from the audio input list.
4. Verify that macOS sound output is set to the **Multi-Output Device**.
5. Click **Start Subtitles** and play a video with spoken Mandarin.
6. Allow time for audio capture, recognition, and translation to produce subtitle text.

The overlay updates automatically without manually refreshing the page. Click **Stop** in the interface to stop recognition. To shut down Flask, press the following in the Terminal running the server:

```text
Control + C
```

> **Tip:** If the interface says recognition is running but no subtitles appear, check BlackHole audio routing first instead of repeatedly clicking Start.

### 4.4 Whisper model configuration

Choose a smaller model using an environment variable:

```bash
WHISPER_MODEL=tiny python app_fast.py
```

Or explicitly choose `base`:

```bash
WHISPER_MODEL=base python app_fast.py
```

Smaller models are generally faster but may be less accurate with complex dialogue, accents, or background noise. French mode adds an NLLB-200 translation stage and may have greater total latency.

### 4.5 Original versus faster configuration

| Setting | `app.py` | `app_fast.py` |
|---|---|---|
| Default Whisper model | `small` | `base` |
| Audio window | 7 s | 4 s |
| Interval between processing attempts | 5 s | 2 s |
| Beam size | 3 | 1 |
| Compute device | CPU | CPU |
| Compute type | `int8` | `int8` |

These are the prototype's intended experimental settings; actual behavior depends on the checked-out code and any environment-variable overrides.

The faster version may also allow adjustment of the audio window and processing interval:

```bash
WINDOW_SECONDS=4 STEP_SECONDS=2 python app_fast.py
```

**Important:** A two-second processing interval does **not** mean two-second subtitle latency. Actual delays depend on CPU performance, model loading and inference, audio buffering, speech complexity, and—in French mode—the additional translation stage.

## 5. Troubleshooting

### 5.1 BlackHole 2ch is not listed

Check that:

- BlackHole is installed correctly.
- It appears in macOS Audio MIDI Setup.
- You have restarted the Python application.
- You have clicked **Refresh Devices** in the browser interface.
- Audio permissions and relevant applications have been restarted if necessary.

### 5.2 No English or French subtitles appear

First confirm that the video is playing audible dialogue, macOS output is set to a Multi-Output Device that includes BlackHole, the application's audio input is **BlackHole 2ch**, and you have selected a subtitle language and clicked **Start Subtitles**.

If macOS requests microphone or audio-input access, allow it for the relevant application.

#### Test whether BlackHole receives audio

Keep an audible YouTube video playing. In **another Terminal window**, enter the project directory, activate its virtual environment, and run the following test. The Flask server can remain running in the original Terminal.

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

**Interpreting the result:**

- `Audio RMS: 0.0`: No audio signal was detected during the test. If the video was audibly playing, check macOS output routing first.
- An RMS value noticeably above zero: BlackHole is receiving a signal. If subtitles still do not appear, investigate Whisper processing and backend logs.
- `BlackHole input not found`: Python cannot find the BlackHole input device; check installation and device settings.

RMS is a basic measure of signal strength, **not** a speech-recognition quality score. Test during a segment with continuous spoken dialogue.

#### Inspect Flask API status

If audio is present but subtitles still do not appear, open another Terminal and run:

```bash
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
```

`running: true` only means the recognition task is active; it does **not** prove subtitles are being generated. If `latest` remains `null` and `seq` remains `0`, no subtitle result has been produced. Also inspect the Terminal running `app_fast.py` for model loading, audio capture, transcription timings, and errors.

### 5.3 English or French subtitles are very slow

Try the faster backend:

```bash
python app_fast.py
```

Or a smaller Whisper model:

```bash
WHISPER_MODEL=tiny python app_fast.py
```

The faster backend can report transcription timing in Terminal. French mode may take longer because it also runs NLLB-200 translation. First-time model loading can add further delay.

### 5.4 Check whether recognition is progressing

With the application running, open another Terminal and run:

```bash
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
```

A response **after successful subtitle generation** may include fields such as these (illustrative example):

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

- `running`: Whether the recognition task is active.
- `error`: Any error reported by the backend.
- `language`: Selected target subtitle language, such as `en` or `fr`.
- `latest.text`: Most recently generated subtitle text.
- `seq`: Subtitle update sequence number.

If `seq` increases while dialogue is playing, the backend is generally producing new subtitle updates. `running: true` alone is insufficient evidence of successful recognition.

### 5.5 A YouTube video cannot be embedded

Some YouTube videos prohibit embedding on third-party pages. You may play a video you are authorized to access in another browser tab and capture its system audio through BlackHole. However, the subtitles will still appear in the **local LiveSubTranslate page**; they will not automatically overlay the separate YouTube tab.

### 5.6 Change the YouTube video

The updated interface supports entering a new YouTube URL directly:

1. Paste the new video URL into the link field.
2. Click **Load Video**.
3. Wait for the video to load.
4. Choose a subtitle language, confirm the audio device, and start recognition.

You no longer need to edit the iframe URL in `templates/index.html` manually. Some videos may still be unavailable because of embedding permissions or browser restrictions.

### 5.7 Port 8765 is already in use

If you see:

```text
Address already in use
Port 8765 is in use by another program.
```

An earlier Flask server may still be running. Return to its Terminal and press `Control + C` before starting another backend.

To identify the process listening on that port:

```bash
lsof -nP -iTCP:8765 -sTCP:LISTEN
```

Only stop a process after confirming that it belongs to the previous LiveSubTranslate instance. Do not launch `app.py` and `app_fast.py` simultaneously on the same port.

## 6. Known limitations

**Subtitle latency**

Recognition and translation run locally and may lag behind dialogue. Strict real-time synchronization is not guaranteed; French mode may incur additional translation delay.

**Recognition and translation quality**

Background music, overlapping speakers, accents, dialects, idioms, and culturally specific expressions can reduce accuracy.

**Repeated or missing subtitles**

Sliding audio windows can cause phrases to be repeated or omitted.

**Language support**

The current prototype targets spoken Mandarin and provides English and French subtitle modes. English uses Faster-Whisper direct translation; French uses Mandarin transcription followed by NLLB-200 translation. Both paths remain experimental and are not guaranteed to produce subtitles for every video.

**Dependence on audio routing**

macOS must route playback audio into BlackHole correctly. A running recognition task does not necessarily mean that audio is being captured.

**YouTube embedding restrictions**

Some videos cannot be embedded in the local interface because of platform or video-owner settings.

**Platform compatibility**

The documented setup is macOS with BlackHole. Windows and Linux configurations have not been validated.

**Local development server**

Flask's development server is intended for local experimentation, not public internet exposure.

**Copyright and privacy**

Only process audio you are authorized to access and handle, and comply with applicable law and platform terms. Do not commit copyrighted movie clips, private recordings, access tokens, or other sensitive data to the repository.

## 7. Possible future improvements

- Improve YouTube URL parsing and embedded playback compatibility.
- Provide clearer BlackHole setup guidance and automatic audio diagnostics.
- Improve speech segmentation, subtitle deduplication, and latency control.
- Improve Mandarin-to-French translation quality and speed.
- Add timestamps and more accurate subtitle synchronization.
- Support SRT and VTT subtitle export.
- Benchmark subtitle latency, speech recognition, and translation quality.
- Explore additional target languages.
- Improve Windows and Linux compatibility.

## 8. License

The project's license is determined by the `LICENSE` file in the root of the GitHub repository.

If the repository adopts the **MIT License**, others may use, modify, copy, and distribute the project under its conditions, including retaining the required copyright and license notices.

Third-party components—including Faster-Whisper, Flask, BlackHole, Transformers, and the NLLB-200 model—remain subject to their respective licenses and terms of use.

> Do not describe the repository as MIT-licensed until the appropriate MIT `LICENSE` file has actually been added.

---

**LiveSubTranslate — Experimental Open-Source Prototype**

A local Python, Faster-Whisper, NLLB-200, BlackHole, and Flask prototype for English and French subtitles from Mandarin speech.
