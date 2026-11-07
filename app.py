<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LiveSubTranslate · 中文原声实时英文字幕</title>
<style>
:root{color-scheme:dark}
body{font:16px -apple-system,BlinkMacSystemFont,Arial,sans-serif;background:#101827;color:#eaf0fb;margin:0}
main{max-width:1080px;margin:auto;padding:24px}h1{font-size:26px}
p{color:#b9c6db;line-height:1.6}
.player{position:relative;aspect-ratio:16/9;background:#050910;border-radius:14px;overflow:hidden}
.player iframe{width:100%;height:100%;border:0}
.placeholder{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;color:#b9c6db;box-sizing:border-box}
.subtitle{position:absolute;bottom:10%;left:6%;width:88%;text-align:center;pointer-events:none;font-size:clamp(18px,2.8vw,34px);font-weight:700;color:white;text-shadow:0 2px 5px #000,0 0 9px #000;line-height:1.35}
.panel{background:#1d2a3d;border-radius:12px;padding:18px;margin-top:16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
button,select,input{background:#304461;color:white;border:1px solid #506789;border-radius:8px;padding:11px;font-size:15px;box-sizing:border-box}
input{flex:1;min-width:220px}button{cursor:pointer}button.primary{background:#2263cb}button:disabled{opacity:.5;cursor:not-allowed}
.status{font-size:14px;color:#b9c6db}small{color:#b9c6db}
</style>
</head>
<body><main>
<h1>🎬 LiveSubTranslate · 中文原声实时英文字幕</h1>
<p>输入你想观看的 YouTube 视频链接，通过 Mac 音频输入设备捕获声音，并使用本地 Whisper 将普通话翻译为英文。字幕可能延迟或不准确。</p>
<form class="panel" id="videoForm">
<label for="videoUrl">YouTube 视频链接：</label>
<input id="videoUrl" type="url" placeholder="https://www.youtube.com/watch?v=..." autocomplete="off" required>
<button class="primary" type="submit">加载视频</button>
<span class="status" id="videoStatus" role="status"></span>
</form>
<div class="player">
<div class="placeholder" id="placeholder">请在上方输入 YouTube 视频链接并点击「加载视频」</div>
<iframe id="youtubePlayer" title="YouTube video" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen hidden></iframe>
<div class="subtitle" id="subtitle" aria-live="polite">English subtitles will appear here.</div>
</div>
<div class="panel">
<label for="device">音频输入：</label>
<select id="device"><option value="">正在加载...</option></select>
<button id="refresh" type="button">刷新设备</button>
<button class="primary" id="start" type="button">开始英文字幕</button>
<button id="stop" type="button">停止</button>
<span class="status" id="status" role="status">未启动</span>
</div>
<p><small>注意：必须将 Mac 的声音输出路由到包含 BlackHole 2ch 的多输出设备，并在此选择 BlackHole 2ch 作为输入。部分 YouTube 视频禁止嵌入；遇到这种情况，可以在另一个标签页播放视频，但字幕仍只显示在本地网页中。请仅处理你有权使用的音频。</small></p>
</main>
<script>
const $ = id => document.getElementById(id);
let lastSeq = 0;

function getYouTubeId(raw) {
  try {
    const url = new URL(raw.trim());
    const host = url.hostname.toLowerCase();
    let id = '';
    if (host === 'youtu.be' || host === 'www.youtu.be') {
      id = url.pathname.split('/')[1] || '';
    } else if (['youtube.com','www.youtube.com','m.youtube.com','music.youtube.com','www.youtube-nocookie.com','youtube-nocookie.com'].includes(host)) {
      const parts = url.pathname.split('/').filter(Boolean);
      if (parts[0] === 'watch') id = url.searchParams.get('v') || '';
      else if (['embed','shorts','live'].includes(parts[0])) id = parts[1] || '';
    }
    return /^[a-zA-Z0-9_-]{11}$/.test(id) ? id : null;
  } catch { return null; }
}

$('videoForm').addEventListener('submit', event => {
  event.preventDefault();
  const id = getYouTubeId($('videoUrl').value);
  if (!id) {
    $('videoStatus').textContent = '链接无效，请粘贴完整的 YouTube 视频地址。';
    return;
  }
  $('youtubePlayer').src = `https://www.youtube.com/embed/${encodeURIComponent(id)}?enablejsapi=1`;
  $('youtubePlayer').hidden = false;
  $('placeholder').hidden = true;
  $('subtitle').textContent = 'English subtitles will appear here.';
  $('videoStatus').textContent = '视频已加载，请点击播放器中的播放按钮。';
});

async function devices() {
  try {
    const response = await fetch('/api/devices');
    if (!response.ok) throw new Error('无法获取音频设备');
    const list = await response.json();
    const select = $('device');
    select.replaceChildren();
    for (const item of list) {
      const option = document.createElement('option');
      option.value = String(item.id);
      option.textContent = item.name;
      select.appendChild(option);
    }
    const bh = list.find(x => x.name.toLowerCase().includes('blackhole'));
    if (bh) select.value = String(bh.id);
    if (!list.length) $('status').textContent = '没有可用的音频输入设备';
  } catch (e) { $('status').textContent = e.message; }
}
$('refresh').onclick = devices;
$('start').onclick = async () => {
  const d = $('device').value;
  if (d === '') { alert('请先选择 BlackHole 2ch 等音频输入设备'); return; }
  try {
    const response = await fetch('/api/start', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({device: Number(d)})
    });
    const result = await response.json();
    if (!response.ok || !result.ok) alert(result.error || '启动失败');
  } catch (e) { $('status').textContent = '启动失败：' + e.message; }
};
$('stop').onclick = async () => {
  try { await fetch('/api/stop', {method:'POST'}); }
  catch (e) { $('status').textContent = '停止失败：' + e.message; }
};

async function updateStatus() {
  try {
    const response = await fetch('/api/status', {cache:'no-store'});
    if (!response.ok) throw new Error('服务器未响应');
    const s = await response.json();
    $('status').textContent = s.error ? '错误：' + s.error : (s.running ? '正在识别 · ' + (s.device || '正在启动') : '已停止');
    if (s.latest && s.latest.seq !== lastSeq) {
      lastSeq = s.latest.seq;
      $('subtitle').textContent = s.latest.text;
    }
  } catch (e) { $('status').textContent = '连接中断：' + e.message; }
}
setInterval(updateStatus, 1000);
devices();
updateStatus();
</script>
</body>
</html>
