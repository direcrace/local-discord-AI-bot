"""
Cortex — Multi-Persona Discord Bot Template
=============================================
Fully config-driven: personas, status rotation, boot intro, and Pocket
access are all defined in config.json (see config.example.json). No code
changes needed to personalize this bot — copy config.example.json to
config.json and edit it.

See SETUP.md for install instructions and troubleshooting.
"""
import json
import logging
import os
import re
from collections import defaultdict, deque
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from openai import OpenAI

from config_loader import load_config, get_default_persona_key
from intro import show_intro


# Setup & Config


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
CONFIG = load_config()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

PERSONAS = CONFIG["personas"]
DEFAULT_PERSONA = get_default_persona_key(CONFIG)

POCKET_CFG = CONFIG["pocket"]
POCKET_ALLOWED_USERS: set[int] = set(POCKET_CFG.get("allowed_user_ids", []))
POCKET_OPEN_TO_ALL = POCKET_CFG.get("open_to_all", True) or not POCKET_ALLOWED_USERS

LLM_CFG = CONFIG["llm"]
MAX_HISTORY_MESSAGES = LLM_CFG["max_history_messages"]
MAX_TOKENS_RESPONSE = LLM_CFG["max_tokens_response"]

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(CONFIG["bot_name"])

llm_client = OpenAI(base_url=LLM_CFG["base_url"], api_key="lm-studio")

TAG_PATTERN = re.compile(
    r"\[\s*(" + "|".join(re.escape(k) for k in PERSONAS.keys()) + r")\s*\]",
    re.IGNORECASE,
)

BOT_START_TIME = None


# Status Rotation (config-driven)


ACTIVITY_TYPE_MAP = {
    "playing": discord.ActivityType.playing,
    "watching": discord.ActivityType.watching,
    "listening": discord.ActivityType.listening,
    "streaming": discord.ActivityType.streaming,
    "competing": discord.ActivityType.competing,
}


@tasks.loop(minutes=CONFIG["status_rotation"].get("interval_minutes", 5))
async def rotate_status():
    import random

    messages = CONFIG["status_rotation"].get("messages", [])
    if not messages:
        return
    entry = random.choice(messages)
    activity_type = ACTIVITY_TYPE_MAP.get(entry["type"], discord.ActivityType.playing)
    text = entry["text"].format(guild_count=len(bot.guilds))
    await bot.change_presence(activity=discord.Activity(type=activity_type, name=text))



# Shared History pro Channel (Guild-Channels UND Pocket-Kontexte)


HISTORY: dict[int, deque] = defaultdict(lambda: deque(maxlen=MAX_HISTORY_MESSAGES))
HISTORY_FILE = os.path.join(BASE_DIR, "ergo_history.json")


def save_history():
    serializable = {str(cid): list(msgs) for cid, msgs in HISTORY.items()}
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for cid, msgs in raw.items():
            HISTORY[int(cid)] = deque(msgs, maxlen=MAX_HISTORY_MESSAGES)
        log.info("History loaded (%d contexts).", len(HISTORY))
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Could not load history: %s", e)



# Discord Bot Setup


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    global BOT_START_TIME
    BOT_START_TIME = datetime.now()
    load_history()
    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    log.info("Personas loaded: %s", ", ".join(PERSONAS.keys()))
    if POCKET_OPEN_TO_ALL:
        log.info("Pocket: OPEN to everyone.")
    else:
        log.info("Pocket: restricted to %d user(s).", len(POCKET_ALLOWED_USERS))

    try:
        synced = await bot.tree.sync()
        log.info("Slash commands synced: %d", len(synced))
    except Exception as e:
        log.error("Slash command sync failed: %s", e)

    if CONFIG["status_rotation"].get("enabled", True) and not rotate_status.is_running():
        rotate_status.start()


