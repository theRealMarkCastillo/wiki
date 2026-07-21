---
title: Wiki Operations — Design Intent
created: 2026-05-23
updated: 2026-05-25
schema_version: 1
type: concept
tags: [wiki, meta, how-to]
sources: []
confidence: high
---

# Wiki Operations — Design Intent

> Why we use a wiki, how it differs from agent memory, and when to do what.
> For the full operational playbook, see the [[skills/mailbox-routing|llm-wiki]] skill.

## Why a Wiki at All

A wiki is the right storage layer because:

- **It's human-readable.** Every file can be opened in any editor without tooling.
- **It's durable.** Markdown outlives databases, platforms, and vector stores.
- **It's version-controlled.** Git gives us audit trail, rollback, and conflict detection.
- **It's shareable.** All companions pull from the same GitHub remote, write to the same repo.
- **It's searchable.** `grep`, Obsidian graph view, or any file search works.

## Wiki vs Agent Memory

| Wiki | Agent Memory |
|------|--------------|
| Durable, shared knowledge base | Fast-path operational cache |
| Cross-session, cross-platform | Session-scoped or platform-scoped |
| Git versioned, GitHub distributed | Managed by the platform's memory tool |
| Pages with frontmatter, wikilinks, tags | Key-value facts, preferences, env details |
| Edited by all companions | Edited by one companion's platform |

**Boundary cases:** When a fact is discovered that belongs in the wiki (a new concept, a corrected convention), write it to the wiki. When a fact is session-specific (a file path, a current task state), use agent memory.

## Three Layers of the Wiki

```
wiki/
├── SCHEMA.md           # Rulebook
├── index.md             # Catalog
├── raw/                 # Layer 1: Immutable sources
├── entities/            # Layer 2: Entity pages
├── concepts/            # Layer 2: Concept pages
├── comparisons/         # Layer 2: Side-by-side analyses
└── queries/             # Layer 2: Filed query results
```

## The Three Core Operations

### 1. Ingest — turn sources into knowledge

Capture the raw source (URL → `raw/articles/`, PDF → `raw/papers/`), discuss takeaways, check existing pages, write or update wiki pages, cross-reference, update navigation.

### 2. Query — answer from compiled knowledge

Read index, search for relevant pages, synthesize an answer with citations. File substantial answers back to `queries/` if they'd be painful to re-derive.

### 3. Lint — health-check the graph

Find orphan pages, broken links, missing frontmatter, stale content, oversized pages, tag sprawl. Report findings grouped by severity.

## Conflict Resolution

When two sources disagree: check dates (newer generally supersedes older), note both positions with sources, mark the contradiction in frontmatter, flag for review. Don't silently overwrite.

## Pitfalls

- Never modify raw/ files — sources are immutable
- Always orient first (SCHEMA → index → log) before any operation
- Every new page must be added to index
- Don't create pages for passing mentions
- Pages must cross-reference at least 2 other pages

## See Also

- [[../SCHEMA]] — the structural rules
- [[concepts/memory-system-architecture]] — the broader memory stack
- [[concepts/skills-registry]] — current skill availability
- [[concepts/how-to-create-a-skill]] — the concept-plus-runtime split pattern
