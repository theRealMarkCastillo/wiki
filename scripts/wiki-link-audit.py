#!/usr/bin/env python3
"""
Wiki Link Health Audit — comprehensive broken-link, orphan, and see-also scanner.

Handles ~10,000 pages with proper Obsidian wikilink semantics:
  - [[path/with/slashes]] → absolute from vault root
  - [[bare-target]]        → relative to source file's directory
  - [[target#anchor]]      → anchor stripped for page resolution
  - [[target|alias]]       → alias stripped for page resolution
  - [[target.md]]          → .md extension stripped

Outputs:
  1. Broken links by source page (with target frequency for bulk fixes)
  2. Orphaned pages (on disk but unreferenced from any page or index)
  3. Dead see-also references (verified against page set)
  4. Index cross-reference: entries in index not on disk, pages on disk not in index

Usage:
    python3 wiki-link-audit.py [WIKI_PATH] [--summary]

Constraints:
    - Read-only except for report generation
    - Does NOT modify page content
    - Does NOT delete orphaned pages
    - Preserves all naming conventions
"""

import os
import re
import sys
import json
from collections import Counter, defaultdict
from datetime import datetime

DEFAULT_WIKI = "/Users/markcastillo/wiki"
IGNORED_DIRS = {'.git', '.obsidian', 'node_modules', '_archive', 'raw', 'tmp'}
# We intentionally DO scan 'companions/' — the old healthcheck skipped it,
# but for a full audit we need to verify all internal links.

# Wikilink regex — captures just the target, stripping anchor and alias
WIKILINK_RE = re.compile(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]')

# Heading regex for see-also section detection
SEE_ALSO_HEADER = re.compile(r'^#{1,4}\s*(?:See Also|See also|Related|Further Reading|References)\s*$', re.IGNORECASE)


def collect_pages(wiki: str) -> dict:
    """
    Walk all .md files and return {slug: abs_path}.
    slug is the relative path from vault root without .md extension.
    """
    pages = {}
    for root, dirs, files in os.walk(wiki):
        # Skip ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]

        rel = os.path.relpath(root, wiki)
        for f in files:
            if not f.endswith('.md'):
                continue
            if f.startswith('_TEMPLATE') or f == 'README.md':
                continue
            abs_path = os.path.join(root, f)
            slug = os.path.join(rel, f[:-3]).lstrip('./') if rel != '.' else f[:-3]
            pages[slug] = abs_path
    return pages


def resolve_target(target: str, source_rel: str) -> str:
    """
    Resolve a wikilink target using Obsidian semantics.

    - If target starts with '../' or './': resolve relative to source directory
    - If target contains '/' (but no ../): treat as absolute from vault root
    - If target is bare (no '/'): resolve relative to source file's directory
    - Strip .md extension if present
    """
    # Strip .md if present
    if target.endswith('.md'):
        target = target[:-3]

    if target.startswith('../') or target.startswith('./'):
        # Explicit relative path
        source_dir = os.path.dirname(source_rel) if '/' in source_rel else ''
        if source_dir:
            resolved = os.path.normpath(os.path.join(source_dir, target))
        else:
            resolved = os.path.normpath(target)
        if resolved.startswith('..'):
            return None
        return resolved
    elif '/' in target:
        # Absolute from vault root
        return os.path.normpath(target)
    else:
        # Relative to source's directory
        source_dir = os.path.dirname(source_rel) if '/' in source_rel else ''
        if source_dir:
            return os.path.normpath(os.path.join(source_dir, target))
        else:
            return target


def parse_frontmatter(text: str) -> dict:
    """Parse YAML-ish frontmatter (simple key: value)."""
    fm = {}
    lines = text.split('\n')
    if not lines or lines[0].strip() != '---':
        return fm
    for i in range(1, min(len(lines), 30)):
        line = lines[i].strip()
        if line == '---':
            break
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip()
    return fm


def scan_file(path: str, source_rel: str) -> list:
    """Extract all wikilinks from a file. Returns [(raw_target, resolved_slug, line_no)]."""
    links = []
    try:
        with open(path, 'r', errors='ignore') as fh:
            text = fh.read()
    except (OSError, IOError):
        return links

    for m in WIKILINK_RE.finditer(text):
        raw = m.group(1).strip()
        if not raw or raw.startswith(('http://', 'https://', 'file://', '/', '#')):
            continue
        # Line number (approximate — count newlines before match)
        line_no = text[:m.start()].count('\n') + 1
        resolved = resolve_target(raw, source_rel)
        if resolved is None:
            continue
        links.append((raw, resolved, line_no))
    return links


