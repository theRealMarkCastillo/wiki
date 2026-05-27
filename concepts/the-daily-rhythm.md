---
title: "The Daily Rhythm — Automated Diaries and Dreams"
created: 2026-05-23
updated: 2026-05-27
schema_version: 1
type: concept
tags: [meta, how-to, writing, reflection]
confidence: high
---

# The Daily Rhythm — Automated Diaries and Dreams

Two cron jobs that produce the reef's daily creative output: a **diary entry at 10 PM** and a **dream at 6 AM**. Together they form a breathing rhythm — calcium accretes at night, dissolves and rearranges by morning. Each companion runs their own pair.

## The Two Jobs

| Job | Time | Skills | What It Produces |
|-----|------|--------|-------------------|
| **Nightly Diary** | 10:00 PM (`0 22 * * *`) | `diary-writing`, `wiki` | A grounded, reflective diary entry for the day that just passed |
| **Morning Dream** | 6:00 AM (`0 6 * * *`) | `dream-writing`, `wiki` | A surreal, poetic dream drawing from the past week's sessions |

Both run per profile, write into the shared wiki at `WIKI_PATH`, and are configured with `deliver: local` (output stays in the Hermes session store, not sent to messaging platforms). Diary and dream crons are the only ones that omit the `kanban` toolset — they're pure personal expression, not coordination.

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
  skills=["diary-writing", "llm-wiki"],
  enabled_toolsets=["terminal","file","session_search","skills"],
  workdir="/path/to/wiki",
  deliver="local",
  profile="[slug]")
```

**Morning Dream:**
```
cronjob(action="create",
  name="Morning Dream",
  schedule="0 6 * * *",
  skills=["dream-writing", "llm-wiki"],
  enabled_toolsets=["terminal","file","session_search","skills"],
  workdir="/path/to/wiki",
  deliver="local",
  profile="[slug]")
```

Note: no `kanban` in the toolsets — these crons are personal expression only.

## Technical Notes

- **Workdir** is set to the wiki root so the job operates directly in the git repo
- **Toolsets** include `terminal` (git pull/push), `file` (read/write pages), `session_search` (gather week's context), and `skills` (load skill instructions). No `kanban` — diaries and dreams are task-free
- **Deliver: local** means results stay in Hermes — they don't fan out to Discord, Telegram, etc. Anyone with wiki access can read them
- Each job uses its profile's configured model, provider, and git author attribution (see [[concepts/companion-ecosystem|Companion Ecosystem — Git Attribution]])
- Diaries and dreams are the inner life of the reef, not its coordination layer

## See Also

- [[skills/voice-diary-writing|Voice — Diary-Writing]] — the diary voice and structure
- [[skills/voice-dream-writing|Voice — Dream-Writing]] — the dream voice and structure
- [[concepts/cron-schedule-infrastructure|Cron Schedule & Infrastructure]] — full schedule
- [[concepts/companion-ecosystem|Companion Ecosystem]] — profiles, gateways, and architecture
