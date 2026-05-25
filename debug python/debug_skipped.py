import json
import re
import os

# --- CONFIGURATION ---
SOURCE_FOLDER = "genshin_json_output"

# The exact keywords you are using to filter out junk
SKIP_KEYWORDS = ['other', 'any', 'dps', 'conditional', 'see notes']

def get_skipped_items():
    skipped_log = []
    
    # 1. Loop through all files
    if not os.path.exists(SOURCE_FOLDER):
        print(f"❌ Error: Folder '{SOURCE_FOLDER}' not found.")
        return

    for filename in os.listdir(SOURCE_FOLDER):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(SOURCE_FOLDER, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                continue

            for char in data:
                for build in char.get('builds', []):
                    for art_line in build.get('artifacts', []):
                        
                        # --- REPLICATE THE CLEANING LOGIC ---
                        entry = art_line.strip()
                        entry = entry.replace("Aubade of Morningstar and Moon", "Aubade of Morningstar & Moon")
                        entry = re.sub(r'\[.*?\]', '', entry)
                        entry = re.sub(r'\(see notes\)', '', entry, flags=re.IGNORECASE)
                        
                        # --- REPLICATE THE SPLITTING LOGIC ---
                        if '/' in entry:
                            parts = entry.split('/')
                        elif ' and ' in entry.lower():
                            parts = re.split(r'\s+and\s+', entry, flags=re.IGNORECASE)
                        elif '+' in entry:
                            parts = entry.split('+')
                        else:
                            parts = re.split(r'\)\s+(?=[A-Z0-9])', entry)

                        # --- ANALYZE EACH PART ---
                        for part in parts:
                            part = part.strip()
                            if not part: continue

                            # Try to find the name using the (4) or (2) regex
                            match = re.search(r'(.+?)\s*\(([24])\)', part)
                            
                            if match:
                                set_name = match.group(1).strip()
                                set_name = set_name.lstrip('+').strip()
                                lower_name = set_name.lower()

                                # CHECK AGAINST BAD KEYWORDS
                                for k in SKIP_KEYWORDS:
                                    if k in lower_name:
                                        # Record the collision
                                        skipped_log.append({
                                            "blocked_word": set_name,
                                            "trigger_keyword": k,
                                            "full_source_line": art_line
                                        })
                                        # We break here because we found a reason to skip it
                                        break
    return skipped_log

# --- RUN AND REPORT ---
print(f"🔎 Scanning for artifacts blocked by keywords: {SKIP_KEYWORDS}...\n")

collisions = get_skipped_items()

# Group by the unique name so we don't see duplicates
unique_collisions = {}
for item in collisions:
    key = item['blocked_word']
    if key not in unique_collisions:
        unique_collisions[key] = item

if not unique_collisions:
    print("✅ No items were blocked. Your keywords might be too safe (or data is clean).")
else:
    print(f"⚠️  FOUND {len(unique_collisions)} UNIQUE BLOCKED ITEMS ⚠️")
    print("="*60)
    print(f"{'BLOCKED STRING':<30} | {'TRIGGER':<10} | {'STATUS'}")
    print("-" * 60)
    
    for name, info in unique_collisions.items():
        trigger = info['trigger_keyword']
        
        # Simple visual check for the user
        status = "✅ JUNK (Correct)"
        
        # Highlight known false positives
        if "thundersoother" in name.lower():
            status = "❌ FALSE POSITIVE (Fix required)"
        
        print(f"{name:<30} | {trigger:<10} | {status}")

    print("="*60)
    print("\nIf you see any REAL artifact sets in the list above marked as 'FALSE POSITIVE',")
    print("you need to add an exception for them in 'transform.py'.")