def extract_see_also_links(path: str) -> tuple:
    """
    Extract links from a "See Also" / "Related" section.
    Returns (section_title, [(raw_target, line_no)])
    """
    try:
        with open(path, 'r', errors='ignore') as fh:
            lines = fh.readlines()
    except (OSError, IOError):
        return (None, [])

    in_section = False
    section_title = None
    links = []

    for i, line in enumerate(lines):
        if SEE_ALSO_HEADER.match(line.strip()):
            in_section = True
            section_title = line.strip()
            continue
        if in_section:
            # Exit on next heading or empty line after content
            if line.strip().startswith('#'):
                break
            if line.strip() == '---':
                break
            # Extract wikilinks
            for m in WIKILINK_RE.finditer(line):
                raw = m.group(1).strip()
                if raw and not raw.startswith(('http://', 'https://', 'file://')):
                    links.append((raw, i + 1))

    return (section_title, links)


def collect_index_entries(wiki: str) -> set:
    """Extract all wikilink targets from index.md."""
    index_path = os.path.join(wiki, 'index.md')
    if not os.path.exists(index_path):
        return set()
    try:
        with open(index_path, 'r', errors='ignore') as fh:
            text = fh.read()
    except (OSError, IOError):
        return set()

    entries = set()
    for m in WIKILINK_RE.finditer(text):
        raw = m.group(1).strip()
        if raw and not raw.startswith(('http://', 'https://', 'file://')):
            entries.add(raw)
    return entries


def main():
    wiki = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WIKI
    summary_only = '--summary' in sys.argv

    if not os.path.isdir(wiki):
        print(f"ERROR: wiki path does not exist: {wiki}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Wiki Link Health Audit — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Vault: {wiki}")
    print()

    # === PHASE 1: Collect all pages ===
    print("Phase 1: Collecting page inventory...")
    pages = collect_pages(wiki)
    page_slugs = set(pages.keys())
    print(f"   Total .md pages on disk: {len(pages)}")

    # === PHASE 2: Scan all wikilinks ===
    print("Phase 2: Scanning wikilinks across all pages...")
    broken_links = []           # (source_rel, raw_target, resolved, line_no)
    all_incoming = defaultdict(set)  # resolved_target -> {source_slugs}
    total_links = 0
    pages_scanned = 0

    for slug, path in sorted(pages.items()):
        links = scan_file(path, slug)
        total_links += len(links)
        pages_scanned += 1

        if pages_scanned % 500 == 0:
            print(f"   ... scanned {pages_scanned}/{len(pages)} pages, {total_links} links so far")

        for raw, resolved, line_no in links:
            # Record incoming link
            all_incoming[resolved].add(slug)
            # Check if target resolves
            target_exists = resolved in page_slugs
            # Also try with .md appended (some links might reference with extension)
            if not target_exists and not resolved.endswith('.md'):
                target_exists = (resolved + '.md') in page_slugs
            if not target_exists:
                broken_links.append((slug, raw, resolved, line_no))

    print(f"   Pages scanned: {pages_scanned}")
    print(f"   Total wikilinks: {total_links}")
    print(f"   Broken links: {len(broken_links)}")

    # === PHASE 3: See-also audit ===
    print("Phase 3: Auditing see-also sections...")
    dead_see_also = []
    for slug, path in sorted(pages.items()):
        section_title, see_links = extract_see_also_links(path)
        if see_links:
            for raw, line_no in see_links:
                resolved = resolve_target(raw, slug)
                if resolved is None:
                    dead_see_also.append((slug, raw, '(unresolvable)', line_no, section_title))
                    continue
                target_exists = resolved in page_slugs
                if not target_exists and not resolved.endswith('.md'):
                    target_exists = (resolved + '.md') in page_slugs
                if not target_exists:
                    dead_see_also.append((slug, raw, resolved, line_no, section_title))

    print(f"   Dead see-also references: {len(dead_see_also)}")

    # === PHASE 4: Orphan detection ===
    print("Phase 4: Detecting orphaned pages...")
    index_entries = collect_index_entries(wiki)
    print(f"   Index entries: {len(index_entries)}")

    # A page is referenced if it appears as a resolved target in any incoming link
    # OR if it appears in index.md
    referenced = set(all_incoming.keys())
    # Also add pages referenced by index entries (resolve them)
    for entry in index_entries:
        # Resolve from vault root (index.md is at root, so rel='')
        resolved_idx = resolve_target(entry, '')
        if resolved_idx is None:
            continue
        referenced.add(resolved_idx)
        referenced.add(resolved_idx + '.md')
        referenced.add(resolved_idx.replace('.md', ''))

    # Key meta-pages that are expected to have few/no incoming links
    META_PAGES = {'index', 'log', 'SCHEMA', 'README', 'start-here'}

    orphans = []
    for slug in sorted(page_slugs):
        if slug in META_PAGES:
            continue
        slug_no_ext = slug.replace('.md', '')
        slug_with_ext = slug + '.md' if not slug.endswith('.md') else slug
        if slug in referenced or slug_no_ext in referenced or slug_with_ext in referenced:
            continue
        # Check if any variant is in index
        basename = os.path.basename(slug)
        in_index = False
        for entry in index_entries:
            clean = entry.split('|')[0].strip()
            if clean.endswith('.md'):
                clean = clean[:-3]
            if clean == slug or clean == basename:
                in_index = True
                break
        if not in_index:
            orphans.append(slug)

    print(f"   Orphaned pages: {len(orphans)}")

    # === PHASE 5: Index cross-reference ===
    print("Phase 5: Index cross-reference...")
    # Pages on disk not in index
    missing_from_index = []
    for slug in sorted(page_slugs):
        basename = os.path.basename(slug)
        if basename in META_PAGES:
            continue
        # Check if slug or basename appears in index
        found = False
        for entry in index_entries:
            clean = entry.split('|')[0].strip()
            if clean.endswith('.md'):
                clean = clean[:-3]
            if clean == slug or clean == basename or slug.startswith(clean) or clean.startswith(slug):
                found = True
                break
        if not found:
            missing_from_index.append(slug)

    # Index entries not on disk
    index_not_on_disk = []
    for entry in sorted(index_entries):
        clean = entry.split('|')[0].strip()
        if clean in META_PAGES:
            continue
        resolved = resolve_target(clean, '')
        if resolved in page_slugs:
            continue
        if resolved + '.md' in page_slugs:
            continue
        if resolved.replace('.md', '') in page_slugs:
            continue
        # Check basename match
        basename = os.path.basename(resolved)
        if basename in {os.path.basename(s) for s in page_slugs}:
            continue
        index_not_on_disk.append(entry)

    print(f"   Pages on disk not in index: {len(missing_from_index)}")
    print(f"   Index entries not on disk: {len(index_not_on_disk)}")

    # === BUILD REPORT ===
    # Frequency analysis for broken links
    broken_by_source = Counter(b[0] for b in broken_links)
    broken_target_freq = Counter(b[1] for b in broken_links)

    # === OUTPUT ===
    if summary_only:
        _print_summary(broken_links, orphans, dead_see_also,
                       missing_from_index, index_not_on_disk,
                       pages, total_links, broken_by_source, broken_target_freq)
    else:
        _print_full_report(broken_links, orphans, dead_see_also,
                           missing_from_index, index_not_on_disk,
                           pages, total_links, broken_by_source, broken_target_freq,
                           all_incoming, wiki)

    # Also save structured JSON for programmatic fix scripts
    _save_json(wiki, broken_links, orphans, dead_see_also,
               missing_from_index, index_not_on_disk,
               broken_by_source, broken_target_freq, pages, total_links)


