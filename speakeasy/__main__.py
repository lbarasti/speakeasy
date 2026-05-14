from __future__ import annotations

import argparse
import os


def _personalities_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "personalities")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="speakeasy",
        description="Minimal text-to-speech notification service",
    )
    parser.add_argument(
        "--personality",
        default=None,
        help="Voice name or path (default: laura)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8300")),
        help="HTTP server port (default: 8300)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available personalities and exit",
    )
    parser.add_argument(
        "--voices",
        action="store_true",
        help="List available Kokoro voice IDs and exit",
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to speak and exit (one-shot mode). If omitted, starts the server.",
    )

    args = parser.parse_args()
    personalities_dir = _personalities_dir()

    from speakeasy.personality import list_personalities, load_personality, resolve_personality

    if args.list:
        from speakeasy.console import console
        names = list_personalities(personalities_dir)
        console.print("Available personalities:", ", ".join(names))
        return

    if args.voices:
        from speakeasy.console import console
        from speakeasy.tts import load_model, list_voices
        load_model()
        console.print("Available voices:", ", ".join(list_voices()))
        return

    personality_path = resolve_personality(args.personality, personalities_dir)
    personality = load_personality(personality_path)

    from speakeasy.console import dim, info
    info(f"Personality: {personality.name} ({personality.speaker}, {personality.language}, {personality.speed}x)")

    from speakeasy.tts import load_model
    load_model()

    text = " ".join(args.text).strip() if args.text else ""

    if text:
        from speakeasy.speaker import speak
        speak(text)
        return

    # Server mode
    from speakeasy.interrupt import start_interrupt_listener
    from speakeasy.speaker import interrupt

    available = list_personalities(personalities_dir)
    dim(f"Available: {', '.join(available)}  [--personality <name>]")

    start_interrupt_listener(interrupt)

    from speakeasy.server import create_app
    import uvicorn

    app = create_app()
    info(f"Listening on http://localhost:{args.port}")
    dim("Press any key to interrupt playback. Ctrl-C to quit.\n")

    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
