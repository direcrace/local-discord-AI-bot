# CORTEX 🧠

> A config-driven, multi-persona Discord bot powered by your own local LLM.
> No cloud API keys, no monthly bill, no "your account has been flagged for
> unusual activity" emails. Just your machine, your model, your rules.

Hey — thanks for checking this out. Seriously. Whether you're here to run
Cortex as-is, rip it apart for parts, or use it as a starting point for your
own project: welcome, and I hope it saves you a weekend of boilerplate.

---

## Why this exists

Most Discord AI bot templates either hardcode everything (so customizing
means digging through 500 lines of Python you didn't write) or wrap a paid
API (so running it costs you money the moment people start talking to it).

Cortex does neither:

- 🧩 **Fully config-driven** — personas, boot messages, status rotation,
  access control: all in `config.json`. Zero code changes needed to make it
  yours.
- 🖥️ **Runs on your own hardware** — talks to [LM Studio](https://lmstudio.ai)
  locally. Your conversations never leave your machine.
- 🎭 **Multiple personas, one bot** — tag-based routing (`[NOVA] what's a
  good coop game`) lets one bot wear as many hats as you want to give it.
- 📱 **Works outside servers too** — the `/pocket` slash command is
  user-installable, so it follows *you*, not just the server it's in.
- ✅ **Fails loudly, not silently** — bad config? You get a readable error
  telling you exactly what to fix, not a bot that just... doesn't respond.
- 🎬 **Comes with a boot intro** — because if you're gonna self-host a bot,
  it should at least look cool doing it.

---

## Before you start

Please actually read these two before running anything.... Yes, I know nobody reads these but PLEASE Read those:

License
requirements

---

## Quick start

```your terminal
pip install -r requirements.txt
cp config.example.json config.json
```

Then edit `config.json` to make it yours, set up your `.env` (see
`SETUP.md`), start LM Studio, and run:

```your terminal
python cortex_bot.py
```

That's it. Full details, including every error message you might see and
what it actually means, are in `requirements.md`.

---

## What you can customize without touching code

- Bot name, version, author, boot ASCII art + fake loading bars
- As many personas as you want, each with its own tone and system prompt
- Rotating status messages (`Playing ...`, `Watching ...`, etc.)
- Who's allowed to use `/pocket` (open to everyone, or an allowlist)
- Which local model it talks to, temperature, response length, history depth

All of it lives in `config.json`. If you break it, the bot will tell you
what's wrong instead of just crashing with a stack trace.

---

## Contributing / forking

Go for it — that's what a template is for. Just genuinely, please read the
license first so you know what "go for it" actually covers.

If you build something cool with this, I'd love to hear about it.
