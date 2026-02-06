import json
import sys
from pathlib import Path

# Read original file with proper encoding detection
input_path = Path(sys.argv[1])
output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix('.fixed.json')

# Try different encodings
for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
    try:
        with open(input_path, 'r', encoding=encoding) as f:
            data = json.load(f)
        print(f"Successfully read with encoding: {encoding}")
        break
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"Failed with {encoding}: {e}")
        continue
else:
    print("Could not read file with any encoding")
    sys.exit(1)

# Write as clean UTF-8 without BOM
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Fixed file written to: {output_path}")
