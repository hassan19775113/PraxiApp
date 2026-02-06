import json
import sys
from pathlib import Path

input_path = Path(sys.argv[1])
output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix('.filtered.json')

# Read fixture
with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter out Django auto-generated models that conflict with migrations
exclude_models = {
    'contenttypes.contenttype',  # Auto-created by Django
    'auth.permission',  # Auto-created based on models
}

filtered = [
    obj for obj in data
    if obj.get('model') not in exclude_models
]

print(f"Original: {len(data)} objects")
print(f"Filtered: {len(filtered)} objects")
print(f"Removed: {len(data) - len(filtered)} objects")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"Wrote: {output_path}")
