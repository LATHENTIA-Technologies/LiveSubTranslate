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
WINDOW_SECONDS = float(os.environ.get('WINDOW_SECONDS', '4'))
STEP_SECONDS = float(os.environ.get('STEP_SECONDS', '2'))
MODEL_SIZE = os.environ.get('WHISPER_MODEL', 'base')
FRENCH_MODEL = os.environ.get('FRENCH_MODEL', 'facebook/nllb-200-distilled-600M')

state = {'running': False, 'error': '', 'latest': None, 'seq': 0,
         'device': '', 'language': 'en', 'processing_seconds': None}
lock = threading.Lock()
stop_event = threading.Event()
worker = None


def input_devices():
    return [{'id': idx, 'name': d['name'], 'channels': d['max_input_channels']}
            for idx, d in enumerate(sd.query_devices()) if d['max_input_channels'] > 0]


def make_french_translator():
    """Load an optional local Chinese-to-French translation model on French runs."""
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    except ImportError as exc:
        raise RuntimeError('French subtitles require: pip install transformers sentencepiece torch') from exc

    print(f'Loading French translation model: {FRENCH_MODEL}', flush=True)
    tokenizer = AutoTokenizer.from_pretrained(FRENCH_MODEL, src_lang='zho_Hans')
    translator_model = AutoModelForSeq2SeqLM.from_pretrained(FRENCH_MODEL)
    translator_model.eval()
    french_id = tokenizer.convert_tokens_to_ids('fra_Latn')
    if french_id is None or french_id == tokenizer.unk_token_id:
        raise RuntimeError('Translation model does not support fra_Latn.')

    def translate(text):
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        with torch.inference_mode():
            tokens = translator_model.generate(
                **inputs, forced_bos_token_id=french_id,
                max_new_tokens=160, num_beams=2)
        return tokenizer.batch_decode(tokens, skip_special_tokens=True)[0].strip()

    return translate


def run_capture(device_id, language):
    try:
        print(f'Loading Whisper model: {MODEL_SIZE} | subtitles: {language}', flush=True)
        model = WhisperModel(MODEL_SIZE, device='cpu', compute_type='int8')
        translate_french = make_french_translator() if language == 'fr' else None
        if stop_event.is_set():
            return
        print('Models loaded.', flush=True)
        chunks = deque(maxlen=max(1, int(WINDOW_SECONDS * RATE / BLOCK)))
        last_process = time.monotonic() - STEP_SECONDS

        def callback(indata, frames, time_info, status):
            if status:
                print(f'Audio warning: {status}', flush=True)
            chunks.append(indata[:, 0].copy())

        with sd.InputStream(samplerate=RATE, channels=1, dtype='float32',
                            blocksize=BLOCK, device=device_id, callback=callback):
            device_name = sd.query_devices(device_id)['name']
            with lock:
                state['device'] = device_name
            print(f'Capturing audio from {device_name}', flush=True)

            while not stop_event.is_set():
                time.sleep(0.1)
                if (time.monotonic() - last_process < STEP_SECONDS or
                        len(chunks) < int(2 * RATE / BLOCK)):
                    continue
                last_process = time.monotonic()
                audio = np.concatenate(list(chunks)).astype(np.float32)
                rms = float(np.sqrt(np.mean(audio ** 2)))
                if rms < 0.003:
                    continue

                started = time.monotonic()
                task = 'translate' if language == 'en' else 'transcribe'
                segments, _ = model.transcribe(
                    audio, language='zh', task=task, beam_size=1, best_of=1,
                    vad_filter=False, condition_on_previous_text=False)
                text = ' '.join(s.text.strip() for s in segments).strip()
                if text and translate_french is not None and not stop_event.is_set():
                    text = translate_french(text)
                elapsed = time.monotonic() - started
                print(f'Processing {elapsed:.2f}s | {language} | RMS {rms:.4f} | {text}', flush=True)
                with lock:
                    state['processing_seconds'] = round(elapsed, 2)
                    if text and not stop_event.is_set() and (not state['latest'] or state['latest']['text'] != text):
                        state['seq'] += 1
                        state['latest'] = {'seq': state['seq'], 'text': text,
                                           'time': time.time(), 'language': language}
    except Exception as exc:
        print(f'Capture error: {type(exc).__name__}: {exc}', flush=True)
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
    data = request.get_json(silent=True) or {}
    device_id = data.get('device')
    language = data.get('language', 'en')
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
        state.update(running=True, error='', latest=None, device='',
                     language=language, processing_seconds=None)
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
