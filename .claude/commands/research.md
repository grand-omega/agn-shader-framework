---
description: Research a topic with parallel agents
allowed-tools: Agent, WebSearch, WebFetch, Read, Write, Grep, Glob
---

# Research: $ARGUMENTS

Create an agent team to research from multiple angles:

> **$ARGUMENTS**

Spawn 3 teammates:

1. **Web researcher**: Search web for best practices, packages on PyPI,
   documentation, and community solutions.

2. **Codebase explorer**: Search existing code in `src/` and `docs/`
   for related patterns and prior work.

3. **Devil's advocate**: After the others report, challenge their
   conclusions. Find risks, edge cases, alternatives.

Have them debate, then synthesize into:
`docs/plans/research-YYYY-MM-DD-<topic>.md`
