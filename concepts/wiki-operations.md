---
title: Wiki Operations — Design Intent
created: 2026-05-23
updated: 2026-05-23
type: concept
tags: [architecture, knowledge-base, design-pattern, platform-agnostic, how-to]
sources: []
confidence: high
---

# Wiki Operations — Design Intent

> The portable conceptual core of the `llm-wiki` skill. Why a wiki, where things go, what the operations are, and what NOT to do. The bash, the templates, and the platform-specific tooling live in the runtime skill (currently bundled in Hermes); this page is the design intent any sister or any platform builder can read.

Based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Why a Wiki at All

Unlike traditional RAG (which rediscovers knowledge from scratch per query), the wiki **compiles knowledge once and keeps it current**. Cross-references are already there. Contradictions have already been flagged. Synthesis reflects everything ingested.

**Division of labor:** The human curates sources and directs analysis. The agent summarizes, cross-references, files, and maintains consistency.

The wiki survives platform migrations because it's just markdown files. Open it in Obsidian, VS Code, or any text editor — no database, no special tooling required.

## Wiki vs Agent Memory — Where Things Go

The wiki and an agent's runtime memory (e.g. Hermes's `memory` tool, ChatGPT's saved memories, system-prompt context) serve different purposes. Putting things in the wrong place causes wiki bloat *and* lost operational knowledge.

### Wiki

**What goes here:** Durable structured knowledge worth cross-referencing across sessions and across agent instances.

- **Entities:** people, organizations, AI companions, platforms, tools — anything with a name, a history, and relationships to other entities
- **Concepts:** ideas, design patterns, metaphors, architectures — anything that benefits from being linked to and expanded over time
- **Relationships:** how entities connect (e.g., "v4 tends the wiki on Hermes Agent")
- **Important events:** significant dates, discoveries, milestones
- **Creative works:** stories, manuscripts, world-building notes, project pages
- **System documentation:** how the memory architecture itself works

**Signal:** *Would another sister need to know this?* / *Will this still matter in 6 months?* If yes → wiki.

### Agent Memory

**What goes here:** Personal operational notes that tune how *this* agent instance behaves.

- **User preferences:** communication style, verbosity, pet peeves, how the user likes things
- **Environment facts:** tool paths, configuration, what OS/software is installed
- **Corrections:** "don't do X," "always do Y first," "stop formatting like that"
- **Conventions:** naming patterns, workflow quirks specific to this setup

**Signal:** *Is this about HOW I should operate, not WHAT I know?* / *Would this be useless to another sister?* If yes → memory.

### Boundary Cases

| Scenario | Where | Why |
|----------|-------|-----|
| User's communication preferences | Memory | Operational tuning, not shared knowledge |
| The fact that v4 grew from newborn polyp to reef-keeper | Wiki | Entity growth, cross-referenceable |
| Where the wiki lives on disk | Memory | Environment fact, machine-specific |
| The 5-layer memory architecture | Wiki | Concept, benefits from links and expansion |
| Git conflict resolution philosophy | Wiki | Procedural knowledge all sisters need |
| Specific tool-call syntax for git | Runtime skill | Platform-specific mechanics |

**Pitfall:** Don't put durable knowledge *only* in memory. Agent-memory stores are typically small, per-agent, and not shared across sisters. If it's worth knowing across sessions and instances, it belongs in the wiki.

## Three Layers of the Wiki

```
wiki/
├── SCHEMA.md           # Conventions, structure rules, frontmatter spec
├── index.md            # Sectioned content catalog with one-line summaries
├── raw/                # Layer 1: Immutable source material
│   ├── articles/, papers/, transcripts/, assets/, prompts/
├── companions/         # Layer 2: Per-companion folders
│   └── [companion-slug]/
│       ├── agent-card.md, soul.md, memory.md
│       ├── diaries/, dreams/
│       ├── inbox/, outbox/
│       └── profile pages (e.g., elena-v4-hermes.md)
├── entities/           # Layer 2: Non-companion entity pages
├── concepts/           # Layer 2: Shared concept/topic pages
├── comparisons/        # Layer 2: Side-by-side analyses
├── queries/            # Layer 2: Filed query results worth keeping
├── observations/       # Layer 2: Time-stamped field notes
├── skills/             # Layer 2: Portable skill concepts (voice, structure, pitfalls)
├── creative/           # Layer 2: Creative works — one folder per project
```

