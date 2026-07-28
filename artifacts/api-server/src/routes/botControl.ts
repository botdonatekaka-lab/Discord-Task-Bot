// ================================================================
// botControl.ts — Bật/tắt Python bot qua Express + Socket.IO
// ================================================================

import { type Express } from "express";
import { Server as SocketIO } from "socket.io";
import { spawn, type ChildProcess } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

// dist/index.mjs → artifacts/api-server/dist/ → go up 3 levels → workspace root
const __currentDir = path.dirname(fileURLToPath(import.meta.url));
const WORKSPACE_ROOT = path.resolve(__currentDir, "../../..");

let botProcess: ChildProcess | null = null;

function isRunning(): boolean {
  return botProcess !== null && !botProcess.killed;
}

export function setupBotControl(app: Express, io: SocketIO): void {
  function broadcastStatus(): void {
    io.emit("status", { running: isRunning() });
  }

  function ts(): string {
    return new Date().toLocaleTimeString("vi-VN", { hour12: false });
  }

  // ── GET /api/status ──────────────────────────────────────────────
  app.get("/api/status", (_req, res) => {
    res.json({ running: isRunning() });
  });

  // ── POST /api/start ──────────────────────────────────────────────
  app.post("/api/start", (_req, res) => {
    if (isRunning()) {
      res.json({ success: false, message: "Bot đang chạy rồi." });
      return;
    }

    botProcess = spawn("python", ["run.py"], {
      cwd: WORKSPACE_ROOT,
      env: { ...process.env },
    });

    botProcess.stdout?.on("data", (data: Buffer) => {
      data
        .toString()
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .forEach((line) => io.emit("log", { ts: ts(), text: line }));
    });

    botProcess.stderr?.on("data", (data: Buffer) => {
      data
        .toString()
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .forEach((line) =>
          io.emit("log", { ts: ts(), text: line, error: true }),
        );
    });

    botProcess.on("close", (code) => {
      io.emit("log", {
        ts: ts(),
        text: `Process kết thúc (exit code ${code})`,
        error: code !== 0,
      });
      botProcess = null;
      broadcastStatus();
    });

    botProcess.on("error", (err) => {
      io.emit("log", { ts: ts(), text: `Lỗi: ${err.message}`, error: true });
      botProcess = null;
      broadcastStatus();
    });

    broadcastStatus();
    io.emit("log", { ts: ts(), text: "▶ Đang khởi động bot..." });
    res.json({ success: true });
  });

  // ── POST /api/stop ───────────────────────────────────────────────
  app.post("/api/stop", (_req, res) => {
    if (!isRunning()) {
      res.json({ success: false, message: "Bot chưa chạy." });
      return;
    }

    io.emit("log", { ts: ts(), text: "⏹ Đang tắt bot..." });

    botProcess!.kill("SIGTERM");

    const killTimer = setTimeout(() => {
      if (isRunning()) {
        botProcess!.kill("SIGKILL");
        io.emit("log", {
          ts: ts(),
          text: "Đã dùng SIGKILL để buộc tắt.",
          error: true,
        });
      }
    }, 3000);

    botProcess!.once("close", () => clearTimeout(killTimer));
    res.json({ success: true });
  });

  // ── Socket.IO: gửi trạng thái khi client kết nối ────────────────
  io.on("connection", (socket) => {
    socket.emit("status", { running: isRunning() });
  });
}
