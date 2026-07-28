// ================================================================
// app.js — KaiX Control Panel client
// ================================================================

const socket = io();

const dot         = document.getElementById('dot');
const statusLabel = document.getElementById('statusLabel');
const startBtn    = document.getElementById('startBtn');
const stopBtn     = document.getElementById('stopBtn');
const consoleEl   = document.getElementById('console');

// ── Socket events ─────────────────────────────────────────────────

socket.on('connect', () => {
  dot.className = 'dot connecting';
  statusLabel.textContent = 'Đang kết nối...';
});

socket.on('disconnect', () => {
  dot.className = 'dot stopped';
  statusLabel.textContent = 'Mất kết nối với server';
  setButtons(false, false);
});

socket.on('status', ({ running }) => {
  updateStatus(running);
});

socket.on('log', ({ ts, text, error }) => {
  appendLog(ts, text, error);
});

// ── UI helpers ────────────────────────────────────────────────────

function updateStatus(running) {
  if (running) {
    dot.className = 'dot running';
    statusLabel.textContent = '🟢 Đang chạy';
  } else {
    dot.className = 'dot stopped';
    statusLabel.textContent = '🔴 Đã dừng';
  }
  setButtons(!running, running);
}

function setButtons(startEnabled, stopEnabled) {
  startBtn.disabled = !startEnabled;
  stopBtn.disabled  = !stopEnabled;
}

function appendLog(ts, text, isError = false) {
  // Remove placeholder on first real log
  const placeholder = consoleEl.querySelector('.log-placeholder');
  if (placeholder) placeholder.remove();

  const line = document.createElement('div');
  line.className = 'log-line' + (isError ? ' error' : '');

  const timeSpan = document.createElement('span');
  timeSpan.className = 'ts';
  timeSpan.textContent = `[${ts}]`;

  line.appendChild(timeSpan);
  line.appendChild(document.createTextNode(text));
  consoleEl.appendChild(line);

  // Auto-scroll to bottom
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

function clearLog() {
  consoleEl.innerHTML = '<div class="log-placeholder">Nhật ký sẽ hiển thị ở đây...</div>';
}

// ── Button actions ────────────────────────────────────────────────

async function startBot() {
  startBtn.disabled = true;
  try {
    const res  = await fetch('/start', { method: 'POST' });
    const data = await res.json();
    if (!data.success) {
      const ts = new Date().toLocaleTimeString('vi-VN', { hour12: false });
      appendLog(ts, data.message, true);
      startBtn.disabled = false;
    }
  } catch {
    const ts = new Date().toLocaleTimeString('vi-VN', { hour12: false });
    appendLog(ts, 'Không thể kết nối đến server.', true);
    startBtn.disabled = false;
  }
}

async function stopBot() {
  stopBtn.disabled = true;
  try {
    const res  = await fetch('/stop', { method: 'POST' });
    const data = await res.json();
    if (!data.success) {
      const ts = new Date().toLocaleTimeString('vi-VN', { hour12: false });
      appendLog(ts, data.message, true);
      stopBtn.disabled = false;
    }
  } catch {
    const ts = new Date().toLocaleTimeString('vi-VN', { hour12: false });
    appendLog(ts, 'Không thể kết nối đến server.', true);
    stopBtn.disabled = false;
  }
}