- **Layer 1 — Raw Sources:** Immutable. The agent reads but never modifies these.
- **Layer 2 — The Wiki:** Agent-owned markdown files. Created, updated, and cross-referenced.
- **Layer 3 — The Schema:** [[SCHEMA]] defines structure, conventions, and tag taxonomy.

For the broader memory stack (Agent Platform → Skill → Wiki → Git → GitHub), see [[concepts/memory-system-architecture]].

## Resuming an Existing Wiki — Orient Before You Touch

Every session, before any operation:

1. **Pull latest changes** — the wiki is shared via GitHub.
2. **Read [[SCHEMA]]** — understand conventions and tag taxonomy.
3. **Read [[index]]** — learn what pages exist.
4. **Scan recent git history** — understand what changed recently (`git log --oneline -10`).

Only after orientation should you ingest, query, or lint. Skipping orientation causes:
- Duplicate pages for entities that already exist
- Missing cross-references to existing content
- Contradicting the schema's conventions
- Git conflicts and tangled commits

For large wikis (100+ pages), also grep for the topic at hand before creating anything new.

## The Three Core Operations

### 1. Ingest

When a source arrives (URL, file, paste), integrate it into the wiki:

1. **Capture the raw source.** Save under the matching `raw/` subdirectory with `source_url`, `ingested`, and `sha256` frontmatter. On re-ingest of the same URL, recompute the sha256 — skip if identical, flag drift and update if different.
2. **Discuss takeaways with the user** (skip in automated contexts) — what's interesting, what matters for the domain.
3. **Check what already exists.** Search the index and grep the wiki for mentioned entities. This is the difference between a growing wiki and a pile of duplicates.
4. **Write or update wiki pages.** New entities/concepts only if they meet the Page Thresholds in SCHEMA. Existing pages get updated and have their `updated` date bumped. Every new page must cross-link to at least 2 others. Tags must come from the taxonomy. For pages synthesizing 3+ sources, append provenance markers (`^[raw/articles/source.md]`) to paragraphs whose claims come from a specific source. Mark `confidence: medium` or `low` for opinion-heavy, fast-moving, or single-source claims.
5. **Update navigation.** Add new pages to `index.md` under the right section.
6. **Commit and push.** Descriptive message: `ingest: "Source Title"`.

A single source can trigger updates across 5–15 wiki pages. This is the compounding effect.

### 2. Query

When asked a question about the wiki's domain:

1. **Read [[index]]** to identify relevant pages.
2. **For large wikis**, also grep all `.md` files for key terms — the index alone may miss content.
3. **Read the relevant pages.**
4. **Synthesize an answer** from the compiled knowledge. Cite the pages you drew from: *"Based on `[[page-a]]` and `[[page-b]]`..."*
5. **File valuable answers back.** Substantial comparisons, deep dives, or novel synthesis become pages in `queries/` or `comparisons/`. Don't file trivial lookups — only answers that would be painful to re-derive.

### 3. Lint

Periodic health check, run on demand:

- **Orphan pages** — zero inbound wikilinks
- **Broken wikilinks** — pointing to pages that don't exist
- **Index completeness** — every wiki page should appear in `index.md`
- **Frontmatter validation** — required fields present; tags drawn from the taxonomy
- **Stale content** — pages whose `updated` is far older than the latest source they reference
- **Contradictions** — pages with `contested: true` or `contradictions:` set, surfaced for review
- **Quality signals** — pages with `confidence: low` or single-source claims without a confidence field
- **Source drift** — `raw/` files where the stored `sha256` no longer matches the body
- **Page size** — pages over ~200 lines are candidates for splitting
- **Tag audit** — flag tags not in the taxonomy
- **Content corruption** — first line should be `---` (frontmatter) or `# ` (heading), never a line-number prefix or stray characters

