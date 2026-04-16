#!/usr/bin/env python3
"""UserPromptSubmit hook: remind Claude to use uv instead of pip/python."""

import json
import sys


def main():
    data = json.load(sys.stdin)
    prompt = data.get("prompt", "").lower()

    reminders = []

    if "pip install" in prompt or "pip3 install" in prompt:
        reminders.append("Use 'uv add <package>' instead of pip install.")

    if "python " in prompt and "uv run" not in prompt:
        reminders.append("Use 'uv run <script>' instead of bare python.")

    if "pip freeze" in prompt:
        reminders.append("Dependencies are in pyproject.toml. Use 'uv pip list' if needed.")

    if "virtualenv" in prompt or "venv" in prompt:
        reminders.append("uv manages the venv automatically. Just use 'uv sync'.")

    if "requirements.txt" in prompt:
        reminders.append("This project uses pyproject.toml, not requirements.txt.")

    if reminders:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": " ".join(reminders),
            }
        }
        json.dump(output, sys.stdout)


if __name__ == "__main__":
    main()
