#!/usr/bin/env python3
import os
import sys
from pathlib import Path

root = Path('.')
conflicted = []
for p in root.rglob('*'):
    if p.is_file():
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        if '<<<<<<<' in text:
            conflicted.append(p)

if not conflicted:
    print('No files with conflict markers found.')
    sys.exit(0)

print(f'Found {len(conflicted)} files with conflict markers')
for p in conflicted:
    print('Processing', p)
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    out_lines = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        if line.startswith('<<<<<<<'):
            # skip until =======, keep the 'theirs' side
            i += 1
            # skip 'ours' side
            while i < len(lines) and not lines[i].startswith('======='):
                i += 1
            if i < len(lines) and lines[i].startswith('======='):
                i += 1
            # now copy 'theirs' until >>>>>>>
            while i < len(lines) and not lines[i].startswith('>>>>>>>'):
                out_lines.append(lines[i])
                i += 1
            # skip the >>>>>>> line
            if i < len(lines) and lines[i].startswith('>>>>>>>'):
                i += 1
            changed = True
        else:
            out_lines.append(line)
            i += 1
    if changed:
        backup = p.with_suffix(p.suffix + '.bak')
        try:
            p.rename(backup)
        except Exception:
            # fallback copy
            import shutil
            shutil.copy(p, backup)
        p.write_text(''.join(out_lines), encoding='utf-8')
        print('Rewrote', p, '-> backup at', backup)

print('Done')
