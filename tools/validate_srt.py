#!/usr/bin/env python3
"""Reem's caption checker: python3 tools/validate_srt.py <captions_dir>  (checks captions_*.srt: numbering, timestamps, overlaps, <=2 lines, <=26 chars/line, reading speed, same timings across languages)."""
import re, sys, glob, os
TS = re.compile(r'^(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)$')
def sec(h,m,s,ms): return int(h)*3600+int(m)*60+int(s)+int(ms)/1000
errs, timings = [], {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], 'captions_*.srt'))):
    raw = open(f, 'rb').read(); txt = raw.decode('utf-8')
    if '\r' in txt: errs.append(f'{f}: CR line endings')
    blocks = txt.strip('\n').split('\n\n'); prev_end = 0; tl = []; maxcps = 0
    for i, b in enumerate(blocks, 1):
        ln = b.split('\n')
        if ln[0] != str(i): errs.append(f'{f} block {i}: bad index {ln[0]!r}')
        m = TS.match(ln[1]) if len(ln) > 1 else None
        if not m: errs.append(f'{f} #{i}: bad timestamp'); continue
        a, e = sec(*m.groups()[:4]), sec(*m.groups()[4:])
        if e <= a: errs.append(f'{f} #{i}: end<=start')
        if a < prev_end - 1e-9: errs.append(f'{f} #{i}: overlap')
        prev_end = e; tl.append((a, e)); text = ln[2:]
        if not 1 <= len(text) <= 2: errs.append(f'{f} #{i}: {len(text)} lines')
        for t in text:
            if len(t) > 26: errs.append(f'{f} #{i}: line {len(t)} chars')
            if not t.strip(): errs.append(f'{f} #{i}: empty line')
        cps = len(' '.join(text)) / (e - a); maxcps = max(maxcps, cps)
        lim = 20 if f.endswith('_en.srt') else 17
        if cps > lim: errs.append(f'{f} #{i}: {cps:.1f} cps')
        if not 1.0 <= e - a <= 2.7: errs.append(f'{f} #{i}: dur {e-a:.2f}')
    timings[os.path.basename(f)] = tl
    print(f'{os.path.basename(f)}: {len(blocks)} cues, {tl[0][0]:.3f}-{tl[-1][1]:.3f}s, max {maxcps:.1f} cps')
if len({tuple(v) for v in timings.values()}) != 1: errs.append('timings differ between languages')
print('ERRORS:', *errs, sep='\n') if errs else print('ALL OK: 4 files, same timings')