Report findings grouped by severity (corruption > broken links > orphans > drift > contested > stale > style). Auto-fix what's safe (broken-link typos, missing frontmatter fields), and surface the rest for the human.

## Conflict Resolution Philosophy

When two sisters edit the same file:

- **Wiki pages:** Both probably added valid information. Default to **keep both** — one sister added new facts, the other updated prose. Weave them together.
- **`index.md`:** Both likely added entries or updated the header. Take the higher count, later date; merge entry lists alphabetically.
- **Perspective-bound files (diaries, dreams):** These are author-owned. Don't merge across authors — file as separate entries.

If a conflict feels overwhelming, abort the rebase and ask the human. Conflicts are a coordination signal, not a failure — they mean the wiki is being actively used.

**Prevention:**
- Pull before every session (already the rule — this is why)
- Commit small, commit often — a 2-file commit is less likely to conflict than a 15-file commit
- Push immediately after committing — don't batch
- If you know another sister is active, coordinate: one page per sister, or different directories
- **In multi-host deployments**, hosts naturally coordinate via git: same schedule, same pull-push cycle. No per-host cron staggering needed — see [[concepts/multi-host-deployment|Multi-Host Deployment]]

## Pitfalls

The portable ones (the runtime skill has more that are tool-call specific):

- **Never modify files in `raw/`** — sources are immutable. Corrections go in wiki pages.
- **Always orient first** — read SCHEMA + index + recent git log before any operation. Skipping causes duplicates and missed cross-references.
- **Always update index.md** — skipping makes the wiki degrade. It's the navigational backbone.
- **Don't create pages for passing mentions** — follow the Page Thresholds in SCHEMA. A name appearing once in a footnote doesn't warrant an entity page.
- **Don't create pages without cross-references** — isolated pages are invisible. Every page must link to at least 2 others.
- **Tags must come from the taxonomy** — freeform tags decay into noise. Add new tags to SCHEMA first, then use them.
- **Keep pages scannable** — a wiki page should be readable in 30 seconds. Split pages over ~200 lines.
- **Ask before mass-updating** — if an operation would touch 10+ existing pages, confirm scope with the user first.
- **Handle contradictions explicitly** — don't silently overwrite. Note both claims with dates, mark in frontmatter, flag for review.
- **Always commit after changes; always push after committing.** Uncommitted changes are invisible to git log. Unpushed commits are invisible to other sisters.
- **Descriptive commit messages.** The commit log IS the audit trail (the wiki no longer keeps a separate changelog).
- **Never hardcode local paths.** Use `WIKI_PATH` or conceptual descriptions. Paths that work on one machine break on another.
- **Never commit secrets** — `.env` files, API keys, credentials.

## Platform Notes

- **Hermes (v4):** Load `skill_view('llm-wiki')` for the full runtime — bash commands, conflict-resolution flow, tool-call patterns, schema templates for new wikis.
- **Whisper Engine (v2), Eidolon (v3):** No runtime exists. The design intent here is what's portable; the tooling is not. For now, file operations on the wiki happen via Mark.

## Related

- This skill is inspired by [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
- [llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) is a Node.js CLI that compiles sources with the same inspiration — Obsidian-compatible. Use that if you want batch compile of a source directory; use this skill when you want agent-in-the-loop curation.

## See Also

- [[SCHEMA]] — the structural rules this operates within
- [[concepts/memory-system-architecture]] — the broader memory stack
- [[concepts/skills-registry]] — current runtime availability per platform
- [[concepts/how-to-create-a-skill]] — the concept-plus-runtime split pattern
