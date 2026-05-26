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

Main model: `deepseek/deepseek-v4-pro` via OpenRouter. Falls back to `anthropic/claude-3.5-haiku` via `fallback_providers` if the primary is unavailable.

All four active auxiliary slots are pinned to OpenRouter. Model choice is graduated by task complexity:

| Task | Model | Why this tier |
|------|-------|--------------|
| Vision | `google/gemini-2.5-flash` | Image analysis needs real reasoning |
| Web Extract | `google/gemini-2.5-flash` | Web content summarization needs accuracy |
| Compression | `google/gemini-2.5-flash` | Context summaries must be coherent |
| Title Generation | `google/gemini-2.5-flash-lite` | Session titles are 3-6 words; lite is plenty |

```yaml
# Main model fallback (triggers on 429, 529, 503, connection failures)
fallback_providers:
- provider: openrouter
  model: anthropic/claude-3.5-haiku

# Auxiliary routing
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
    model: google/gemini-2.5-flash-lite

# Provider routing: spread auxiliary load across sub-providers
provider_routing:
  order:
  - Google
  - Anthropic
  require_parameters: true
```

Set with:

```bash
for task in vision web_extract compression; do
  hermes config set auxiliary.$task.provider openrouter
  hermes config set auxiliary.$task.model google/gemini-2.5-flash
done
hermes config set auxiliary.title_generation.provider openrouter
hermes config set auxiliary.title_generation.model google/gemini-2.5-flash-lite
```

## Model Selection Principle

Match the model tier to the task's reasoning surface:

- **flash** — tasks that need factual accuracy and coherent multi-paragraph output (summarization, image analysis, compression)
- **flash-lite** — tasks with a tiny reasoning surface where the output is a few tokens (titles, labels, classifications)
- **full models** (e.g., `claude-sonnet-4`) — don't use for auxiliary tasks; that's what the main model is for

## Other Auxiliary Tasks (Left on `auto`)

These are infrequent enough that `auto` is fine:

| Task | Config Key |
|------|-----------|
| Skills Hub | `auxiliary.skills_hub` |
| MCP helpers | `auxiliary.mcp` |
| Approval classification | `auxiliary.approval` |
| Kanban specify | `auxiliary.triage_specifier` |
| Kanban decomposition | `auxiliary.kanban_decomposer` |

## Sub-Provider Rate Limits

When OpenRouter routes through a sub-provider (e.g., Google), transient rate limits (HTTP 429 with `Retry-After`) from the sub-provider do NOT trigger Hermes's fallback — they're treated as retryable. To spread load across multiple sub-providers, use [[#provider-routing|Provider Routing]] within OpenRouter.

### Provider Routing (Active)

Provider routing is configured to try Google first, then Anthropic — all internally within OpenRouter, before Hermes ever sees a failure.

```yaml
provider_routing:
  order:
  - Google
  - Anthropic
  require_parameters: true
```

## Fallback Chain

When you pin an explicit provider and it hits a capacity error (quota exhausted, payment required), Hermes falls through to the main agent model as a safety net. If your main model can't handle that task (e.g., DeepSeek for vision), add a `fallback_chain`:

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