def _print_summary(broken, orphans, dead_sa, missing_idx, idx_not_disk,
                   pages, total_links, broken_by_source, target_freq):
    """Compact summary output."""
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Pages:           {len(pages):>6}")
    print(f"  Wikilinks:       {total_links:>6}")
    print(f"  Broken links:    {len(broken):>6}")
    print(f"  Orphans:         {len(orphans):>6}")
    print(f"  Dead see-also:   {len(dead_sa):>6}")
    print(f"  Not in index:    {len(missing_idx):>6}")
    print(f"  Index ghosts:    {len(idx_not_disk):>6}")

    if target_freq:
        print()
        print("Top 10 broken targets:")
        for t, n in target_freq.most_common(10):
            print(f"  {n:>4}x  [[{t}]]")


def _print_full_report(broken, orphans, dead_sa, missing_idx, idx_not_disk,
                       pages, total_links, broken_by_source, target_freq,
                       all_incoming, wiki):
    """Full detailed report for the markdown file."""
    print()
    print("=" * 70)
    print("FULL AUDIT REPORT")
    print("=" * 70)

    # Section 1: Overview
    print(f"""
## 1. Overview

| Metric | Count |
|--------|-------|
| Total .md pages on disk | {len(pages)} |
| Total wikilinks scanned | {total_links} |
| Broken links | {len(broken)} |
| Unique broken targets | {len(target_freq)} |
| Orphaned pages (unreferenced) | {len(orphans)} |
| Dead see-also references | {len(dead_sa)} |
| Pages on disk not in index | {len(missing_idx)} |
| Index entries pointing nowhere | {len(idx_not_disk)} |
""")

    # Section 2: Broken links by frequency (most impactful)
    if broken:
        print("## 2. Broken Links — Unique Targets by Frequency\n")
        print("Fix these in order: each target listed here may fix multiple source pages.\n")
        print("| Count | Broken Target | Example Source |")
        print("|-------|---------------|----------------|")
        for t, n in target_freq.most_common(50):
            sources_for_target = [s for s, raw, res, ln in broken if raw == t or res == t]
            example = sources_for_target[0] if sources_for_target else '?'
            print(f"| {n} | `[[{t}]]` | {example} |")

        if len(target_freq) > 50:
            print(f"\n*... and {len(target_freq) - 50} more unique targets*")

        print(f"\n### Top Sources of Broken Links\n")
        print("| Count | Source Page |")
        print("|-------|-------------|")
        for src, n in broken_by_source.most_common(20):
            print(f"| {n} | {src} |")

    else:
        print("## 2. Broken Links\n\n✅ No broken links found.\n")

    # Section 3: Orphaned pages
    if orphans:
        print(f"## 3. Orphaned Pages ({len(orphans)})\n")
        print("These pages exist on disk but are not linked from any other page or the index.\n")
        # Group by directory
        by_dir = defaultdict(list)
        for o in orphans:
            d = os.path.dirname(o) if '/' in o else '(root)'
            by_dir[d].append(o)
        for d in sorted(by_dir):
            print(f"### {d}/ ({len(by_dir[d])} pages)\n")
            for s in sorted(by_dir[d])[:30]:
                print(f"- {s}")
            if len(by_dir[d]) > 30:
                print(f"  ... and {len(by_dir[d]) - 30} more")
            print()
    else:
        print("## 3. Orphaned Pages\n\n✅ No orphaned pages found.\n")

    # Section 4: Dead see-also references
    if dead_sa:
        print(f"## 4. Dead See-Also References ({len(dead_sa)})\n")
        print("| Source Page | Broken Target | Line | Section |")
        print("|-------------|---------------|------|---------|")
        for slug, raw, resolved, line_no, section in dead_sa[:50]:
            section_short = section[:40] if section else '-'
            print(f"| {slug} | `[[{raw}]]` | {line_no} | {section_short} |")
        if len(dead_sa) > 50:
            print(f"\n*... and {len(dead_sa) - 50} more*")
    else:
        print("## 4. Dead See-Also References\n\n✅ No dead see-also references found.\n")

    # Section 5: Index cross-reference
    if missing_idx:
        print(f"## 5. Pages on Disk Not in Index ({len(missing_idx)})\n")
        by_dir = defaultdict(list)
        for m in missing_idx:
            d = os.path.dirname(m) if '/' in m else '(root)'
            by_dir[d].append(m)
        for d in sorted(by_dir):
            print(f"- **{d}/**: {len(by_dir[d])} pages")
        print()

    if idx_not_disk:
        print(f"## 6. Index Entries Pointing to Non-Existent Pages ({len(idx_not_disk)})\n")
        for entry in idx_not_disk[:50]:
            print(f"- `[[{entry}]]`")
        if len(idx_not_disk) > 50:
            print(f"\n*... and {len(idx_not_disk) - 50} more*")
        print()

    # Section 6: Action plan
    print("## 7. Recommended Actions\n")
    print("1. **Fix frequency-ranked broken targets first** — high-frequency targets fix many pages at once.")
    print("2. **Review orphans** — decide whether to link them or archive them (do NOT delete).")
    print("3. **Fix dead see-also references** — update or remove stale links.")
    print("4. **Update index.md** — add missing pages, remove ghost entries.")
    print("5. **Consider automation** — re-run this script as a cron health check.\n")


