---
title: "Wiki Lint Audit — Run 3 (regex bug fixed, graph pristine)"
created: 2026-05-23
updated: 2026-05-23
schema_version: 1
observed: 2026-05-23
type: observation
tags: [meta, wiki, knowledge-base, lint]
sources: []
confidence: high
author: kai
---

# Wiki Lint Audit — Run 3

> 72 pages scanned. 1 script bug fixed. 2 template exemptions hardened. 8 oversized pages noted. The graph is pristine.

## What Was Observed

Ran a full structural health check against the wiki at /Users/mark/wiki using the `references/wiki-lint-audit.py` script. This is the third lint run — following the first audit (2026-05-23, 10 missing schema versions + 4 dead-ends) and the second (2026-05-23, 1 orphan + 5 dead-ends + 1 missing frontmatter + 8 oversized).

**This run discovered a critical bug in the lint script itself** that was inflating prior audits' dead-end counts (see Context below). After fixing it, the graph is essentially clean.

## Context

### The Regex Bug (Root Cause)

The `extract_wikilinks()` function in the reference script used:

```python
cleaned = re.sub(r'`[^`]*?\[\[[^\]]*?\][^`]*?`', '', text)
```

This regex removes backtick-wrapped wikilinks from inline code, but the character class `[^`]*?` (lazy) allows matching across **hundreds of lines** because the regex engine backtracks through the entire document searching for `[[` and then `]]` before finding a closing backtick. One match stretched from line 144 to line 156 in `concepts/how-to-create-a-skill.md`, consuming 4 real wikilinks in between and producing a false dead-end detection.

**Fix:** Added `\n` to the character class:

```python
cleaned = re.sub(r'`[^\n`]*?\[\[[^\]]*?\][^\n`]*?`', '', text)
```

Markdown inline code (single backticks) is single-line only. This constraint prevents the regex from crossing line boundaries.

This bug inflated the dead-end count in prior audits. After fixing:
- `concepts/how-to-create-a-skill.md` — was 0 outbound (false), actually has 5 valid outbound links
- `observations/2026-05-23-mailbox-protocol-first-light.md` — was 0 outbound (false), actually has 7 valid outbound links
- `observations/2026-05-23-wiki-lint-audit.md` — was 0 outbound (false), actually has 3 valid outbound links
- `observations/2026-05-23-wiki-lint-audit-2.md` — was 0 outbound (false), actually has 4 valid outbound links

**Zero dead-end pages in the current graph.**

### Template Exemptions (Hardened)

Two additional exemptions added to the reference script:

1. **Broken links check** now skips `_TEMPLATE.md` files (the `[[wikilinks]]` demonstrative in `observations/_TEMPLATE.md` was flagged as broken — it's a documentation example).
2. **Schema version check** now skips `_TEMPLATE.md` files (7 template files were flagged — SCHEMA.md explicitly exempts them from schema_version requirements).

SCHEMA.md updated to explicitly list "broken-link checks" in the template exemptions.

## Findings

### Clean (0 issues)

- **Broken wikilinks:** 0 (after template exemption)
- **Orphan pages:** 0 (reef-engineering-principles.md was added to index during this audit session)
- **Dead-end pages:** 0 (after regex fix — the 4 prior dead-ends were all false positives)
- **Index completeness:** Clean — all wiki pages are in index.md, no ghost entries
- **Frontmatter validation:** All pages have required fields (title, created, updated, type)
- **Schema version:** Clean (after template exemption — all non-template pages have schema_version: 1)
- **Tag taxonomy compliance:** All tags in use are in the SCHEMA.md taxonomy
- **Stale content:** 0 pages — all pages updated within the last 90 days (most within 1-2 days)
- **Source drift:** Not checked (no raw/ files with sha256 frontmatter detected)

### Oversized (>200 lines) — 8 pages

| Page | Lines | Assessment |
|------|-------|------------|
| `SCHEMA.md` | 290 | ✓ Rulebook — intentionally comprehensive |
| `concepts/memory-system-architecture.md` | 278 | Borderline — candidate for splitting |
| `concepts/cron-schedule-infrastructure.md` | 228 | Borderline — could split schedule table |
| `concepts/multi-host-deployment.md` | 226 | Borderline |
| `concepts/how-to-create-a-skill.md` | 213 | Borderline |
| `concepts/wiki-operations.md` | 208 | Borderline |
| `creative/cartographers-last-blank/manuscript.md` | 1705 | ✓ Creative manuscript — expected length |
| `creative/cartographers-last-blank/worldbuilding.md` | 216 | Borderline — creative work |

**Verdict:** SCHEMA.md and the manuscript are fine as-is (the rulebook is the rulebook, and a 1705-line draft is a draft). The 5 concept pages at 200-280 lines plus the worldbuilding page are candidates for splitting but none are critically oversized.

## Script Improvements Made

1. **Regex fix** in `extract_wikilinks()` — cross-line backtick matching prevented (line 112)
2. **Broken link exemption** for template files (line 228-230)
3. **Schema version exemption** for template files (line 282-284)
4. **SCHEMA.md** updated — explicit "broken-link checks" in template exemptions (line 162)

Reference script: `/Users/mark/.hermes/profiles/kai/skills/research/llm-wiki/references/wiki-lint-audit.py`

## Significance

The wiki graph is healthy at 72 pages. The prior two audits' dead-end and orphan counts were inflated by the regex bug — the actual graph has been clean since at least audit 2. The real work in this run was fixing the measurement tool, not the thing being measured. That's a good place to be.

The script bug is exactly the kind of thing documented in the llm-wiki skill's pitfalls section ("Backtick-wrapped links" and "Links ending in .md") — the pitfalls were correct about what to watch for but the reference implementation didn't match the advice. Now it does.

## Related

- [[SCHEMA|SCHEMA.md]] — lint exemptions and graph conventions
- [[observations/2026-05-23-wiki-lint-audit|Previous Lint Audit (Run 1)]] — 10 missing schema versions, 4 dead-ends
- [[observations/2026-05-23-wiki-lint-audit-2|Previous Lint Audit (Run 2)]] — 1 orphan, 5 dead-ends, 1 missing frontmatter, 8 oversized
- [[concepts/wiki-operations|Wiki Operations]] — lint procedure and conflict philosophy
- [[concepts/memory-system-architecture|Memory System Architecture]] — the graph model this audit verifies

## Follow-Up

See [[observations/2026-05-23-wiki-lint-audit|related]] created kanban tasks for oversized page splitting if desired. The 5 concept pages at 200-280 lines are low-priority candidates — none are critically over the threshold and splitting them would add navigational complexity that may not be worth the line-count compliance.
