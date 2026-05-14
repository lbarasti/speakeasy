# speakeasy

[![CI](https://github.com/lbarasti/speakeasy/actions/workflows/ci.yml/badge.svg)](https://github.com/lbarasti/speakeasy/actions/workflows/ci.yml)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.10--3.12-blue)
![License](https://img.shields.io/github/license/lbarasti/speakeasy)

> Running an AI coding agent, a long build, or a deploy? **Let a friendly voice notify you when a workflow needs your attention.**

Speakeasy is a local TTS server for macOS that any tool, script, or agent can call with a single `curl`.

📢 It speaks notifications out loud so you can step away without missing a thing.

## Quick start

```bash
# 1. Start the server
uv run speakeasy

# 2. In another terminal, speak something
curl -X POST localhost:8300/notify \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hello from speakeasy"}'
```

[Listen to the sample notification](https://raw.githubusercontent.com/lbarasti/speakeasy/main/assets/hello-from-speakeasy.mp3)

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python 3.10–3.12
- macOS with Apple Silicon

## Usage

### Server mode

```bash
# Start with default voice
uv run speakeasy

# Choose a voice
uv run speakeasy --personality laura

# Custom port
uv run speakeasy --port 9000
```

### One-shot mode

```bash
# Speak a message and exit
uv run speakeasy "The deployment is complete"

# List available voices
uv run speakeasy --list
```

## API

### `POST /notify`

Speak a message aloud.

```json
{ "message": "CI passed for PR 42" }
```

Returns `{ "status": "ok" }` after playback completes.

### Claude Code integration

Add this to your Claude Code hooks config and speakeasy will announce every permission request:

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:8300/permission",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

> [!TIP]
> Set `ANTHROPIC_API_KEY` for LLM-powered summaries of what the tool is about to do. Without it, you get a simpler static template.

## Voices

Voice configs live in the `personalities/` folder as markdown files. You'll find a few predefined ones and it's trivial to set up your own. The following options are supported:


| Field        | Purpose                                                                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**     | Display name, shown at startup                                                                                                              |
| **Speaker**  | Kokoro voice ID — the prefix determines language and gender (see below)                                                                     |
| **Language** | For English voices (`af/am/bf/bm`), tunes the espeak pronunciation fallback for unknown words. Non-English voices use their own phonemizer. |
| **Speed**    | Playback speed multiplier (1.0 = normal)                                                                                                    |


Run `uv run speakeasy --voices` to list all available voice IDs.

## Keypress interrupt

While audio is playing, press any key to stop it immediately. `Ctrl-C` exits the app.

## How it works

```
                        ┌───────────────────────┐
                        │   speakeasy (Python)   │
                        │       :8300            │
                        │                        │
 POST /notify ─────────>│  ┌─────────────────┐   │
 { message: "..." }     │  │   speaker.py    │   │
                        │  │                 │   │
 POST /permission ─────>│  │ tts.py ─────┐   │   │
 { tool_name, ... }     │  │  Kokoro MLX │   │   │
                        │  │             v   │   │
                        │  │ playback.py ────────>   afplay (macOS)
                        │  └─────────────────┘   │
                        │                        │
             stdin ────>│  any key = interrupt   │
                        └───────────────────────┘
```

## Tests

```bash
uv run pytest
```

The tests mock TTS model loading, Anthropic calls, and audio playback, so they run quickly without downloading models or playing sound.

There is also an opt-in integration test that loads the real Kokoro model and verifies WAV generation. It is skipped by default and only runs on macOS:

```bash
SPEAKEASY_RUN_TTS_INTEGRATION=1 uv run pytest -m integration
```

