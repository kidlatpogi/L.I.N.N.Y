import json
from pathlib import Path

config_file = Path.home() / ".linny" / "linny_config.json"

print(f"Checking: {config_file}")
print(f"Exists: {config_file.exists()}")

if config_file.exists():
    try:
        with open(config_file, 'r') as f:
            content = f.read()
            print(f"\n--- File Content ({len(content)} bytes) ---")
            print(content[:500])  # First 500 chars
            print("\n--- Parsing JSON ---")
            f.seek(0)
            config = json.load(f)
            print("✓ JSON is valid!")
            print(f"Keys: {list(config.keys())}")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Error: {e}")
        print(f"Line {e.lineno}, Column {e.colno}")
        print(f"Position: {e.pos}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
else:
    print("\n❌ Config file does not exist!")
    print("Creating template...")
    
    template = {
        "user_name": "Zeus",
        "language": "English",
        "timezone": "Asia/Manila",
        "voice_en": "en-PH-RosaNeural",
        "voice_tl": "fil-PH-BlessicaNeural",
        "groq_api_key": "",
        "gemini_api_key": "",
        "perplexity_api_key": "",
        "smart_bulb_ip": "",
        "app_aliases": {
            "teams": "msteams:",
            "themes": "msteams:",
            "spotify": "spotify:",
            "calculator": "calc"
        }
    }
    
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"✓ Created template at {config_file}")
