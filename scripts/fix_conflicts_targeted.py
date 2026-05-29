#!/usr/bin/env python3
from pathlib import Path
import sys

targets = [Path('AI'), Path('AI/pipeline'), Path('GPD_back/apps'), Path('storage_service')]
files = []
for t in targets:
    if t.exists():
        for p in t.rglob('*'):
            if p.is_file() and p.suffix in ('.py', '.txt') or p.name in ('requirements.txt', 'package.json'):
                try:
                    s = p.read_text(encoding='utf-8')
                except Exception:
                    continue
                if '<<<<<<<' in s:
                    files.append(p)

if not files:
    print('No targeted files with conflict markers found.')
    sys.exit(0)

print('Files to fix:', len(files))
for p in files:
    print('Fixing', p)
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    out=[]
    i=0
    changed=False
    while i<len(lines):
        if lines[i].startswith('<<<<<<<'):
            i+=1
            while i<len(lines) and not lines[i].startswith('======='):
                i+=1
            if i<len(lines) and lines[i].startswith('======='):
                i+=1
            while i<len(lines) and not lines[i].startswith('>>>>>>>'):
                out.append(lines[i]); i+=1
            if i<len(lines) and lines[i].startswith('>>>>>>>'):
                i+=1
            changed=True
        else:
            out.append(lines[i]); i+=1
    if changed:
        bak = p.with_suffix(p.suffix + '.bak')
        try:
            p.rename(bak)
        except Exception:
            import shutil
            shutil.copy(p, bak)
        p.write_text(''.join(out), encoding='utf-8')
        print('Rewrote', p)
print('Done')
