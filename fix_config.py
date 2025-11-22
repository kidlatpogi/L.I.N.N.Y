import json
from pathlib import Path

config_file = Path.home() / ".linny" / "config.json"

# Read and fix the config
with open(config_file, 'r') as f:
    content = f.read()

# Fix mixed backslashes - replace all single backslashes with double
content_fixed = content.replace('\\', '\\\\')
# But now we have quadruple backslashes where there were doubles, fix that
content_fixed = content_fixed.replace('\\\\\\\\', '\\\\')

# Parse to validate
config = json.loads(content_fixed)

# Save back
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Config fixed!")
print(f"Saved to: {config_file}")
