import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'workspaces/t2'))
from duration import parse_duration
assert parse_duration('1d2h3m4s5ms') == 93784005
assert parse_duration('0s') == 0
assert parse_duration('18446744073709551616ms') == 2**64
for invalid in ('1s1m','1s2s','1s 2ms','0s1ms'):
    try:
        parse_duration(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(invalid)
print('T2 minimal acceptance PASS: combination, zero, huge, invalid order/duplicate/space/zero segment')
