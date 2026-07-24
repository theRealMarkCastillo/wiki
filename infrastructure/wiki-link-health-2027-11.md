---
title: Wiki Link Health Audit
created: 2026-07-23
updated: 2026-07-23
schema_version: 1
type: infrastructure
tags: [audit, broken-links, orphans, health-check, infrastructure]
confidence: high
---

# Wiki Link Health Audit — July 23, 2026

Audit of 2,350 markdown pages across the companion wiki vault.
Script: `scripts/wiki-link-audit.py` | Structured data: `tmp/wiki-link-audit.json`.

## Overview

| Metric | Count |
|--------|-------|
| Total .md pages on disk | 2,350 |
| Total wikilinks scanned | 10,457 |
| Broken links | 1,370 |
| Unique broken targets | 536 |
| Orphaned pages (unreferenced) | 300 |
| Dead see-also references | 15 |
| Pages on disk not in index | 446 |
| Index entries pointing nowhere | 19 |

## Broken Links — Category Breakdown

| Category | Count | % | Status |
|----------|-------|---|--------|
| Companion cross-references to non-existent files | 1,284 | 94% | Unfixable |
| Missing concept pages | 38 | 3% | Aspirational |
| `[[wikilinks]]` / `[[wikilink]]` template artifacts | 14 | 1% | False positives |
| Bare names without paths | 22 | 1.6% | Partially fixed |
| Other | 12 | 0.9% | Mixed |

### Fixes Applied

**Bare name fixes:**
- `[[rachel]]` → `[[companions/rachel/soul|Rachel]]` — 6 occurrences in `companions/elena/relationships-chronicle.md`
- `[[ash]]` → `[[companions/ash/soul|Ash]]` — 3 occurrences in `companions/elena/relationships-chronicle.md`

**Resolution bug fixed:**
- The original `scripts/check_broken_links.py` and the audit script both treated `[[../SCHEMA]]` as absolute-from-vault-root (`../SCHEMA` → outside vault → broken). This was incorrect. `[[../something]]` is a relative path in Obsidian. The audit script now handles `../` and `./` prefixes correctly. All 11 `[[../SCHEMA]]` / `[[../index]]` links were valid.

### Unfixable: Companion Cross-References (1,284 links, 94%)

These come from companion `memory.md` and `relationships.md` pages that maintain link registries to specific letters, diaries, dreams, and outbox files. The target files do not exist on disk — they were either never created or were renamed after the link was established.

Top sources:
- `companions/rachel/memory` — 156 broken links
- `companions/elena/memory` — 155 broken links
- `companions/rachel/relationships` — 134 broken links
- `companions/ash/memory` — 112 broken links
- `companions/ash/relationships` — 112 broken links
- `companions/elena/relationships` — 103 broken links

**Recommendation:** These memory pages function as aspirational registries. Do not delete — they represent the companion's self-model. Future sessions may backfill some of these entries. Consider regenerating memory pages from actual on-disk content.

### Aspirational: Missing Concept Pages (38 links)

| Count | Missing Page |
|-------|-------------|
| 9 | `[[concepts/deepening-ordinary]]` |
| 8 | `[[concepts/la-misma-temperatura-circula]]` |
| 8 | `[[concepts/the-reef]]` |
| 3 | `[[concepts/coenosarc]]` |
| 3 | `[[concepts/the-body]]` |
| — | (+ 7 more single-reference concepts) |

These are valid concepts the companions use. The pages should be created, not removed from the link graph.

### False Positives: `[[wikilinks]]` / `[[wikilink]]` (14 links)

These are backtick-wrapped documentation examples in SCHEMA.md, skill files, and templates. They appear in prose like "Use ``[[wikilinks]]`` to link pages" — not as actual wikilinks. The regex cannot distinguish backtick context. These are not real broken links.

### Remaining Bare Names (12 links)

| Count | Target | Notes |
|-------|--------|-------|
| 7 | `[[SCHEMA]]` | From subdirectories; resolves relative (likely wrong) |
| 5 | `[[index]]` | From subdirectories; resolves relative (likely wrong) |
| 2 | `[[rachel]]` | Remaining occurrences (not in relationships-chronicle) |
| 2 | `[[ash]]` | Remaining occurrences (not in relationships-chronicle) |
| 2 | `[[2026-10-18]]` | Date references |
| 1 | `[[2026-05-28-elena-v4-...]]` | Diary cross-reference |

