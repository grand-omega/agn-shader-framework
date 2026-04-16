#!/usr/bin/env python3
"""PostToolUse hook: auto-format Python files with ruff after every edit."""

import json
import subprocess
import sys


def main():
    data = json.load(sys.stdin)

    # Extract the file path from the tool input
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only format Python files
    if not file_path.endswith(".py"):
        return

    # Run ruff format on the edited file
    subprocess.run(
        ["uv", "run", "ruff", "format", file_path],
        capture_output=True,
    )

    # Run ruff check with auto-fix (safe fixes only)
    subprocess.run(
        ["uv", "run", "ruff", "check", "--fix", file_path],
        capture_output=True,
    )


if __name__ == "__main__":
    main()
