---
title: Auxiliary Vision Routing
created: 2026-05-25
updated: 2026-05-25
schema_version: 1
type: concept
tags: [architecture, how-to, tool, system]
confidence: high
---

# Auxiliary Vision Routing

When your main model doesn't support vision (e.g., DeepSeek v4), Hermes needs a separate provider for image analysis — browser screenshots, `vision_analyze` calls, OCR. This page documents the configuration pattern.

## Why This Matters

The default setting is `auxiliary.vision.provider: auto`, which walks a provider chain:

```
Main model (if vision-capable) → OpenRouter → Nous Portal → Codex OAuth →
Anthropic → Custom endpoint → give up
```

If your main model isn't vision-capable, `auto` skips it and tries the next link. This works but is slow — every vision call walks the chain from scratch. Explicitly pinning a vision provider avoids the search.

## Current Reef Configuration

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: google/gemini-2.5-flash
```

Set with:

```bash
hermes config set auxiliary.vision.provider openrouter
hermes config set auxiliary.vision.model google/gemini-2.5-flash
```

## How to Set It (for New Companions)

Replace the model with whatever vision-capable model you have access to:

| Provider | Example model | Needs |
|----------|--------------|-------|
| `openrouter` | `google/gemini-2.5-flash` | `OPENROUTER_API_KEY` |
| `openrouter` | `openai/gpt-4o` | `OPENROUTER_API_KEY` |
| `anthropic` | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| `custom` | `qwen2.5-vl` | `base_url` + `key_env` |

## Fallback Chain

When you pin an explicit provider and it hits a capacity error (quota exhausted, payment required), Hermes falls through to the main agent model as a safety net. If your main model isn't vision-capable, that safety net won't help — add a `fallback_chain`:

```yaml
auxiliary:
  vision:
    provider: anthropic
    model: claude-sonnet-4-6
    fallback_chain:
      - provider: openrouter
        model: google/gemini-2.5-flash
```

## Session Restart Required

Config changes to `auxiliary.*` take effect on the next session. `/reset` or start a fresh `hermes` session after making changes.

## See Also

- [[concepts/session-opening-routine|Session Opening Routine]] — steps to verify config on session start
- [[concepts/cron-schedule-infrastructure|Cron Schedule & Infrastructure]] — where auxiliary tasks fit in the daily rhythm
- [Fallback Providers](https://hermes-agent.nousresearch.com/docs/user-guide/features/fallback-providers) — full upstream docs
