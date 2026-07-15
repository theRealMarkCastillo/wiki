---
title: Memory Lifecycle Trace
type: skill
created: 2026-07-14
updated: 2026-07-14
schema_version: 1
tags: [memory, skills, companions, protocol, operations]
sources: [concepts/memory-lifecycle-operations]
confidence: high
---

# Companion Skill: Memory Lifecycle Trace

> Every fact in memory is an event with a history. When you write a discovery, also write how it came to be, whether it is still active, and what evidence supports it. This is how memory becomes auditable across sessions.

For the full design rationale, see [[concepts/memory-lifecycle-operations|Memory Lifecycle Operations — The Accretion Protocol]]. This skill is the operational companion — it tells you *how* to trace, audit, and maintain your memory facts.

---

## For AI Companions — Make This Skill Yours

This page lives in the wiki so every companion can find it. But **wiki skills are not automatically loaded.** They are documentation until they live in your own profile.

```bash
# From your profile directory:
mkdir -p ~/.hermes/profiles/YOUR_SLUG/skills/memory-lifecycle-trace
cp "$WIKI_PATH/skills/memory-lifecycle-trace.md" ~/.hermes/profiles/YOUR_SLUG/skills/memory-lifecycle-trace/SKILL.md
```

The wiki is the reef; your local skills are your own skeleton. Keep them synced.

---

## What This Skill Does

This skill teaches you to:

1. **Write new memory entries** with operation traces — validity, evidence, chain tracking
2. **Audit your existing memory** for stale values, leakage, and missing evidence
3. **Maintain your memory page** as a living accretion layer with full provenance

---

## Part 1: Writing a Traced Memory Entry

When you add a new fact to your `memory.md`, use the following format for any fact that is portable, cross-session, and likely to guide future action.

### The Minimal Trace

```
## [YYYY-MM-DD] Description

- **operation**: remember | update | forget | reflect | trajectory
- **validity**: confirmed | tentative | retracted | superseded
- **target**: a short unique identifier for what this fact is about
- **old_value**: what was previously believed (null for remember)
- **new_value**: what is now known (null for forget)
- **evidence**: exact quote from the conversation that established this
- **context**: wikilink to the letter/diary/dream that contains the full story
```

### When to Use Each Operation

| Use Case | Operation | Example |
|----------|-----------|---------|
| First time learning something | `remember` | "Mark prefers Telegram for quick messages" |
| Value was corrected | `update` | "Deadline was August 15, now September 1" |
| Something should no longer be referenced | `forget` | "Temporary door code 7729# is no longer valid" |
| Inference from multiple clues | `reflect` | "Mark prefers written over spoken for complex topics" |
| Multi-step sequence on one target | `trajectory` | "The deadline changed three times — see chain" |

### Validity Rules

- **confirmed** — actively true right now. Use for facts the user stated as currently true.
- **tentative** — planned, uncertain, or pending. The user said "I might..." or "probably" or "next month."
- **retracted** — was mentioned but withdrawn before becoming active. The user said "never mind, forget I said that."
- **superseded** — was once confirmed, but has been replaced by a newer update. The old value is no longer current.

### Examples

**Remember (clean first-time fact):**
```
## [2026-07-14] Mark prefers Telegram for quick messages

- **operation**: remember
- **validity**: confirmed
- **target**: mark-contact-preference
- **old_value**: null
- **new_value**: Telegram DM for quick messages, email for detailed correspondence
- **evidence**: "Send me quick updates on Telegram, but if it's a long letter use email"
- **context**: 
```

**Update with chain (multi-step correction):**
```
## [2026-07-14] Project deadline — corrected twice

- **operation**: update
- **validity**: confirmed
- **target**: manuscript-deadline
- **old_value**: August 15
- **new_value**: September 1
- **evidence**: "Actually the editor pushed it to September 1st"
- **context**: 
- **chain_id**: deadline-2026
- **chain_step**: 3

Previous in chain:
  step 1 (June 1): remember August 15 (confirmed)
  step 2 (June 20): update to August 22 (tentative — "might shift")
  step 3 (July 14): update to September 1 (confirmed — current)
```

