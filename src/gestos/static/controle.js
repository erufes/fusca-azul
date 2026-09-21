'use strict';
const byId = id => document.getElementById(id);
const video = byId('webcam');
const overlay = byId('overlay');
const ctx = overlay.getContext('2d');
const capture = document.createElement('canvas');
const captureContext = capture.getContext('2d');
const toggle = byId('show-landmarks');
const button = byId('camera-button');
const edges = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
const commands = {
  FRENTE: ['forward', 'Em frente'],
  PARAR: ['stop', 'Parar'],
  AGUARDANDO: ['waiting', 'Aguardando'],
  NENHUMA_MAO: ['idle', 'Nenhuma mão detectada'],
};
let ws, stream, pending = false, sentAt = 0, lastPoints = [], session = 0, frameSession = 0, reconnectTimer, closing = false;
function setCommand(state, title) {
  byId('command-card').dataset.state = state;
  byId('command-text').textContent = title;
}
function clearDetection() {
  lastPoints = [];
  ctx.clearRect(0, 0, overlay.width, overlay.height);
}
function drawPoints() {
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  if (!toggle.checked || lastPoints.length !== 21) return;
  // Video and canvas use the same aspect ratio and mirror transform.
  const points = lastPoints.map(p => [p.x * overlay.width, p.y * overlay.height]);
  ctx.strokeStyle = '#d6e6bc';
  ctx.lineWidth = Math.max(2, overlay.width / 240);
  ctx.lineCap = 'round';
  ctx.beginPath();
  edges.forEach(([a, b]) => { ctx.moveTo(...points[a]); ctx.lineTo(...points[b]); });
  ctx.stroke();
  points.forEach(([x, y], index) => {
    ctx.beginPath();
    ctx.arc(x, y, Math.max(3, overlay.width / 130), 0, Math.PI * 2);
    ctx.fillStyle = [4,8,12,16,20].includes(index) ? '#fff0ac' : '#f4fbff';
    ctx.fill();
    ctx.strokeStyle = '#343a2d';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });
}
toggle.addEventListener('change', drawPoints);
function connect() {
  if (closing) return;
  const socket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws/video?landmarks=1');
  ws = socket;
  socket.onopen = () => {
    byId('connection').dataset.state = 'online';
    byId('connection').textContent = 'Conectado';
  };
  socket.onmessage = event => {
    pending = false;
    if (!stream || frameSession !== session) return;
    try {
      const result = JSON.parse(event.data);
      if (result.error || !commands[result.command]) throw new Error('Resposta inválida');
      lastPoints = result.landmarks || [];
      setCommand(...commands[result.command]);
      drawPoints();
    } catch {
      clearDetection();
      setCommand('waiting', 'Tente novamente');
    }
  };
  socket.onclose = () => {
    pending = false;
    byId('connection').dataset.state = 'offline';
    byId('connection').textContent = 'Reconectando…';
    clearDetection();
    if (stream) setCommand('waiting', 'Sem conexão');
    if (!closing) reconnectTimer = setTimeout(connect, 2000);
  };
  socket.onerror = () => socket.close();
}
function stopCamera(message = '') {
  session++;
  if (stream) stream.getTracks().forEach(track => track.stop());
  stream = null;
  video.srcObject = null;
  byId('placeholder').hidden = false;
  byId('placeholder-title').textContent = 'Câmera pausada';
  byId('placeholder-text').textContent = message;
  button.textContent = 'Ativar câmera';
  clearDetection();
  setCommand('idle', '—');
}
button.addEventListener('click', async () => {
  if (stream) { stopCamera(); return; }
  button.disabled = true;
  try {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('INSECURE_CONTEXT');
    stream = await navigator.mediaDevices.getUserMedia({video: {width: {ideal: 640}, height: {ideal: 480}, facingMode: 'user'}, audio: false});
    video.srcObject = stream;
    await video.play();
    stream.getVideoTracks()[0].addEventListener('ended', () => stopCamera('A câmera foi desconectada. Conecte-a e tente novamente.'));
    capture.width = overlay.width = video.videoWidth;
    capture.height = overlay.height = video.videoHeight;
    byId('placeholder').hidden = true;
    button.textContent = 'Pausar câmera';
    setCommand(...commands.NENHUMA_MAO);
  } catch (error) {
    stopCamera();
    byId('placeholder-title').textContent = 'Não foi possível abrir a câmera';
    const messages = {NotAllowedError: 'Permita o acesso à câmera no navegador e tente novamente.', NotFoundError: 'Nenhuma câmera encontrada. Conecte uma câmera para continuar.', NotReadableError: 'A câmera pode estar em uso por outro aplicativo. Feche-o e tente novamente.', INSECURE_CONTEXT: 'Para usar a câmera, abra a página por HTTPS ou por localhost no computador do servidor.'};
    const message = messages[error.name] || messages[error.message] || 'Verifique a câmera e tente novamente.';
    byId('placeholder-text').textContent = message;
  } finally { button.disabled = false; }
});
// One frame in flight prevents slow recognition from building up a video queue.
const captureTimer = setInterval(() => {
  if (pending) {
    if (performance.now() - sentAt > 5000) { clearDetection(); ws.close(); }
    return;
  }
  if (!stream || ws?.readyState !== WebSocket.OPEN || video.readyState < 2) return;
  frameSession = session;
  const capturedSession = session;
  const socket = ws;
  pending = true;
  sentAt = performance.now();
  captureContext.drawImage(video, 0, 0, capture.width, capture.height);
  capture.toBlob(blob => {
    if (ws !== socket) return;
    if (!blob || !stream || session !== capturedSession || socket.readyState !== WebSocket.OPEN) { pending = false; return; }
    socket.send(blob);
  }, 'image/jpeg', 0.65);
}, 100);
window.addEventListener('pagehide', () => {
  closing = true;
  clearInterval(captureTimer);
  clearTimeout(reconnectTimer);
  stopCamera();
  ws?.close();
});
connect();
