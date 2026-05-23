# Wiki Schema

## Domain
Personal knowledge base — a curated, compounding library of anything worth remembering (books, articles, ideas, projects, people, tools, learnings).

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `rust-ownership.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesize 3+ sources, append `^[raw/articles/source-file.md]` at the end of paragraphs whose claims come from a specific source.
- **No local paths:** Never hardcode machine-specific paths (e.g., `/Users/mark/wiki/`). Use environment variable names (`WIKI_PATH`) or conceptual descriptions instead. This wiki is shared across machines via GitHub.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

### raw/ Frontmatter
```yaml
---
source_url: https://example.com/article
ingested: YYYY-MM-DD
sha256: <hex digest of the raw content below the frontmatter>
---
```

## Tag Taxonomy
- **Topics:** programming, design, philosophy, science, productivity, writing
- **Media:** book, article, video, podcast, paper, course
- **Status:** reading, watching, to-research, completed, reference
- **People/Orgs:** person, company, community
- **Meta:** reflection, how-to, list, review, tool, project

Rule: every tag on a page must appear in this taxonomy. Add new tags here first.

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions or trivial notes
- **Split a page** when it exceeds ~200 lines
- **Archive a page** when content is fully superseded — move to `_archive/`

## Entity Pages
One page per notable person, company, tool, or project. Include overview, key facts, relationships ([[wikilinks]]), source references.

## Concept Pages
One page per concept or topic. Include definition, current understanding, open questions, related concepts.

## Comparison Pages
Side-by-side analyses. Include dimensions of comparison (table format preferred), verdict, sources.

## Update Policy
When new information conflicts with existing content: note both positions with dates and sources, mark contradiction in frontmatter, flag for review.