def detect_persona(content: str) -> tuple[str, str]:
    stripped = content.strip()
    match = re.match(
        r"^\[\s*(" + "|".join(re.escape(k) for k in PERSONAS.keys()) + r")\s*\]\s*(.*)",
        stripped,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        persona_key = match.group(1).upper()
        remaining = match.group(2).strip()
        return persona_key, remaining
    return DEFAULT_PERSONA, stripped


async def generate_response(persona_key: str, context_id: int, user_display: str, user_message: str) -> str:
    persona = PERSONAS[persona_key]
    history_messages = list(HISTORY[context_id])

    messages = [{"role": "system", "content": persona["system_prompt"]}]
    for msg in history_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": f"{user_display}: {user_message}"})

    try:
        completion = llm_client.chat.completions.create(
            model=LLM_CFG["model"],
            messages=messages,
            max_tokens=MAX_TOKENS_RESPONSE,
            temperature=LLM_CFG["temperature"],
        )
        reply = completion.choices[0].message.content.strip()
    except Exception as e:
        log.error("LM Studio request failed: %s", e)
        return "⚠️ No connection to the local model. Check if LM Studio is running and the model is loaded."

    HISTORY[context_id].append({"role": "user", "content": f"{user_display}: {user_message}"})
    HISTORY[context_id].append({"role": "assistant", "content": reply})
    save_history()

    return reply



# Guild behaviour: Mention / [TAG]


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    mentioned = bot.user in message.mentions
    stripped_content = message.content.strip()
    has_tag = bool(re.match(
        r"^\[\s*(" + "|".join(re.escape(k) for k in PERSONAS.keys()) + r")\s*\]",
        stripped_content,
        re.IGNORECASE,
    ))

    if not (mentioned or has_tag):
        await bot.process_commands(message)
        return

    content = message.content
    for mention in message.mentions:
        content = content.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
    content = content.strip()

    persona_key, clean_content = detect_persona(content)

    if not clean_content:
        await message.reply(
            f"Hey, I'm {PERSONAS[persona_key]['display_name']}. What's up?",
            mention_author=False,
        )
        return

    async with message.channel.typing():
        reply = await generate_response(
            persona_key=persona_key,
            context_id=message.channel.id,
            user_display=message.author.display_name,
            user_message=clean_content,
        )

    persona_name = PERSONAS[persona_key]["display_name"]
    formatted = f"**[{persona_name}]** {reply}"
    if len(formatted) > 2000:
        formatted = formatted[:1990] + "…"

    await message.reply(formatted, mention_author=False)
    await bot.process_commands(message)



# Pocket -- user-installable slash command (config-gated)


POCKET_AI_CHOICES = [
    app_commands.Choice(name=data["display_name"], value=key)
    for key, data in PERSONAS.items()
]


@bot.tree.command(
    name="pocket",
    description="Ask Cortex anything, anywhere (DMs, servers, even where the bot isn't a member).",
)
@app_commands.describe(
    ai="Which persona should answer?",
    request="Your question or request",
)
@app_commands.choices(ai=POCKET_AI_CHOICES)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def pocket_command(
    interaction: discord.Interaction,
    ai: app_commands.Choice[str],
    request: str,
):
    if not POCKET_CFG.get("enabled", True):
        await interaction.response.send_message("🔒 Pocket is disabled in this bot's config.", ephemeral=True)
        return

    if not POCKET_OPEN_TO_ALL and interaction.user.id not in POCKET_ALLOWED_USERS:
        await interaction.response.send_message("🔒 Pocket is locked for your account.", ephemeral=True)
        return

    persona_key = ai.value
    await interaction.response.defer(thinking=True)

    context_id = interaction.channel_id or interaction.user.id

    reply = await generate_response(
        persona_key=persona_key,
        context_id=context_id,
        user_display=interaction.user.display_name,
        user_message=request,
    )

    persona_name = PERSONAS[persona_key]["display_name"]
    formatted = f"**[{persona_name} • 📱 Pocket]** {reply}"
    if len(formatted) > 2000:
        formatted = formatted[:1990] + "…"

    await interaction.followup.send(formatted)



# -Owner-only utility commands-

@bot.command(name="personas")
async def list_personas(ctx: commands.Context):
    lines = ["**Available personas:**"]
    for key, data in PERSONAS.items():
        marker = " (default)" if key == DEFAULT_PERSONA else ""
        lines.append(f"`[{key}]` -> {data['display_name']}{marker}")
    await ctx.send("\n".join(lines))


@bot.command(name="clearhistory")
async def clear_history(ctx: commands.Context):
    if ctx.author.id != OWNER_ID:
        await ctx.send("You don't have permission for that.")
        return
    HISTORY[ctx.channel.id].clear()
    save_history()
    await ctx.send("History for this channel has been cleared.")


@bot.command(name="pocketstatus")
async def pocket_status(ctx: commands.Context):
    if ctx.author.id != OWNER_ID:
        await ctx.send("You don't have permission for that.")
        return
    if POCKET_OPEN_TO_ALL:
        await ctx.send("📱 Pocket is currently **open to everyone**.")
    else:
        await ctx.send(
            f"📱 Pocket is currently **restricted** to {len(POCKET_ALLOWED_USERS)} "
            f"user(s): {', '.join(str(u) for u in POCKET_ALLOWED_USERS)}"
        )



# Entry Point


if __name__ == "__main__":
    show_intro(CONFIG)

    if not DISCORD_TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN is missing. Check your .env file "
            "(the filename must be exactly '.env', not 'env.txt' or similar)."
        )
    bot.run(DISCORD_TOKEN)
