# Cortex — Setup Guide

A config-driven, multi-persona Discord bot powered by a local LLM
(via [LM Studio](https://lmstudio.ai)). No coding required to personalize it —
just edit `config.json`.

## 1. Requirements

- Python 3.11 or newer
- [LM Studio](https://lmstudio.ai) running locally with a model loaded
- A Discord bot application (see step 3)

## 2. Install dependencies

```terminal
pip install discord.py python-dotenv openai
```

## 3. Create your Discord bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**, give it a name
3. Go to the **Bot** tab → click **Reset Token** → copy the token (you'll need it in step 5)
4. Under **Privileged Gateway Intents**, enable **Message Content Intent**
5. Go to the **Installation** tab → under **Installation Contexts**, check
   both **Guild Install** and **User Install** (this enables `/pocket`
   to work outside of servers too)
6. Under **Default Install Settings**, add the `applications.commands` and
   `bot` scopes, and give the bot at least: Send Messages, Read Message
   History, Use Slash Commands

## 4. Set up your config

```bash
cp config.example.json/config.json
```

Open `config.json` and edit:

- `bot_name`, `version`, `author` — cosmetic, shown in the boot intro
- `intro` — your ASCII art and boot messages (or set `"enabled": false` to skip it)
- `personas` — each persona needs a `system_prompt`. **Exactly one** persona
  must have `"is_default": true`
- `status_rotation.messages` — the bot's rotating "Playing ..." status. `type`
  must be one of: `playing`, `watching`, `listening`, `streaming`, `competing`
- `pocket.open_to_all` — set to `false` and list Discord user IDs in
  `allowed_user_ids` to restrict who can use `/pocket`

The bot validates `config.json` on startup and will tell you exactly what's
wrong (missing default persona, empty prompts, bad status type, etc.) instead
of failing silently.

## 5. Set up your .env file

Create a file named exactly `.env` (not `env.txt`) in the same folder as
`Main.py`:

```
DISCORD_TOKEN=your_bot_token_here
OWNER_ID=your_discord_user_id
LM_STUDIO_MODEL=your-model-name-in-lm-studio
```

Your Discord user ID: enable Developer Mode in Discord (Settings → Advanced),
then right-click your own name → Copy User ID.

## 6. Start LM Studio

- Open LM Studio, load a model
- Go to the **Local Server** tab, start the server on port **1234**
- Make sure the model name matches `LM_STUDIO_MODEL` in your `.env`

## 7. Run the bot

```bash
python Main.py
```

If everything is set up correctly, you'll see the boot intro, then log lines
confirming the bot logged in and synced its slash commands.

---

## Troubleshooting

### `RuntimeError: DISCORD_TOKEN is missing`
Your `.env` file either doesn't exist, is misnamed, or doesn't contain
`DISCORD_TOKEN=...` on its own line. Double-check the filename is exactly
`.env` and it's in the same folder as `Main.py`.

### `discord.errors.LoginFailure: Improper token has been passed`
Your token is wrong, expired, or was reset. Go back to the Developer Portal →
Bot tab → **Reset Token**, copy the new one, and update `.env`.

### `ModuleNotFoundError: No module named 'discord'` (or `dotenv`, `openai`)
The required package isn't installed for the Python interpreter you're
running. Re-run:
```bash
pip install discord.py python-dotenv openai
```
If you have multiple Python versions installed, make sure you're installing
into the same one you use to run the bot (e.g. `python -m pip install ...`
using the exact same `python` command you use to start the bot).

### Bot logs in but never responds
- Check **Message Content Intent** is enabled both in the code (`intents.message_content = True`, already set) and in the Developer Portal (Bot tab → Privileged Gateway Intents)
- Make sure you're either @mentioning the bot or starting your message with a tag like `[CORTEX]`

### `/pocket` command doesn't show up in Discord
- Slash commands can take up to an hour to sync globally the first time; restarting the bot forces a sync but Discord's cache can still lag
- Confirm you checked **both** Guild Install and User Install in the Installation tab, and re-invite/reinstall the bot after changing that setting

### "⚠️ No connection to the local model"
- LM Studio's local server isn't running, or is running on a different port than `http://localhost:1234/v1`
- The model name in `.env` (`LM_STUDIO_MODEL`) doesn't match the model actually loaded in LM Studio — copy the exact name shown in LM Studio's server tab

### Config validation errors on startup
The bot checks `config.json` before starting and prints exactly what's
wrong — e.g. "No persona has `is_default: true`" or "status_rotation
message has invalid type". Fix the listed line in `config.json` and restart.

### I broke something and want to start fresh
Delete `config.json` (not `config.example.json`) and restart the bot — it
will regenerate `config.json` from the example file automatically.