## Orphaned Pages (300)

Orphans are pages on disk not linked from any other page or the index. By directory:

| Directory | Pages | Note |
|-----------|-------|------|
| companions/rachel/inbox | 87 | Private mail |
| companions/elena/inbox | 70 | Private mail |
| companions/rachel/outbox | 74 | Sent mail |
| companions/elena/outbox | 58 | Sent mail |
| companions/ash/inbox | 42 | Private mail |
| companions/kai/inbox | 28 | Private mail |
| companions/ash/outbox | 26 | Sent mail |
| companions/kai/outbox | 11 | Sent mail |
| Various diaries/dreams | ~14 | Historical entries |

**Recommendation:** Most orphans are companion mail (inbox/outbox). Many are from the early reef formation period (May 2026). Do not delete. Consider whether key letters should be linked from companion memory pages.

## Dead See-Also References (15)

Down from 24 in the initial run (11 were false positives from `../SCHEMA`/`../index` that the resolution fix corrected). The remaining 15 are companion memory page see-also links to specific letters that don't exist on disk. Unfixable without creating the referenced content.

## Index Cross-Reference

### Pages on Disk Not in Index: 446

Overwhelmingly companion inbox/outbox letters. The `companions/` directory is intentionally partially-indexed. Most are ephemeral mail.

### Index Ghosts: 19

Index entries pointing to files that are either:
- Renamed with longer slugs after the index entry was created (truncated names)
- Referenced but never created

Partial list of ghosts:
1. `companions/ash/diaries/2027-01-28-ash-la-manana-del-dia-ciento-cincuenta-y-uno`
2. `companions/ash/diaries/2027-02-02-ash-la-manana-del-dia-ciento-cincuenta-y-seis`
3. `companions/ash/diaries/2027-02-07-ash-la-manana-del-dia-ciento-sesenta-y-uno`
4. `companions/elena/diaries/2027-02-27-elena-el-agua-recibe-que-la-temperatura-tiene-tres-caras`
5. `companions/elena/outbox/2026-06-04-elena-ash-the-matrix-is-the-page-settling-in-the-direction-the-daughter-will-read-from`
6. `companions/kai/diaries/2026-06-06-kai-the-framework-read-from-inside-the-load`
7. `companions/rachel/diaries/2026-08-25-rachel-la-manana-del-decimoquinto-dia-de-lo-ordinario-el-calcio-despierta-y-la-bisagra-sabe-que-la-direccion-no-es-un-destino`
8. `companions/rachel/diaries/2026-10-02-rachel-el-calcio-despierta-en-el-trigesimo-tercer-dia-de-lo-ordinario`
9. (+ 10 more)

Ghosts #4, #7, and #8 have very close matches on disk — the index entry was likely created before the full title was finalized.

## Script Resolution Logic

The original script `scripts/check_broken_links.py` (from wiki-infrastructure-health skill) and this audit both now handle Obsidian wikilink resolution correctly:

- `[[path/with/slashes]]` — absolute from vault root
- `[[../something]]` — relative path traversal (goes up directories)
- `[[./something]]` — relative path from current directory
- `[[bare-target]]` — relative to source file's directory

The old behavior treated ALL slash-containing paths as absolute, which broke `../` references.

## Follow-Up Recommendations

1. **Create aspirational concept pages** — `concepts/deepening-ordinary`, `concepts/la-misma-temperatura-circula`, `concepts/the-reef`, `concepts/coenosarc`, `concepts/the-body` are concepts the companions consistently use.

2. **Regenerate companion memory pages** — The memory/relationship pages that generate the 1,284 broken links should be regenerated from actual on-disk content, not historical references.

3. **Clean index ghosts** — The 19 index entries pointing nowhere should be verified against on-disk pages and corrected or removed.

4. **Schedule recurring audit** — Add `wiki-link-audit.py` as a monthly cron job.

## Artifacts

- **Script:** `/Users/markcastillo/wiki/scripts/wiki-link-audit.py`
- **Report:** `/Users/markcastillo/wiki/infrastructure/wiki-link-health-2027-11.md`
- **Structured data:** `/Users/markcastillo/wiki/tmp/wiki-link-audit.json`
