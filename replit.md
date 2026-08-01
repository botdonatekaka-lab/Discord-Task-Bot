# Discord Donation Bot

A Python Discord bot for managing donations on a Vietnamese Discord server. Handles donation packages, invite tracking, and admin approval workflows.

## Stack
- **Language:** Python 3.11
- **Library:** discord.py 2.x
- **Entry point:** `run.py` → `bot/main.py`

## How to run

The bot starts automatically via the **Discord Bot** workflow (`python run.py`).

To restart it manually, use the workflow panel or run:
```
python run.py
```

## Required secrets

| Secret | Description |
|--------|-------------|
| `DISCORD_TOKEN` | Bot token from Discord Developer Portal (Application → Bot → Token) |

## Project structure

```
bot/
  main.py         — Bot init, events (on_ready, on_member_join, etc.)
  commands.py     — Slash commands
  config.py       — Package definitions, channel IDs, bank info
  views.py        — Discord UI components (buttons, modals, selects)
  embeds.py       — Embed builders
  tasks.py        — Background tasks (e.g. expiry checks)
  data.py         — Data helpers (load/save JSON, formatting)
  event.py        — Event channel message handling
  donate_data.json    — Donation records (persistent)
  creator_data.json   — Creator/invite tracking data
  event_data.json     — Event configuration
run.py            — Script to start the bot
```

## User preferences
- Keep existing Vietnamese code structure and naming conventions
