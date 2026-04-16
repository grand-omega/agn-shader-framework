# Research: Claude Code Experimental Agent Teams

**Date**: 2026-04-15
**Topic**: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS — real-world usage, configuration patterns, pain points

---

## 1. What It Is

Agent Teams landed in Claude Code **v2.1.32 (2026-02-05)** as an experimental feature.
Enable it via:

```json
// ~/.claude/settings.json or project settings.json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

or `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in shell.

**Key distinction from subagents:**

| | Subagents | Agent Teams |
|---|---|---|
| Context | Own window; results summarized back | Own window; fully independent |
| Communication | Report to main agent only | Teammates message each other directly |
| Coordination | Main agent manages everything | Shared task list + self-coordination |
| Token cost | Lower | Significantly higher (linear scale) |
| Best for | Focused tasks, single result matters | Parallel exploration, debate, cross-layer |

---

## 2. Architecture

```
Team Lead (main session)
├── Shared task list (~/.claude/tasks/{team-name}/)
├── Mailbox (per-agent)
├── Teammate A (own 1M-token context)
├── Teammate B (own 1M-token context)
└── Teammate C (own 1M-token context)
```

- **Team config**: `~/.claude/teams/{team-name}/config.json` — runtime state, auto-generated, don't hand-edit
- **Task list**: `~/.claude/tasks/{team-name}/` — shared, file-locked to prevent race conditions
- **No project-level team config** — `.claude/teams/` is not recognized; use `CLAUDE.md` for cross-agent guidance
- Teammates load the same project context (CLAUDE.md, MCP servers, skills) as a regular session
- Lead's conversation history does NOT carry over to teammates

---

## 3. .claude/agents/ Configuration Format

Subagent definitions (`.claude/agents/` or `~/.claude/agents/`) can be reused as teammate types.
Format is **Markdown with YAML frontmatter**:

```markdown
---
name: security-reviewer
description: Use this agent when reviewing authentication, input validation, or token handling.
model: sonnet
tools:
  - Read
  - Grep
  - Glob
  - Bash
permissionMode: default
memory: user
color: red
---

You are a senior security engineer. Review code for vulnerabilities.
Focus on: injection attacks, token handling, session management, input validation.
Report findings with severity (critical/high/medium/low) and remediation steps.
```

**Scope priority** (highest to lowest):
1. Managed settings (org-wide)
2. `--agents` CLI flag (session only)
3. `.claude/agents/` (project-level, version-controlled)
4. `~/.claude/agents/` (user-level, all projects)
5. Plugin `agents/` directories

