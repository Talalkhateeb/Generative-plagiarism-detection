#!/usr/bin/env python3
from pathlib import Path
import shutil
root=Path('GPD_front')
files=[p for p in root.rglob('*') if p.is_file()]
count=0
for p in files:
    try:
        s=p.read_text(encoding='utf-8')
    except Exception:
        continue
    if '<<<<<<<' in s:
        lines=s.splitlines(keepends=True)
        out=[]
        i=0
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
            else:
                out.append(lines[i]); i+=1
        bak=p.with_suffix(p.suffix + '.bak')
        try:
            p.rename(bak)
        except Exception:
            shutil.copy(p, bak)
        p.write_text(''.join(out), encoding='utf-8')
        print('Fixed', p)
        count+=1
print('Done. Files fixed:', count)
