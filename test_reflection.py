import sys
sys.path.insert(0, '.')
from config import Config
from backend.chat import _should_run_reflection

print('Test 1: _should_run_reflection')
assert _should_run_reflection('hi', None) == False, 'Should block short msgs'
assert _should_run_reflection('I want to spend R500 on this ad.', None) == True, 'Should detect R500'
assert _should_run_reflection('I want to spend $5,000.50 on this ad.', None) == True, 'Should detect $5,000.50'
assert _should_run_reflection('short', {'action': 'web_search'}) == True, 'Should run on actions'

long_msg = 'word ' * 50
assert _should_run_reflection(long_msg, None) == True, 'Should run on >40 words'

print('_should_run_reflection OK')
print('ALL PASSED')
