import os
import threading
import time
from collections import deque
from flask import Flask, jsonify, render_template, request
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

app = Flask(__name__)
RATE = 16000
BLOCK = 1600
WINDOW_SECONDS = 7
STEP_SECONDS = 5
DEVICE_NAME = os.environ.get('AUDIO_DEVICE', '').strip()
MODEL_SIZE = os.environ.get('WHISPER_MODEL', 'small')

state = {'running': False, 'error': '', 'latest': None, 'seq': 0, 'device': ''}
lock = threading.Lock()
stop_event = threading.Event()
worker = None

def input_devices():
    result = []
    for idx, d in enumerate(sd.query_devices()):
        if d['max_input_channels'] > 0:
            result.append({'id': idx, 'name': d['name'], 'channels': d['max_input_channels']})
    return result

def run_capture(device_id):
    try:
        model = WhisperModel(MODEL_SIZE, device='cpu', compute_type='int8')
        chunks = deque(maxlen=int(WINDOW_SECONDS * RATE / BLOCK))
        last_process = time.monotonic()
        def callback(indata, frames, time_info, status):
            if status:
                pass
            chunks.append(indata[:, 0].copy())
        with sd.InputStream(samplerate=RATE, channels=1, dtype='float32', blocksize=BLOCK, device=device_id, callback=callback):
            with lock:
                state['device'] = sd.query_devices(device_id)['name']
            while not stop_event.is_set():
                time.sleep(0.15)
                if time.monotonic() - last_process < STEP_SECONDS or len(chunks) < int(3 * RATE / BLOCK):
                    continue
                last_process = time.monotonic()
                audio = np.concatenate(list(chunks)).astype(np.float32)
                if np.sqrt(np.mean(audio ** 2)) < 0.003:
                    continue
                # Whisper's translate task translates Mandarin speech directly into English.
                segments, _ = model.transcribe(audio, language='zh', task='translate', beam_size=3,
                                               vad_filter=True, condition_on_previous_text=False)
                text = ' '.join(s.text.strip() for s in segments).strip()
                if text:
                    with lock:
                        if not state['latest'] or state['latest']['text'] != text:
                            state['seq'] += 1
                            state['latest'] = {'seq': state['seq'], 'text': text, 'time': time.time()}
    except Exception as exc:
        with lock:
            state['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        with lock:
            state['running'] = False

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/api/devices')
def devices():
    return jsonify(input_devices())

@app.post('/api/start')
def start():
    global worker
    with lock:
        if state['running']:
            return jsonify({'ok': True})
        device_id = request.json.get('device') if request.is_json else None
        if device_id is None:
            return jsonify({'ok': False, 'error': 'Select a capture device (e.g. BlackHole 2ch).'}), 400
        state.update(running=True, error='', latest=None)
        stop_event.clear()
    worker = threading.Thread(target=run_capture, args=(int(device_id),), daemon=True)
    worker.start()
    return jsonify({'ok': True})

@app.post('/api/stop')
def stop():
    stop_event.set()
    return jsonify({'ok': True})

@app.get('/api/status')
def status():
    with lock:
        return jsonify(dict(state))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8765, debug=False, threaded=True)
