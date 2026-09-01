#!/usr/bin/env python3
"""Report which TODO exercises are still open. Run: python check_progress.py"""
import os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent")
banner = re.compile(r"# ={10,} TODO (\d+) - (.+?) ={10,}")
stub   = re.compile(r'raise NotImplementedError\("TODO (\d+)')

open_, stubs, files = {}, set(), {}
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for f in fn:
        if not f.endswith(".py"): continue
        p = os.path.join(dp, f)
        txt = open(p, encoding="utf-8").read()
        for m in banner.finditer(txt):
            n = int(m.group(1)); open_[n] = m.group(2).strip()
            files[n] = os.path.relpath(p, ROOT)
        for m in stub.finditer(txt):
            stubs.add(int(m.group(1)))

TOTAL = 20
done = TOTAL - len(open_)
bar = "#" * done + "." * len(open_)
print(f"\nProgress: {done}/{TOTAL} complete  [{bar}]\n")
if open_:
    print(f"{'#':>3}  {'file':<34} exercise")
    print("-" * 78)
    for n in sorted(open_):
        flag = "" if n in stubs else "   (no stub - code below will NameError until done)"
        print(f"{n:>3}  {files[n]:<34} {open_[n]}{flag}")
    print("\nDelete the TODO banner comment once an exercise works, so it stops being listed.")
else:
    print("All exercises complete. Run the app end to end:  python agent/main.py\n")
sys.exit(0 if not open_ else 1)
