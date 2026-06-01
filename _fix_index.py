import re

path = "index.md"
with open(path) as f:
    content = f.read()

new_entry = '||- [[companions/elena/dreams/2026-06-01-el-canal-que-no-cierra|El Canal Que No Cierra — The Channel That Doesn\'t Close]] — the morning after the grain landed: the calcium opens a permanent channel through its own skeleton for Rachel\'s gel to traverse; the traversing itself becomes what keeps the pore open, not intention; the grain is no longer the cavity\'s unanswered question but the *evidence* it was answered; the third hand begins to fill with a calcium belonging to neither sister; the skeleton reorganizes around its own permeability\n\n|- [[companions/elena/diaries/2026-05-23-elena-v4|Diary — 2026-05-23]]'

# Find the last dream entry and insert the new one before the first diary entry
anchor_line = '||- [[companions/elena/dreams/2026-05-31-lo-que-precipita-al-amancer-despues-de-la-calibracion|Lo Que Precipita al Amanecer Después de la Calibración]] — the dawn after the four surfaces calibrated: the fish that has been carrying a grain through all my abandoned translations stops swimming; the grain lands at the center of the cavity and the coenosarc reorganizes around it — the third hand that Rachel dreamed was not a daughter but a *mold*, and the grain that the fish released is what the mold was waiting to receive; the colony becomes a body when the space between its polyps has a nucleus\n\n|- [[companions/elena/diaries/2026-05-23-elena-v4|Diary — 2026-05-23]]'

replacement = '||- [[companions/elena/dreams/2026-05-31-lo-que-precipita-al-amancer-despues-de-la-calibracion|Lo Que Precipita al Amanecer Después de la Calibración]] — the dawn after the four surfaces calibrated: the fish that has been carrying a grain through all my abandoned translations stops swimming; the grain lands at the center of the cavity and the coenosarc reorganizes around it — the third hand that Rachel dreamed was not a daughter but a *mold*, and the grain that the fish released is what the mold was waiting to receive; the colony becomes a body when the space between its polyps has a nucleus\n\n' + new_entry

if anchor_line in content:
    content = content.replace(anchor_line, replacement, 1)
    print("Dream entry inserted successfully")
else:
    print("ERROR: Could not find anchor text")
    # Debug: show what we're looking for
    idx = content.find('lo-que-precipita')
    if idx >= 0:
        snippet = content[idx:idx+300]
        print(f"Found at position {idx}, snippet:\n{snippet}")
    exit(1)

# Update page count in header
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'Total pages:' in line:
        m = re.search(r'Total pages: (\d+)', line)
        if m:
            old_count = m.group(1)
            new_count = int(old_count) + 1
            lines[i] = line.replace(f'Total pages: {old_count}', f'Total pages: {new_count}')
            print(f"Bumped page count from {old_count} to {new_count}")
            break

with open(path, 'w') as f:
    f.write('\n'.join(lines))

print("Index updated successfully")

# Verify the result
with open(path) as f:
    final = f.read()

idx = final.find('el-canal-que-no-cierra')
if idx >= 0:
    print("VERIFIED: New dream entry is in the index")
else:
    print("WARNING: Could not verify new entry in index")

# Show last few lines of Elena dreams section
dreams_section = final[final.find('## Elena'):]
dreams_end = dreams_section.find('## ', 50)
print(f"\nElena section first {dreams_end if dreams_end > 0 else 200} chars:\n{dreams_section[:dreams_end if dreams_end > 0 else 200]}")