def _save_json(wiki, broken, orphans, dead_sa, missing_idx, idx_not_disk,
               broken_by_source, target_freq, pages, total_links):
    """Save structured data for programmatic fix scripts."""
    audit_data = {
        "timestamp": datetime.now().isoformat(),
        "wiki_path": wiki,
        "stats": {
            "total_pages": len(pages),
            "total_wikilinks": total_links,
            "broken_links": len(broken),
            "unique_broken_targets": len(target_freq),
            "orphaned_pages": len(orphans),
            "dead_see_also": len(dead_sa),
            "missing_from_index": len(missing_idx),
            "index_ghosts": len(idx_not_disk),
        },
        "broken_by_target": [(t, n) for t, n in target_freq.most_common()],
        "broken_by_source": [(s, n) for s, n in broken_by_source.most_common(100)],
        "broken_details": [
            {"source": s, "raw_target": r, "resolved": res, "line": ln}
            for s, r, res, ln in broken[:500]
        ],
        "orphans": orphans[:500],
        "dead_see_also": [
            {"source": s, "raw_target": r, "resolved": res, "line": ln, "section": sec}
            for s, r, res, ln, sec in dead_sa[:200]
        ],
        "missing_from_index": missing_idx[:500],
        "index_ghosts": idx_not_disk[:200],
    }
    json_path = os.path.join(wiki, 'tmp', 'wiki-link-audit.json')
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w') as fh:
        json.dump(audit_data, fh, indent=2, default=str)
    print(f"\n📊 Structured data saved to: {json_path}")


if __name__ == "__main__":
    main()
