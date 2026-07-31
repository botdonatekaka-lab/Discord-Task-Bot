# KaiX Discord Bot

A Vietnamese Discord bot with a web control panel (dashboard).

## Project structure

| Path | Purpose |
|------|---------|
| `bot/` | Discord bot source (Python, discord.py) |
| `run.py` | Bot entry point — spawned by the dashboard |
| `server.js` | Web dashboard (Node.js / Express + Socket.IO) |
| `web/` | Dashboard frontend (plain HTML/CSS/JS) |

## How to run

One workflow manages the entire project:

### Dashboard Web (`node server.js`)
Opens a control panel at the app's preview URL. Use the **Bật Bot** (Start) / **Tắt Bot** (Stop) buttons to control the bot. The dashboard spawns `python run.py` as a child process and streams its logs in real time.

> **Important:** Do not run `python run.py` separately — the dashboard is the sole controller of the bot process. Running both would start two bot instances on the same token.

## Required secrets

| Secret | Description |
|--------|-------------|
| `DISCORD_TOKEN` | Bot token from the Discord Developer Portal (Bot → Token) |

## User preferences
