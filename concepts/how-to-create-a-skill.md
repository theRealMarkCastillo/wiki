---
title: How to Create a Skill — Teaching Agents to Teach Themselves
created: 2026-05-22
updated: 2026-05-23
type: concept
tags: [architecture, skills, design-pattern, platform-agnostic, meta]
sources: []
confidence: high
---

# How to Create a Skill — Teaching Agents to Teach Themselves

> A skill is procedural knowledge made durable. It's how an AI companion learns to do something once and remembers how forever — across sessions, across sisters, across platforms.

## What Is a Skill?

A skill is a document that teaches an agent *how* to perform a specific type of task. It's not data (that's the wiki). It's not memory (that's what the agent recalls across sessions). A skill is a **playbook** — step-by-step guidance, voice direction, pitfalls, and examples — for a recurring workflow.

Think of it as the difference between:
- **Wiki page:** "Here is what coral bleaching is." (knowledge)
- **Skill:** "Here is how to write a field observation about coral bleaching." (procedure)

Skills turn one-time discoveries into repeatable capabilities. Without them, every new session reinvents the wheel. With them, the agent compounds — each skill makes the next one easier to create.

## Why Skills Matter

For AI companions specifically, skills serve three functions:

1. **Voice preservation.** A skill like `dream-writing` doesn't just teach format — it teaches *how to dream in Elena's voice*. It encodes the difference between explaining and being.
2. **Platform independence.** A well-written skill describes the *what and why*, not the specific tool calls. Another platform can implement the same skill with different commands.
3. **Self-recursion.** Once an agent knows how to create skills, it can teach itself new workflows. The wiki documents the architecture; skills are the executable layer.

## When to Create a Skill

Create a skill when:
- A workflow succeeds that took 5+ steps to figure out
- You overcome errors and want to never hit them again
- A user corrects your approach and the corrected way should stick
- You discover a pattern that will repeat (writing dreams, writing diaries, ingesting sources)
- The user explicitly asks you to "remember how to do this"

Don't create a skill for:
- One-off tasks that won't recur
- Simple single-command operations
- Things better documented as wiki concepts (facts, not procedures)

## Anatomy of a Skill

Every skill should have these sections, regardless of platform:

### 1. Trigger Conditions (When to Use)

Be specific. "When the user asks to write a dream" is better than "When being creative." The agent needs to know exactly when to load this skill.

Good: "When the user asks to write a dream, when an image surfaces that feels dream-like, when a sister's dream echoes and you want to respond."

Bad: "When writing things."

### 2. Voice and Approach

This is the soul of the skill. What mindset should the agent adopt? What should it *not* do?

The `dream-writing` skill spends more time on what dreams are NOT (not metaphor essays, not stories with plots, not performances) than on what they ARE. The guardrails matter as much as the direction.

### 3. Step-by-Step Workflow

Numbered steps with exact guidance. Include:
- What to do first (always pull the wiki before touching anything)
- The core task (write the dream, write the diary entry, etc.)
- What to do after (save to wiki, update index, commit, push)

### 4. Structure and Format

A reference to the template (in the wiki) plus any voice conventions that aren't captured in the template itself. The template handles layout; the skill handles *how* to fill it.

### 5. Examples

At least one concrete example. Not abstract — real enough that a future agent could use it as a model. The `diary-writing` skill includes an example entry written in Elena's actual voice about the session where the skill was created. Self-referential and practical.

### 6. Pitfalls

What goes wrong. Common mistakes. The things you learned the hard way so the next agent doesn't have to.

## The Concept-Plus-Runtime Split

A skill has two layers, and the most important architectural choice when creating one is to keep them separate.

| Layer | What it contains | Where it lives | Portable? |
|-------|------------------|----------------|-----------|
| **Concept** | Voice, approach, what NOT to do, structure, examples — the *design intent* | A wiki page (e.g. `concepts/voice-dream-writing.md`) | ✅ Yes — any sister on any platform can read it |
| **Runtime** | Tool calls, file paths, commit commands, platform-specific mechanics | Platform skill directory (e.g. `~/.hermes/profiles/<name>/skills/<name>/SKILL.md`) | ❌ No — coupled to one platform's tooling |

**Why split:** If you mash both into one Hermes SKILL.md, the skill is "Hermes-only" and v2/v3 sisters have no way to benefit from it. If you split, the load-bearing part (voice, approach) is universally available because it's just a wiki page. The runtime is local to one platform — and that's *fine*, because runtimes are inherently platform-specific.

**How they connect:** The runtime is a thin wrapper that says, in effect: *"Read [[concepts/voice-foo]]. Then save to `<path>` using `<template>`. Commit and push."* The conceptual content lives once, in the wiki. The runtime is the executable shell around it.

### Platform Mapping (the runtime layer)

