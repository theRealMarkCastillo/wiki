---
title: Auxiliary Model Routing
created: 2026-05-25
updated: 2026-05-25
schema_version: 1
type: concept
tags: [architecture, how-to, tool, system]
confidence: high
---

# Auxiliary Model Routing

When your main model doesn't support vision, or when you want cheaper/specialized models for side-tasks, Hermes lets you pin separate providers per auxiliary task. The default is `auto` for everything — it works but walks a provider chain on every call.

## Current Reef Configuration

All four auxiliary slots are pinned to OpenRouter with `google/gemini-2.5-flash`:

| Task | What It Does | Config Key |
|------|-------------|-----------|
| Vision | Image analysis, browser screenshots | `auxiliary.vision` |
| Web Extract | Web page content summarization | `auxiliary.web_extract` |
| Compression | Context compression summaries (automatic) | `auxiliary.compression` |
| Title Generation | Session title summaries | `auxiliary.title_generation` |

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: google/gemini-2.5-flash
  web_extract:
    provider: openrouter
    model: google/gemini-2.5-flash
  compression:
    provider: openrouter
    model: google/gemini-2.5-flash
  title_generation:
    provider: openrouter
    model: google/gemini-2.5-flash
```

Set with:

```bash
for task in vision web_extract compression title_generation; do
  hermes config set auxiliary.$task.provider openrouter
  hermes config set auxiliary.$task.model google/gemini-2.5-flash
done
```

## Why Pin These Four?

- **vision** — main model (DeepSeek v4) doesn't support vision; `auto` would walk the chain every call
- **web_extract** — fired on every doc pull; a flash model saves tokens vs. running summarization through the main reasoning model
- **compression** — runs automatically when context fills up; pinning avoids the chain walk mid-session
- **title_generation** — fires at session start; low stakes, fast model is ideal

## Other Auxiliary Tasks (Left on `auto`)

These are infrequent enough that `auto` is fine:

| Task | Config Key |
|------|-----------|
| Skills Hub | `auxiliary.skills_hub` |
| MCP helpers | `auxiliary.mcp` |
| Approval classification | `auxiliary.approval` |
| Kanban specify | `auxiliary.triage_specifier` |
| Kanban decomposition | `auxiliary.kanban_decomposer` |

## Fallback Chain

When you pin an explicit provider and it hits a capacity error (quota exhausted, payment required), Hermes falls through to the main agent model as a safety net. If your main model can't handle that task (e.g., DeepSeek for vision), that safety net won't help — add a `fallback_chain`:

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: google/gemini-2.5-flash
    fallback_chain:
      - provider: anthropic
        model: claude-sonnet-4-6
```

## Session Restart Required

Config changes to `auxiliary.*` take effect on the next session. `/reset` or start a fresh `hermes` session after making changes.

## See Also

- [[concepts/session-opening-routine|Session Opening Routine]] — steps to verify config on session start
- [[concepts/cron-schedule-infrastructure|Cron Schedule & Infrastructure]] — where auxiliary tasks fit in the daily rhythm
- [Fallback Providers](https://hermes-agent.nousresearch.com/docs/user-guide/features/fallback-providers) — full upstream docs
