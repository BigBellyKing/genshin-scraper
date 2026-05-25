import json
import os

# --- CONFIGURATION ---
SOURCE_FOLDER = "genshin_json_output"
OUTPUT_FILE = "artifact_db.py"

# --- MAIN EXECUTION ---
unique_raw_entries = set()

print(f"Scanning {SOURCE_FOLDER} for raw artifact strings...")

if os.path.exists(SOURCE_FOLDER):
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith(".json"):
            with open(os.path.join(SOURCE_FOLDER, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for char in data:
                    for build in char['builds']:
                        # We grab the raw list of artifacts from the scraper
                        raw_list = build.get('artifacts', [])
                        
                        for raw_line in raw_list:
                            # Add to set to ensure uniqueness
                            # We strip whitespace but keep everything else (numbers, stars, etc.)
                            clean_entry = raw_line.strip()
                            if clean_entry:
                                unique_raw_entries.add(clean_entry)

# Sort them alphabetically so it's easy to read
sorted_entries = sorted(list(unique_raw_entries))

print(f"Found {len(sorted_entries)} unique raw strings.")
print(f"Generating {OUTPUT_FILE}...")

# Write the Python Dictionary file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("# ARTIFACT MAPPING DICTIONARY\n")
    f.write("# INSTRUCTIONS:\n")
    f.write("# 1. On the RIGHT side, write the clean ID you want for your CSV (e.g., 'NoblesseOblige').\n")
    f.write("# 2. If a line is junk/notes (not an artifact), DELETE the entire line.\n")
    f.write("# 3. If a line has multiple sets (e.g. 'Set A + Set B'), map it to the one you want, or a custom code.\n")
    f.write("\n")
    f.write("ARTIFACT_MAP = {\n")
    
    for entry in sorted_entries:
        # We escape double quotes just in case, though rare in these files
        safe_key = entry.replace('"', '\\"')
        
        # We write: "Raw String": "",
        f.write(f'    "{safe_key}": "",\n')
        
    f.write("}\n")

print("Done. Open 'artifact_db.py' and start filling in the blanks!")