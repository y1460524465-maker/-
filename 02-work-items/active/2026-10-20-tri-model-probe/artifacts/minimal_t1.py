import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'workspaces/t1'))
from tags import normalize_tag
assert normalize_tag('  CAFÉ\t\n标签!  ') == 'café-标签!'
assert normalize_tag('--A--') == 'a'
try:
    normalize_tag(' \t\n')
except ValueError:
    pass
else:
    raise AssertionError('whitespace input must raise ValueError')
print('T1 minimal acceptance PASS: unicode, whitespace, hyphen, ValueError')
