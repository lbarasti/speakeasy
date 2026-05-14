# speakeasy

A minimal text-to-speech notification service. Speaks alerts, announces Claude Code permission requests, and shuts up when you press a key.

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

## Quick start

```bash
# 1. Start the server
uv run speakeasy

# 2. In another terminal, speak something
curl -X POST localhost:8300/notify \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hello from speakeasy"}'
```

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python 3.10–3.12
- macOS (uses `afplay` for audio playback)
- Optional: `ANTHROPIC_API_KEY` for LLM-powered permission summaries

## Usage

### Server mode

```bash
# Start with default voice
uv run speakeasy

# Choose a voice
uv run speakeasy --personality nicola

# Custom port
uv run speakeasy --port 9000
```

### One-shot mode

```bash
# Speak a message and exit
uv run speakeasy "The deployment is complete"

# With a specific voice
uv run speakeasy --personality nicola "Ciao, come stai?"

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

### `POST /permission`

Handle a Claude Code permission hook. Summarises the request using an LLM (or a static template if no API key is set), speaks it aloud, and returns `"ask"` so the user decides in the terminal.

```json
{
  "session_id": "abc",
  "cwd": "/Users/me/code/myproject",
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf dist" }
}
```

Returns:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": { "behavior": "ask" }
  }
}
```

### `GET /health`

Returns `{ "status": "ok" }`.

## Voices

Voice configs live in the `personalities/` folder as markdown files:

```markdown
# Voice

## Name
Nicola

## Speaker
im_nicola

## Language
italian

## Speed
1.1
```

| Field | Purpose |
|---|---|
| **Name** | Display name, shown at startup |
| **Speaker** | Kokoro voice ID — the prefix determines language and gender (see below) |
| **Language** | For English voices (`af/am/bf/bm`), tunes the espeak pronunciation fallback for unknown words. Non-English voices use their own phonemizer. |
| **Speed** | Playback speed multiplier (1.0 = normal) |

### Speaker prefixes

| Prefix | Language | Gender |
|---|---|---|
| `af` / `am` | American English | female / male |
| `bf` / `bm` | British English | female / male |
| `ef` / `em` | Spanish | female / male |
| `ff` | French | female |
| `hf` / `hm` | Hindi | female / male |
| `if` / `im` | Italian | female / male |
| `jf` / `jm` | Japanese | female / male |
| `pf` / `pm` | Portuguese | female / male |
| `zf` / `zm` | Chinese | female / male |

Run `uv run speakeasy --voices` to list all available voice IDs.

### Included voices

| Name | Voice ID | Language |
|---|---|---|
| `default` | `am_adam` | American English |
| `laura` | `bf_emma` | British English |
| `nicola` | `im_nicola` | Italian |

## Keypress interrupt

While audio is playing, press any key to stop it immediately. `Ctrl-C` exits the app.

## Claude Code permission hook

Add to your Claude Code hooks config to have speakeasy announce permission requests:

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "type": "command",
        "command": "curl -s -X POST http://localhost:8300/permission -H 'Content-Type: application/json' -d \"$(cat)\""
      }
    ]
  }
}
```
