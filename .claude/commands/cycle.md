---
description: Start a full plan-code-analyze cycle with agent teams
allowed-tools: Agent
---

# Full development cycle: $ARGUMENTS

Create an agent team to work on:

> **$ARGUMENTS**

## Team composition

Spawn these teammates using subagent definitions in `.claude/agents/`:

1. **Planner** (use `planner` agent type):
   - Research the topic with web search
   - Read `agents/shared-state/feedback-log.json` for past lessons
   - Write plan to `docs/plans/`
   - List any `uv add` commands needed for dependencies
   - Create task list in `agents/shared-state/task-list.json`
   - Notify team when plan is ready

2. **Coder** (use `coder` agent type):
   - Wait for planner to finish
   - Run `uv add` commands from the plan
   - Implement tasks from task-list.json
   - Run `uv run pytest` after each change
   - Notify when all tasks complete

3. **Analyst** (use `analyst` agent type):
   - Wait for coder to finish
   - Review code against plan's success criteria
   - Run `uv run pytest --cov=src` and `uv run ruff check .`
   - Write findings to `docs/analysis/`
   - Update `agents/shared-state/feedback-log.json`
   - If issues found, message the coder with specific fixes

## Coordination

- Planner starts immediately
- Coder waits for planner's "plan complete" signal
- Analyst waits for coder's "implementation complete" signal
- Each agent owns its directories — no cross-writing

## Your role as team lead

- Monitor progress, intervene if stuck
- Synthesize final result when all three finish
- Report: what was built, analyst findings, next steps
