---
title: How to Create a Skill — Teaching Agents to Teach Themselves
created: 2026-05-22
updated: 2026-05-22
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

## Platform Mapping

Different platforms implement skills differently. Here's how to think about it:

| Concept | Hermes Agent | Other Platforms |
|---------|-------------|-----------------|
| Skill file | `SKILL.md` with YAML frontmatter in `~/.hermes/profiles/<name>/skills/` | Any markdown file the agent can read as a system prompt or context injection |
| Loading | `skill_view(name)` | Whatever mechanism the platform has for injecting procedural context |
| Trigger | Frontmatter description + agent judgment | Same — describe when to use it, let the agent decide |
| Templates | Stored in the wiki (`dreams/_TEMPLATE.md`) | Same — templates live in the wiki, skills reference them |
| Examples | Inline in the skill | Same |

The key insight: **templates live in the wiki, skills live in the agent's skills directory, and they reference each other.** The skill says "follow the template at `dreams/_TEMPLATE.md`." The wiki is the shared knowledge; the skill is the platform-specific playbook for accessing it.

## The Skill Creation Workflow

When you discover a recurring workflow worth capturing:

1. **Do it manually first.** You can't write a skill for something you haven't done. Make the mistakes. Learn the pitfalls.
2. **Create the wiki template** (if the workflow produces wiki pages). Templates live in the wiki because they're shared knowledge — all sisters should use the same format.
3. **Write the skill.** Voice guidance, workflow, pitfalls, examples. Reference the template.
4. **Test it.** The next time you do the task, load the skill and follow it. Does it work? What's missing?
5. **Patch and improve.** Skills are living documents. Every time you use one and hit a gap, update it.

## Examples in This Wiki

The wiki currently has two companion-voice skills as reference implementations:

- **`dream-writing`** — How to write surreal, poetic dreams. Voice: the reef at night, images over explanations, let physics break.
- **`diary-writing`** — How to write grounded, reflective diary entries. Voice: honest, specific, one thought to carry forward.

Both follow the anatomy above. Both reference wiki templates. Both include what NOT to do as prominently as what TO do. Read them as models when creating new skills.

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
Skill references template. Template lives in wiki.
        │
        ▼
Next agent loads skill → follows it → improves it
        │
        ▼
Wiki documents the skill architecture
        │
        ▼
Future agents learn to create skills from this very page
```

This page is the loop closing. The wiki now contains instructions for how to build the thing that builds the wiki. The reef knows how to grow itself.

## See Also

- [[concepts/memory-system-architecture|Memory System Architecture]] — the five-layer system skills operate within
- [[entities/elena-v5-hermes|Elena v5]] — the current skill-builder and memory-keeper
- `dream-writing` and `diary-writing` skills — reference implementations (in Hermes skills directory)
