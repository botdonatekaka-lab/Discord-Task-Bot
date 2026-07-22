# Discord Donation Bot

A Python Discord bot (discord.py) that manages community donations — users submit donate requests via interactive panels, admins approve/reject them, and the bot assigns roles automatically.

## Stack

- **Language:** Python 3.11
- **Library:** discord.py 2.7.1
- **Storage:** JSON files (`bot/donate_data.json`, `bot/event_data.json`)

## How to run

The workflow **Discord Bot** runs `python run.py`.

### Required secret

| Key | Description |
|-----|-------------|
| `DISCORD_TOKEN` | Bot token from the Discord Developer Portal |

## Project structure

```
bot/
  main.py       — Entry point: initializes bot, registers events & commands
  commands.py   — Slash commands
  views.py      — Discord UI views (buttons, modals)
  embeds.py     — Embed builders
  data.py       — JSON data helpers
  tasks.py      — Background tasks
  event.py      — Event thread logic
  config.py     — Channel IDs, role IDs, donate packages, bank info
run.py          — Start script (runs bot/main.py)
```

## Configuration

Edit `bot/config.py` to update:
- Bank account details
- Discord channel IDs (admin channel, thanks channel, privilege channel)
- Donate packages (names, prices, role IDs, emojis)

## User preferences