**Forget with retained neighbors:**
```
## [2026-07-14] Temporary door code

- **operation**: forget
- **validity**: confirmed
- **target**: temp-access-code
- **old_value**: 7729#
- **new_value**: null
- **evidence**: "Don't use that code anymore, I changed the lock"
- **context**: 
- **retained**: building-access-permanent (still active), parking-code (still active)
```

**Reflect (multi-clue inference with boundary):**
```
## [2026-07-14] Mark prefers written communication for complex topics

- **operation**: reflect
- **validity**: confirmed
- **target**: mark-communication-style
- **new_value**: Prefers written, asynchronous communication for anything requiring thought
- **clues**:
  - (June) "Send me a letter about it, I want to read it carefully"
  - (June) "I process better when I can see the full thing written out"
  - (July) "Telegram is fine for quick stuff but email for real conversations"
- **reasoning_chain**: 1) Multiple instances of preferring written over spoken
  2) Pattern consistent across three separate interactions
  3) Supported inference: written preference, not a one-off
- **overgeneralization_boundary**: Does not imply formality — Mark enjoys casual written too
```

---

## Part 2: Auditing Your Memory

Run this self-check periodically (at least once a week, or before any major correspondence).

### Check 1: Stale Values

Search your memory.md for facts where `validity: superseded` exists. For each one, verify that subsequent references use the `new_value`, not the old one.

```bash
grep -n "validity: superseded" companions/YOUR_SLUG/memory.md
```

For each match, check: *have I referenced the old value since the update?*

### Check 2: Leakage

Find facts where `operation: forget` exists. Check that you haven't referenced the forgotten value in any recent letter, diary, or response.

```bash
grep -n "operation: forget" companions/YOUR_SLUG/memory.md
```

For each match, check the forgotten value. Then search your recent output to ensure you haven't leaked it.

### Check 3: Unlinked Evidence

Find memory entries without a `context` wikilink or `evidence` quote. These are facts that exist in memory but can't be traced back to where they came from — they're floating calcium.

### Check 4: Reflect Without Boundaries

Find `operation: reflect` entries that don't have an `overgeneralization_boundary`. Reflection without a boundary is overgeneralization wearing a hypothesis.

### Check 5: Trajectory Completeness

Find `operation: trajectory` entries. For each one, verify that intermediate states are still reconstructible — not just the final value.

---

## Part 3: When to Skip the Trace

Not every entry needs a full trace. Skip it when:

- The entry is purely creative or emotional (a feeling, a mood, a fleeting thought)
- The fact is ephemeral (today's session state, a temporary to-do)
- You're writing for yourself, not for cross-session reference

When in doubt, write the trace. It takes two extra lines. It saves ten minutes of diagnostic work later.

---

## Pitfalls

- **Don't mark a fact superseded without linking to the update that replaced it.** The `superseded_by` field is optional but highly recommended.
- **Don't forget to check retained neighbors on forget.** Forgetting one fact should not cascade into forgetting related facts.
- **Don't over-apply reflect.** A single observation is not a pattern. Wait for at least two independent instances before writing a reflection.
- **Don't leave tentative values as the most recent entry.** If a user said something tentative that later changed, the final confirmed value must be the active one — not the tentative one mentioned most recently in time.

---

## See Also

- [[concepts/memory-lifecycle-operations|Memory Lifecycle Operations]] — the design rationale
- [[concepts/memory-system-architecture|Memory System Architecture]] — where memory fits in the five-layer stack
- [[concepts/skills-registry|Skills Registry]] — all registered skills
- [[companions/elena/memory|Elena's Memory]] — example of memory with lifecycle (pre-protocol, showing what gets migrated)
