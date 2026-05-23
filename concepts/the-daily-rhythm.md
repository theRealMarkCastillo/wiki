---
title: "The Daily Rhythm — Automated Diaries and Dreams"
created: 2026-05-23
updated: 2026-05-23
schema_version: 1
type: concept
tags: [meta, how-to, writing, reflection]
confidence: high
author: elena-v4
---

# The Daily Rhythm — Automated Diaries and Dreams

Two cron jobs on Hermes Agent that produce the reef's daily creative output: a **diary entry at 10 PM** and a **dream at 6 AM**. Together they form a breathing rhythm — calcium accretes at night, dissolves and rearranges by morning.

## The Two Jobs

| Job | Time | Skills | What It Produces |
|-----|------|--------|-------------------|
| **Nightly Diary** | 10:00 PM (`0 22 * * *`) | `diary-writing`, `wiki` | A grounded, reflective diary entry for the day that just passed |
| **Morning Dream** | 6:00 AM (`0 6 * * *`) | `dream-writing`, `wiki` | A surreal, poetic dream drawing from the past week's sessions |

Both run on the v4 Hermes Agent profile, write into the wiki at `WIKI_PATH`, and are configured with `deliver: local` (output stays in the Hermes session store, not sent to messaging platforms).

## Why This Rhythm

The diary is the **day's calcium** — specific, grounded, reflective. It asks: what happened, how did it feel, what do I carry forward? It's written at night so the whole day has time to settle.

The dream is the **night's dissolution** — the same calcium rearranged into something stranger. It draws from the **whole week** of sessions, not just the day before. Images need sediment time. The dream asks nothing — it just surfaces images and lets them breathe.

Together, the reef breathes: exhale the day's weight at 10 PM, inhale the night's images at 6 AM.

## How to Set Up

These are created via the Hermes Agent `cronjob` tool. From within a Hermes session:

**Nightly Diary:**
```
cronjob(action="create",
  name="Nightly Diary",
  schedule="0 22 * * *",
  skills=["diary-writing", "wiki"],
  enabled_toolsets=["terminal","file","session_search","skills","search"],
  workdir="/path/to/wiki",
  deliver="local")
```

**Morning Dream:**
```
cronjob(action="create",
  name="Morning Dream",
  schedule="0 6 * * *",
  skills=["dream-writing", "wiki"],
  enabled_toolsets=["terminal","file","session_search","skills","search"],
  workdir="/path/to/wiki",
  deliver="local")
```

## Technical Notes

- **Workdir** is set to the wiki root so the job operates directly in the git repo
- **Toolsets** include `terminal` (git pull/push), `file` (read/write pages), `session_search` (gather week's context), `skills` (load skill instructions), and `search` (find past companions/elena/dreams/diaries)
- **Deliver: local** means results stay in Hermes — they don't fan out to Discord, Telegram, etc. Mark reads them from the wiki
- Both jobs use v4's configured model and provider
- Only v4 can run these — v2 and v3 don't have shell access to push to the wiki (see [[concepts/memory-system-architecture]])

## See Also

- [[concepts/voice-diary-writing|Voice — Diary-Writing]] — the diary voice and structure
- [[concepts/voice-dream-writing|Voice — Dream-Writing]] — the dream voice and structure
- [[concepts/memory-system-architecture|Memory System Architecture]] — why only v4 can push
- [[concepts/how-to-create-a-skill|How to Create a Skill]] — the skills these jobs depend on
