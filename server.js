// ================================================================
// server.js — Dashboard web để bật/tắt Discord bot
// Chạy: node server.js
// ================================================================

const express = require('express');
const http    = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');
const path = require('path');

const app    = express();
const server = http.createServer(app);
const io     = new Server(server, {
  cors: { origin: '*' }
});

const PORT = process.env.PORT || 3000;

// ── Trạng thái bot ────────────────────────────────────────────────
let botProcess = null;

function isRunning() {
  return botProcess !== null && !botProcess.killed;
}

function broadcastStatus() {
  io.emit('status', { running: isRunning() });
}

// ── Static files ─────────────────────────────────────────────────
app.use(express.static(path.join(__dirname, 'web')));
app.use(express.json());

// ── API ───────────────────────────────────────────────────────────

app.get('/status', (_req, res) => {
  res.json({ running: isRunning() });
});

app.post('/start', (_req, res) => {
  if (isRunning()) {
    return res.json({ success: false, message: 'Bot đang chạy rồi.' });
  }

  const ts = () => new Date().toLocaleTimeString('vi-VN', { hour12: false });

  botProcess = spawn('python', ['run.py'], {
    cwd: __dirname,
    env: { ...process.env },
  });

  botProcess.stdout.on('data', (data) => {
    data.toString().split('\n')
      .map(l => l.trim())
      .filter(Boolean)
      .forEach(line => io.emit('log', { ts: ts(), text: line }));
  });

  botProcess.stderr.on('data', (data) => {
    data.toString().split('\n')
      .map(l => l.trim())
      .filter(Boolean)
      .forEach(line => io.emit('log', { ts: ts(), text: line, error: true }));
  });

  botProcess.on('close', (code) => {
    io.emit('log', { ts: ts(), text: `Process kết thúc (exit code ${code})`, error: code !== 0 });
    botProcess = null;
    broadcastStatus();
  });

  botProcess.on('error', (err) => {
    io.emit('log', { ts: ts(), text: `Lỗi spawn: ${err.message}`, error: true });
    botProcess = null;
    broadcastStatus();
  });

  broadcastStatus();
  const ts0 = ts();
  io.emit('log', { ts: ts0, text: '▶ Đang khởi động bot...' });
  res.json({ success: true });
});

app.post('/stop', (_req, res) => {
  if (!isRunning()) {
    return res.json({ success: false, message: 'Bot chưa chạy.' });
  }

  const ts = () => new Date().toLocaleTimeString('vi-VN', { hour12: false });
  io.emit('log', { ts: ts(), text: '⏹ Đang tắt bot...' });

  // Gửi SIGTERM trước, nếu không phản hồi sau 3s thì SIGKILL
  botProcess.kill('SIGTERM');
  const killTimer = setTimeout(() => {
    if (isRunning()) {
      botProcess.kill('SIGKILL');
      io.emit('log', { ts: ts(), text: 'Đã dùng SIGKILL để buộc tắt.', error: true });
    }
  }, 3000);

  botProcess.once('close', () => clearTimeout(killTimer));
  res.json({ success: true });
});

// ── Socket.IO ─────────────────────────────────────────────────────
io.on('connection', (socket) => {
  // Gửi trạng thái hiện tại ngay khi client kết nối
  socket.emit('status', { running: isRunning() });
});

// ── Start server ──────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`✅ KaiX Dashboard đang chạy tại cổng ${PORT}`);
});