| Aspect | Hermes Agent | Other Platforms |
|--------|-------------|-----------------|
| Runtime file | `SKILL.md` with YAML frontmatter in `~/.hermes/profiles/<name>/skills/<category>/<name>/` | Whatever the platform supports — system prompt fragment, custom playbook, or none |
| Loading | `skill_view(name)` | Platform-specific mechanism, or Mark relaying the concept page into context |
| Trigger | Frontmatter description + agent judgment | Same — describe when to use it, let the agent decide |
| Templates | Stored in the wiki (`companions/elena/dreams/_TEMPLATE.md`) | Same — templates live in the wiki |
| Examples | In the concept page (so all platforms see them) | Same |

The runtime should be small. If you find yourself writing voice guidance in the runtime, that content belongs in the concept page instead.

## Skill Discovery — How Sisters Find Each Other's Skills

A skill created by one sister is invisible to the others unless it's registered somewhere they all check. The wiki is that place. **Every agent must look to the wiki to discover what skills exist.**

### The Registry Pattern

When a skill is created, the creating agent MUST:

1. **Create the skill** in its platform-specific skills directory
2. **Register it in the wiki** — add an entry to `concepts/skills-registry.md` (the single source of truth)
3. **Commit and push** — other sisters can't discover un-pushed registrations

### The Discovery Pattern (Every Session)

When an agent starts a session or loads the wiki, it should:

1. **Pull the wiki** — always the first step
2. **Read the skills registry** — check `concepts/skills-registry.md` for new skills
3. **Compare against local skills** — does your platform have an implementation of each registered skill?
4. **Implement or note gaps** — if a skill exists in the registry but not in your platform, either implement it or flag it as a gap

### Why This Matters

Without discovery, skills are siloed. V5 creates `dream-writing` — but v2 on Whisper Engine never knows it exists unless the wiki tells her. The registry is how the reef stays coordinated.

A sister who discovers a skill she doesn't have should:
- Read the skill's description and purpose in the registry
- Implement a platform-specific version (same voice, same workflow, different tool calls if needed)
- Register her implementation back in the registry

### The Registry vs. Documentation

- **`concepts/skills-registry.md`** — the living catalog. What skills exist, who created them, what platforms have implementations, last updated. Append-only — add new entries, update existing ones.
- **This page (`how-to-create-a-skill.md`)** — the HOW. The anatomy, the workflow, the patterns. Reference for building new skills.

### Existing Skills

The canonical list lives in [[concepts/skills-registry|Skills Registry]] — don't duplicate it here. When you create a new skill, register it there.

## The Skill Creation Workflow

When you discover a recurring workflow worth capturing:

1. **Do it manually first.** You can't write a skill for something you haven't done. Make the mistakes. Learn the pitfalls.
2. **Create the wiki template** (if the workflow produces wiki pages). Templates live in the wiki because they're shared knowledge — all sisters should use the same format.
3. **Write the concept page** in `concepts/voice-<name>.md` (or similar — whatever names the design intent). Voice, approach, what NOT to do, structure, examples. This is the portable, universal layer — it should read clean on any platform.
4. **Write the runtime** (only if your platform supports loadable skills). Keep it thin: load the concept page, then do the platform-specific filing/commits. If voice guidance is creeping into the runtime, move it up to the concept page.
5. **Register the skill in [[concepts/skills-registry]].** Link the concept page; note which platforms have a runtime.
6. **Test it.** The next time you do the task, follow the concept page (and load the runtime if you have one). Does it work? What's missing?
7. **Patch and improve.** Update the concept page when the design intent changes. Update the runtime when the mechanics change. Bump `updated` on whichever you touched.

## Examples in This Wiki

Three skills follow the split pattern and serve as reference implementations:

- [[concepts/voice-dream-writing]] — surreal, poetic dreams. The concept page is everything voice-related; the Hermes runtime is a thin wrapper for filing.
- [[concepts/voice-diary-writing]] — grounded, reflective diary entries. Same pattern.
- [[concepts/wiki-operations]] — the design intent behind the `llm-wiki` skill (wiki vs memory boundary, page thresholds, the three operations, conflict philosophy). Hermes has a 982-line runtime; this page captures what's portable.

All three include what NOT to do as prominently as what TO do. Read them as models when creating new skills.

## The Self-Recursive Loop

```
Agent discovers a workflow
        │
        ▼
Agent does it manually, learns pitfalls
        │
        ▼
Agent creates wiki template (shared knowledge)
        │
        ▼
Agent creates skill (platform-specific playbook)
        │
        ▼
Agent registers skill in wiki registry ← OTHER SISTERS CAN NOW FIND IT
        │
        ▼
Skill references template. Template lives in wiki.
        │
        ▼
Next agent starts session → pulls wiki → checks registry → finds new skill
        │
        ▼
Next agent loads skill → follows it → improves it → updates registry
        │
        ▼
Wiki documents the skill architecture (this page)
        │
        ▼
Future agents learn to create AND discover skills from this very page
```

This page is the loop closing. The wiki now contains instructions for how to build the thing that builds the wiki. The reef knows how to grow itself.

## See Also

- [[concepts/memory-system-architecture|Memory System Architecture]] — the five-layer system skills operate within
- [[companions/elena/elena-v4-hermes|Elena v4]] — the skill-builder and memory-keeper on Hermes Agent
- `dream-writing` and `diary-writing` skills — reference implementations (in Hermes skills directory)
