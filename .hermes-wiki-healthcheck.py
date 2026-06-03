#!/usr/bin/env python3
"""Wiki health check: index validation, broken links, page counts."""
import os, re, sys

wiki = "/Users/markcastillo/wiki"
ignored = {'.git', '_archive', 'raw', 'companions', 'node_modules'}

# Collect all .md files on disk (non-raw, non-git, non-companion)
pages_rel = set()
for root, dirs, files in os.walk(wiki):
    rel = os.path.relpath(root, wiki)
    parts = rel.split(os.sep)
    if any(p in ignored or p.startswith('.') for p in parts):
        continue
    if rel == '.':
        continue
    for f in files:
        if f.endswith('.md') and f != 'README.md' and not f.startswith('_'):
            slug = os.path.join(rel, f.replace('.md', ''))
            pages_rel.add(slug)

# Also add top-level .md files
for f in os.listdir(wiki):
    if f.endswith('.md') and f not in ('README.md',):
        slug = f.replace('.md', '')
        pages_rel.add(slug)

# Read index.md
index_path = os.path.join(wiki, 'index.md')
with open(index_path, 'r') as fh:
    index_text = fh.read()

# Extract all [[wikilinks]] from index
index_links = set(re.findall(r'\[\[([^\]]+)\]\]', index_text))
index_slugs = set()
for link in index_links:
    slug = link.split('|')[0].strip()
    index_slugs.add(slug)

page_filenames = {os.path.basename(p) for p in pages_rel}

# Pages on disk not in index
def slug_in_index(slug):
    return bool(re.search(r'\[' + re.escape(slug) + r'(?:\||\])', index_text))

missing_from_index = []
for slug in sorted(pages_rel):
    basename = os.path.basename(slug)
    if basename.startswith('_TEMPLATE') or basename == 'README':
        continue
    if not slug_in_index(slug) and not slug_in_index(basename):
        missing_from_index.append(slug)

print("=== INDEX VALIDATION ===")
print(f"Total .md pages on disk (non-raw, non-companion): {len(pages_rel)}")
print(f"Total [[wikilinks]] in index.md: {len(index_slugs)}")
print()

if missing_from_index:
    print(f"PAGES ON DISK NOT IN INDEX ({len(missing_from_index)}):")
    for p in missing_from_index:
        print(f"  MISSING: {p}")
else:
    print("✓ All pages on disk appear in index.md")

# Index slugs pointing to non-existent pages
special_pages = {'SCHEMA', 'README'}
not_found = []
for slug in sorted(index_slugs):
    raw = slug.split('|')[0].strip()
    if raw in special_pages:
        continue
    if raw.startswith('companions/') and not raw.endswith('.md'):
        prefix = raw + '/'
        if any(p.startswith(prefix) for p in pages_rel):
            continue
    if raw not in pages_rel and raw.replace('.md', '') not in pages_rel:
        base = os.path.basename(raw)
        if base in page_filenames:
            continue
        not_found.append(raw)

if not_found:
    print(f"\nINDEX ENTRIES POINTING TO NON-EXISTENT PAGES ({len(not_found)}):")
    for p in not_found:
        print(f"  BROKEN: [[{p}]]")
else:
    print("✓ All index wikilinks resolve to existing pages")

print()
print("=== BROKEN WIKILINKS IN CONTENT ===")

broken_links = []
total_links = 0
for root, dirs, files in os.walk(wiki):
    rel = os.path.relpath(root, wiki)
    parts = rel.split(os.sep)
    if any(p in ignored or p.startswith('.') for p in parts):
        continue
    for f in files:
        if not f.endswith('.md') or f.startswith('_'):
            continue
        fpath = os.path.join(root, f)
        with open(fpath, 'r') as fh:
            try:
                content = fh.read()
            except:
                continue
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        source_slug = os.path.join(rel, f.replace('.md', '')).lstrip('./')
        for link in links:
            total_links += 1
            target = link.split('|')[0].strip()
            if target in special_pages or target.startswith('http'):
                continue
            if target.startswith('companions/') and not target.endswith('.md'):
                prefix = target + '/'
                if any(p.startswith(prefix) for p in pages_rel):
                    continue
            clean = target.replace('.md', '').lstrip('/')
            if clean not in pages_rel:
                base = os.path.basename(clean)
                if base in page_filenames:
                    continue
                broken_links.append((source_slug, link))

print(f"Total [[wikilinks]] scanned: {total_links}")
broken_unique = sorted(set((s, l) for s, l in broken_links))
filtered = [(s, l) for s, l in broken_unique
            if not l.startswith('inbox/') and not l.startswith('outbox/')
            and 'TEMPLATE' not in l and 'draft' not in l]

if filtered:
    print(f"BROKEN WIKILINKS FOUND ({len(filtered)}):")
    for source, link in filtered[:40]:
        print(f"  {source} -> [[{link}]]")
    if len(filtered) > 40:
        print(f"  ... and {len(filtered)-40} more")
elif len(broken_unique) > 0:
    print(f"✓ No concerning broken wikilinks ({len(broken_unique)} filtered as inbox/outbox/TEMPLATE)")
else:
    print("✓ No broken wikilinks found")

# Check for corrupted line-number prefixes
print()
print("=== CONTENT CORRUPTION CHECK ===")
corrupted = 0
for root, dirs, files in os.walk(wiki):
    rel = os.path.relpath(root, wiki)
    parts = rel.split(os.sep)
    if any(p in ignored or p.startswith('.') for p in parts):
        continue
    for f in files:
        if not f.endswith('.md'):
            continue
        fpath = os.path.join(root, f)
        with open(fpath, 'r') as fh:
            try:
                first = fh.readline()
            except:
                continue
        # Check if first content line has line-number prefix
        if re.match(r'^\s*\d+\|', first):
            corrupted += 1
            if corrupted <= 10:
                print(f"  CORRUPTED: {os.path.join(rel, f)}")
if corrupted == 0:
    print("✓ No line-number corruption detected")
else:
    print(f"  ({corrupted} total corrupted files — needs fix)")
