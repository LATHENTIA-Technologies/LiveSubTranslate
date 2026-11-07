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
WINDOW_SECONDS = float(os.environ.get('WINDOW_SECONDS', '7'))
STEP_SECONDS = float(os.environ.get('STEP_SECONDS', '5'))
MODEL_SIZE = os.environ.get('WHISPER_MODEL', 'small')
# NLLB supports Chinese (Simplified) -> French; downloads on first French use.
FRENCH_MODEL = os.environ.get('FRENCH_MODEL', 'facebook/nllb-200-distilled-600M')

state = {'running': False, 'error': '', 'latest': None, 'seq': 0,
         'device': '', 'language': 'en'}
lock = threading.Lock()
stop_event = threading.Event()
worker = None

def input_devices():
    return [{'id': idx, 'name': d['name'], 'channels': d['max_input_channels']}
            for idx, d in enumerate(sd.query_devices()) if d['max_input_channels'] > 0]

def make_french_translator():
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    except ImportError as exc:
        raise RuntimeError('French subtitles require: pip install transformers sentencepiece torch') from exc
    tokenizer = AutoTokenizer.from_pretrained(FRENCH_MODEL, src_lang='zho_Hans')
    model = AutoModelForSeq2SeqLM.from_pretrained(FRENCH_MODEL)
    model.eval()
    target_id = tokenizer.convert_tokens_to_ids('fra_Latn')
    if target_id is None or target_id == tokenizer.unk_token_id:
        raise RuntimeError('The selected translation model does not support fra_Latn.')

    def translate(text):
        encoded = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        with torch.inference_mode():
            output = model.generate(**encoded, forced_bos_token_id=target_id,
                                    max_new_tokens=160, num_beams=2)
        return tokenizer.batch_decode(output, skip_special_tokens=True)[0].strip()
    return translate

def run_capture(device_id, language):
    try:
        whisper = WhisperModel(MODEL_SIZE, device='cpu', compute_type='int8')
        translator = make_french_translator() if language == 'fr' else None
        chunks = deque(maxlen=max(1, int(WINDOW_SECONDS * RATE / BLOCK)))
        last_process = time.monotonic()

        def callback(indata, frames, time_info, status):
            chunks.append(indata[:, 0].copy())

        if stop_event.is_set():
            return
        with sd.InputStream(samplerate=RATE, channels=1, dtype='float32',
                            blocksize=BLOCK, device=device_id, callback=callback):
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
                task = 'translate' if language == 'en' else 'transcribe'
                segments, _ = whisper.transcribe(
                    audio, language='zh', task=task, beam_size=3,
                    vad_filter=True, condition_on_previous_text=False)
                text = ' '.join(s.text.strip() for s in segments).strip()
                if not text or stop_event.is_set():
                    continue
                if translator is not None:
                    text = translator(text)
                if text and not stop_event.is_set():
                    with lock:
                        if not state['latest'] or state['latest']['text'] != text:
                            state['seq'] += 1
                            state['latest'] = {'seq': state['seq'], 'text': text,
                                               'time': time.time(), 'language': language}
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
    payload = request.get_json(silent=True) or {}
    device_id = payload.get('device')
    language = payload.get('language', 'en')
    if language not in ('en', 'fr'):
        return jsonify({'ok': False, 'error': 'Language must be en or fr.'}), 400
    if isinstance(device_id, bool) or not isinstance(device_id, int):
        return jsonify({'ok': False, 'error': 'Select an audio input device.'}), 400
    try:
        device = sd.query_devices(device_id)
        if device['max_input_channels'] <= 0:
            raise ValueError('Selected device has no audio input channels.')
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 400
    with lock:
        if state['running']:
            return jsonify({'ok': False, 'error': 'Stop the current session before changing language.'}), 409
        state.update(running=True, error='', latest=None, device='', language=language)
        stop_event.clear()
        worker = threading.Thread(target=run_capture, args=(device_id, language), daemon=True)
        worker.start()
    return jsonify({'ok': True, 'language': language})

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
