import json
import pandas as pd

# Load the generated JSON
with open("genshin_builds.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total Characters Scraped: {len(data)}")

# Create a summary table
summary = []
for char in data:
    build_count = len(char['builds'])
    
    # Check for specific failure points
    has_null_role = any(b['role'] is None for b in char['builds'])
    has_empty_weapons = any(len(b['weapons']) == 0 for b in char['builds'])
    
    summary.append({
        "Name": char['name'], 
        "Element": char['element'], 
        "Builds": build_count, 
        "Flags": "⚠️ EMPTY WEAPONS" if has_empty_weapons else "OK"
    })

# Convert to DataFrame for easy viewing
df = pd.read_json(json.dumps(summary))

# 1. Check Element Counts
print("\n--- Count by Element ---")
print(df['Element'].value_counts())

# 2. Check for Suspicious Data
print("\n--- Potential Issues ---")
print(df[df['Flags'] != "OK"])

# 3. Check for "Header Bleed" (Common scraper error)
# If we see "ROLE" or "DPS" as a name, the logic is off.
bad_names = [d for d in data if d['name'] in ["ROLE", "WEAPON", "DPS", "4 STAR", "5 STAR"]]
if bad_names:
    print(f"\n⚠️ FOUND JUNK DATA AS NAMES: {[x['name'] for x in bad_names]}")
else:
    print("\n✅ No Header rows mistaken for Character Names.")