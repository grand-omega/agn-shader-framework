# AGN Shader Framework

Multi-agent development framework powered by Claude Code Agent Teams.

## Quickstart

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone <this-repo>
cd gpu-agent-framework
uv sync

# 3. Verify everything works
uv run pytest
uv run ruff check .

# 4. Enable agent teams (one-time, in your global config)
mkdir -p ~/.claude
# Add to ~/.claude/settings.json:
# { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }

# 5. Start Claude Code
claude

# 6. Run a full cycle
> /cycle implement GPU memory buffer pool

# 7. Or just research
> /research best practices for DMA buffer management
```

## Project structure

```
├── CLAUDE.md                    # Shared context for all agents
├── pyproject.toml               # uv project config + ruff config
├── .python-version              # Python version pin
├── .claude/
│   ├── settings.json            # Permissions, hooks, agent teams flag
│   ├── agents/                  # Subagent role definitions
│   │   ├── planner.md
│   │   ├── coder.md
│   │   ├── analyst.md
│   │   ├── git-ops.md
│   │   ├── latex-report.md
│   │   └── dashboard.md
│   ├── commands/                # Slash commands
│   │   ├── cycle.md             # /cycle <task>
│   │   └── research.md          # /research <topic>
│   └── hooks/                   # Auto-format + uv reminders
│       ├── ruff-format.py
│       └── uv-reminder.py
├── agents/shared-state/
│   ├── task-list.json           # Shared task tracking
│   └── feedback-log.json        # Analyst → Planner feedback loop
├── docs/
│   ├── plans/                   # Planner writes here
│   ├── analysis/                # Analyst writes here
│   └── reports/                 # LaTeX reports here
├── src/                         # Production code
└── tests/                       # Test files
```

## Agent workflow

```
Planner ──plan──→ Coder ──code──→ Analyst
   ↑                                  │
   └──────── feedback-log.json ───────┘
```

## Toolchain

| Tool | Command |
|------|---------|
| Add package | `uv add <package>` |
| Add dev package | `uv add --group dev <package>` |
| Run script | `uv run python src/main.py` |
| Run tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` (also auto via hook) |
| Sync env | `uv sync` |
