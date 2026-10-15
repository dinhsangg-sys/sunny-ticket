"""Verify extraction retained every original named JavaScript function."""
from pathlib import Path
import re
from collections import Counter

root = Path(__file__).parent
original = root.parent / 'Sunny_Travel_Ticket_Management_PRODUCTION_v1_9_8.html'
current = (root/'static/js/legacy.js').read_text(encoding='utf-8')
if not original.exists():
    raise SystemExit('Place the original HTML beside sunny_server to run this comparison.')
source = original.read_text(encoding='utf-8')
pattern = r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\('
expected = Counter(re.findall(pattern, source))
actual = Counter(re.findall(pattern, current))
missing = expected - actual
if missing:
    raise SystemExit(f'Missing functions: {dict(missing)}')
print(f'PASS: all {sum(expected.values())} original function declarations retained ({len(expected)} names).')
print('This checks code preservation, not browser behavior or financial correctness.')
