---
description: Start a full plan-code-analyze cycle with agent teams
allowed-tools: Agent, TeamCreate, TeamDelete, SendMessage, TaskCreate, TaskGet, TaskList, TaskUpdate
---

# Full development cycle: $ARGUMENTS

> **$ARGUMENTS**

## Step 1: Create the team and tasks

Call `TeamCreate` with team_name `"cycle"`.

Then create these four tasks with dependencies:

1. **TaskCreate**: "Plan: $ARGUMENTS"
   - Description: Research the topic, write plan to docs/plans/, create implementation subtasks
   - No blockers

2. **TaskCreate**: "Implement: $ARGUMENTS"
   - Description: Read plan, install deps, implement code in src/ and tests in tests/
   - `addBlockedBy`: [task 1]

3. **TaskCreate**: "Review: $ARGUMENTS"
   - Description: Review code against plan success criteria, write analysis, verdict
   - `addBlockedBy`: [task 2]

4. **TaskCreate**: "Commit: $ARGUMENTS"
   - Description: Run pre-commit checks, stage files, create conventional commit
   - `addBlockedBy`: [task 3]

## Step 2: Spawn all four teammates at once

Spawn all four in a single message using the Agent tool with `team_name: "cycle"`:

1. **planner** — `subagent_type: "planner"`, `team_name: "cycle"`, `name: "planner"`
2. **coder** — `subagent_type: "coder"`, `team_name: "cycle"`, `name: "coder"`
3. **analyst** — `subagent_type: "analyst"`, `team_name: "cycle"`, `name: "analyst"`
4. **git-ops** — `subagent_type: "git-ops"`, `team_name: "cycle"`, `name: "git-ops"`

Each teammate's spawn prompt should include the task description from
$ARGUMENTS so they have full context without needing the lead's history.

**Hub-and-spoke coordination:** Each teammate's spawn prompt MUST include:
> "When you finish your task, message the team lead with your results.
> Do NOT poll TaskList waiting for tasks to unblock — the team lead
> will message you when it's your turn."

Only the **planner** should start working immediately. The **coder**,
**analyst**, and **git-ops** prompts must say:
> "Wait for the team lead to message you before starting work.
> Do not poll or sleep-loop."

## Step 3: Orchestrate handoffs (hub-and-spoke)

The team lead is the central coordinator. All communication flows
through the lead — teammates do NOT message each other directly
(except analyst → coder revision feedback, relayed by lead).

When each teammate messages you with completion:

1. **Planner completes** → lead messages **coder**: "The plan is at
   `docs/plans/<file>`. Your task is unblocked — start implementing."
2. **Coder completes** → lead messages **analyst**: "Implementation
   is done. Files: <list>. Your task is unblocked — start review."
3. **Analyst completes (approved)** → lead messages **git-ops**:
   "Review approved. Your task is unblocked — run checks and commit."
4. **Analyst completes (needs_revision)** → lead messages **coder**
   with the analyst's fix list. When coder finishes, lead messages
   **analyst** to re-review. Max 2 revision rounds — if still failing,
   report to user.

Do NOT read files the teammates are writing. Do NOT re-run tests.
Only relay messages and dispatch the next agent.

## Step 4: Shutdown and cleanup

After git-ops confirms the commit:
1. Send `{"type": "shutdown_request"}` to each teammate individually
   (planner, coder, analyst, git-ops)
2. Wait for each to respond with
   `{"type": "shutdown_response", "approve": true}` — this terminates
   their process
3. Call `TeamDelete` to clean up team resources
4. Report to the user:
   - What was built (files created/modified)
   - Analyst verdict and key findings
   - Git commit hash
   - Any remaining issues or next steps
