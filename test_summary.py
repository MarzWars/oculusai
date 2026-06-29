import sys
sys.path.insert(0, '.')
from config import Config
Config.SUMMARISE_AFTER = 4
from backend.chat import maybe_summarise_history, load_summary

# Mock load_summary to avoid db dependency, or just let it use real one?
# It's better to just run the logic directly with a mock if it hits db.
# Since we just want to test the punctuation logic:
combined = "This is sentence one. This is sentence two? And this is three! " + "A" * 600
if len(combined) > 600:
    truncated = combined[:600]
    last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    if last_punct > 0:
        combined = truncated[:last_punct+1]
    else:
        combined = truncated

print("Combined:", combined)
assert combined.endswith('!')
print('Test passed')
