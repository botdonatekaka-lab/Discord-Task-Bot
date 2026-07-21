# Discord Donation Bot

A Python Discord bot that manages donation packages, admin approval flows, and event number-tracking for a Vietnamese Discord server.

## Run & Operate

- `python run.py` — start the bot (or use the "Discord Bot" workflow)
- Required secret: `DISCORD_TOKEN` — Discord bot token from the Developer Portal

## Stack

- Python 3.11, discord.py 2.x
- JSON file-based persistence (`bot/donate_data.json`, `bot/event_data.json`)
- uv for dependency management (`pyproject.toml` / `uv.lock`)

## Where things live

- `run.py` — entry point
- `bot/main.py` — bot setup, on_ready, on_message
- `bot/config.py` — channel IDs, bank info, donation packages
- `bot/commands.py` — slash commands
- `bot/views.py` — Discord UI components (buttons/modals)
- `bot/data.py` — JSON data helpers
- `bot/event.py` — event thread number-tracking logic
- `bot/tasks.py` — background tasks
- `bot/embeds.py` — embed builders

## Architecture decisions

- Persistent views are re-registered on `on_ready` so pending donation approvals survive restarts.
- All state is stored in JSON files (no database required).
- Slash commands are synced globally on startup.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Channel IDs and role IDs in `bot/config.py` are hardcoded for the target Discord server — update them if the bot moves to a different server.
- Custom emoji IDs in `bot/config.py` must exist on the server the bot is in.