**Frontmatter fields**: `name`, `description`, `model`, `tools`, `disallowedTools`,
`permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `initialPrompt`,
`memory`, `effort`, `background`, `isolation`, `color`.

To use a definition as a teammate:
```text
Spawn a teammate using the security-reviewer agent type to audit the auth module.
```
The definition's `tools` allowlist is honored. Team coordination tools (`SendMessage`,
task tools) are always available to teammates even when `tools` restricts others.
Note: `skills` and `mcpServers` frontmatter fields are **not** applied when running as
a teammate — those load from project/user settings instead.

---

## 4. Common Agent Role Patterns (Community)

### Parallel Code Review (most common pattern)
```text
Create an agent team to review PR #142. Spawn three reviewers:
- One focused on security implications
- One checking performance impact
- One validating test coverage
Have them each review and report findings.
```

### Competing Hypotheses Debugging
```text
Users report the app exits after one message. Spawn 5 agent teammates to
investigate different hypotheses. Have them debate each other to disprove
each other's theories, like a scientific debate.
```

### Full-Stack Feature Development
- Backend agent: API endpoints
- Frontend agent: UI components
- Tests agent: integration tests
- Docs agent: API documentation

### Research + Devil's Advocate
- Researcher: searches web/docs
- Codebase explorer: searches existing patterns
- Devil's advocate: challenges conclusions after others report

### Role Libraries Seen in the Wild
- **wshobson/agents**: 182 specialized agents across 77 plugins — architect-review,
  backend-architect, security-auditor, python-pro, kubernetes-architect, llm-specialist,
  incident-response-engineer, etc.
- **rsmdt/the-startup**: Chief, Analyst, Architect, Software Engineer, QA Engineer,
  Designer, Platform Engineer, Meta Agent — coordinated by `/specify`, `/validate`,
  `/implement`, `/review`, `/debug`, `/document` slash commands
- **drbscl/dream-team**: "Assemble your dream team" — role-based preset configurations

---

## 5. Slash Commands Built for Agent Teams

Community-built slash commands (dropped in `.claude/commands/` as Markdown files):

- `/cycle` — plan-code-analyze loop with agent teams
- `/research` — parallel web + codebase + devil's advocate pattern
- `/review` — multi-agent code review (security/performance/coverage simultaneously)
- `/team-feature` — full-stack feature with domain-separated teammates
- `/team-debug` — competing hypotheses debugging
- `/specify` — PRD + SDD + PLAN via analyst + architect agents
- `/implement` — phase-by-phase with approval gates
- `/conductor` — context-driven orchestration workflow

---

## 6. Coordination Mechanics

### Task lifecycle
- Tasks: pending → in progress → completed
- Dependencies: a pending task with unresolved deps cannot be claimed until deps complete
- File locking on task claim prevents race conditions
- Teammates self-claim after finishing a task

### Hooks for quality gates
- `TeammateIdle` — exit code 2 to keep teammate working with feedback
- `TaskCreated` — exit code 2 to block task creation
- `TaskCompleted` — exit code 2 to block completion (enforce quality)

### Display modes
- **in-process**: all teammates in one terminal; `Shift+Down` to cycle, `Ctrl+T` for task list
- **tmux split panes**: each teammate in own pane; `~/.claude.json: { "teammateMode": "tmux" }`
- `--teammate-mode in-process` flag for per-session override
- iTerm2 support via `it2` CLI + Python API enabled

### Plan approval flow
```text
Spawn an architect teammate to refactor the auth module.
Require plan approval before they make any changes.
```
Teammate works read-only until lead approves. Lead can reject with feedback; teammate
revises and resubmits. Useful for risky/destructive changes.

---

## 7. Pain Points (Confirmed by Community)

| Pain Point | Detail | Workaround |
|---|---|---|
| No session resumption | `/resume`/`/rewind` don't restore in-process teammates | Spawn new teammates after resuming |
| Task status lag | Teammates sometimes fail to mark tasks complete, blocking dependents | Manually update task status or tell lead to nudge |
| Lead implements instead of delegating | Lead starts doing work itself | Explicitly say "delegate this to teammates; wait for them" |
| File conflicts | Two teammates edit same file → overwrites | Assign each teammate non-overlapping file sets |
| Token cost scales badly | 3-agent team ~3-7x tokens vs single session; prompt cache bugs found in binary (10-20x silent inflation) | Use Sonnet/Haiku for routine teammates; scope tasks tightly |
| Context isolation | Agents don't share context window; only explicit messages bridge gap | Embed all critical context into spawn prompts and task descriptions |
| Shutdown is slow | Teammates finish current request before shutting down | Clean up proactively; always use lead to run cleanup |
| One team per session | Lead cannot manage multiple teams | Clean up current team before starting new one |
| No nested teams | Teammates cannot spawn sub-teams | Design flat team structures |
| iTerm2 pane splitting unreliable | Known issues with split-pane mode | Use tmux instead |
| Model lock (as of Mar 2026) | All agents run same model (Opus 4.6 required) | Community requests role-based model selection |
| Permission prompts bubble up | Teammate permission requests interrupt lead | Pre-approve common operations before spawning |

---

## 8. Official Best Practices (Anthropic Docs)

- **Team size**: 3-5 teammates is the sweet spot; beyond 5 coordination overhead exceeds gains
- **Task sizing**: 5-6 tasks per teammate; self-contained units with a clear deliverable
- **Context**: embed task-specific details in spawn prompt — teammates don't inherit lead's history
- **Start with research/review**: before parallel implementation, validate value with read-only tasks
- **File ownership**: one teammate, one directory; no shared file writes
- **Monitor actively**: redirect stuck agents; don't run unattended for long
- **Plan approval**: use for risky tasks to catch bad approaches before damage is done
- **Token economics**: only justified when "time saved > 2x token cost increase" (community rule of thumb)

---

## 9. Devil's Advocate: Is It Actually Worth It?

**Risks and counterarguments:**

1. **Token cost is brutal.** 3-7x multiplier. Two known prompt cache bugs silently inflate costs
   further. Anthropic publicly acknowledged quotas running out faster than expected (March 2026).
   At API prices a heavy session can hit $15K/8 months vs $800 on Max plan.

2. **Context isolation undermines "collaboration."** Agents only share what's explicitly messaged.
   The "debate" pattern requires disciplined prompt engineering or agents talk past each other.

3. **Experimental = unstable.** February 2026 update introduced regressions in context handling,
   tool-use consistency, and long-session stability. No session resumption for in-process teammates.

4. **Lead management overhead.** The lead can only handle one team. Can't delegate team creation.
   No nested teams. Leadership is fixed at creation — you can't promote a teammate.

5. **Subagents often sufficient.** For most parallel tasks where you only need results (not debate),
   subagents are cheaper and simpler. The "research + summarize" pattern works fine with subagents.

6. **Validated ROI is narrow.** The cases with documented gains (Fountain: 50% faster screening;
   CRED: 2x execution speed) involve specific parallel-investigation scenarios, not general coding.

**Where it genuinely wins:**
- Parallel code review with truly independent lenses (security vs. perf vs. coverage)
- Multi-hypothesis debugging where anchoring bias is a real risk
- Large refactors with clean file-boundary separation
- Cross-domain features (frontend + backend + tests owned by specialists simultaneously)

---

## 10. Key GitHub Repos / Resources

- [Official docs](https://code.claude.com/docs/en/agent-teams) — most authoritative source
- [wshobson/agents](https://github.com/wshobson/agents) — 182 agents, 77 plugins, orchestrators
- [rsmdt/the-startup](https://github.com/rsmdt/the-startup) — full agentic startup workflow
- [drbscl/dream-team](https://github.com/drbscl/dream-team) — preset team configurations
- [jessepwj/CCteam-creator](https://github.com/jessepwj/CCteam-creator) — team orchestration skill
- [cs50victor/claude-code-teams-mcp](https://github.com/cs50victor/claude-code-teams-mcp) — use agent teams orchestration with any harness
- [777genius/claude_agent_teams_ui](https://github.com/777genius/claude_agent_teams_ui) — kanban UI for agent teams
- [disler/claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability) — real-time monitoring via hooks
- [FlorianBruniaux/claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) — comprehensive guide
- [obra/superpowers #429](https://github.com/obra/superpowers/issues/429) — TeammateTool, SendMessage, TaskList integration

---

## 11. Implications for This Project (GPU Agent Framework)

Given our CLAUDE.md agent roles (Planner/Coder/Analyst/Git Ops/LaTeX/Dashboard), agent teams
are a natural fit for:

- **Parallel analysis**: Analyst reviewing multiple modules simultaneously
- **Plan + implement loop**: Planner defines tasks → Coder teammates implement in parallel
- **Cross-layer GPU work**: separate teammates for kernel code, test harness, benchmarks

Recommended approach:
1. Define agent roles as `.claude/agents/` markdown files (planner.md, coder.md, analyst.md)
2. Use CLAUDE.md (already present) to set shared context all teammates auto-load
3. Use `docs/plans/` as the shared artifact space for cross-agent coordination
4. Start with review tasks before parallel implementation to calibrate token costs
5. Keep `agents/shared-state/task-list.json` as the human-readable analog; the actual
   agent team task list lives in `~/.claude/tasks/`
