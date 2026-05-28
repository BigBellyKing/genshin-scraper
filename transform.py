import json
import csv
import re
import os
from datetime import datetime


# --- 1. IMPORT CENTRAL CONFIGURATION ---
from config import (
    CHAR_NAME_MAPPING, STAT_MAP, SUBSTAT_BACKFILL_PRIORITY, 
    ARTIFACT_MAP, WHITELIST_FILE, clean_artifact_name, extract_artifact_sets
)

SOURCE_FOLDER = "genshin_json_output"
OUTPUT_FILE = "artifacts_usage_filtered.csv"

# --- 2. HELPER FUNCTIONS ---
def load_whitelist():
    """Loads the whitelist text file into a set of names."""
    allowed = set()
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                name = line.strip()
                if name:
                    allowed.add(name)
        print(f"📋 Loaded {len(allowed)} characters from whitelist.")
    else:
        print(f"⚠️ Warning: {WHITELIST_FILE} not found. No filtering will occur.")
    return allowed

def resolve_to_internal_code(raw_string, char_name):
    cleaned = clean_artifact_name(raw_string)
    extracted_sets = extract_artifact_sets(cleaned)
    final_codes = []
    
    for s in extracted_sets:
        if s in ARTIFACT_MAP:
            final_codes.append(ARTIFACT_MAP[s])
        else:
            fallback = s.title().replace(" ", "").replace("'", "").replace("-", "").replace("+", "") 
            print(f"⚠️ [UNMAPPED ARTIFACT] Char: {char_name} | Raw: '{raw_string}' | Extracted: '{s}' | Guess: '{fallback}'")
            final_codes.append(fallback)
            
    return ", ".join(final_codes)

def extract_stat_codes(text_list):
    """Parses text list and returns a LIST of stat codes."""
    found_stats = []
    for line in text_list:
        if "rate" in line.lower() and "dmg" in line.lower() and "/" in line:
            line = re.sub(r'(Crit\s*Rate)\s*/\s*DMG', r'\1 / Crit DMG', line, flags=re.IGNORECASE)

        parts = line.split('/')
        for part in parts:
            part_clean = part.strip()
            for human_key, code_key in STAT_MAP.items():
                if human_key.lower() in part_clean.lower():
                    if code_key not in found_stats:
                        found_stats.append(code_key)
    return found_stats

# --- 3. MAIN PROCESSING ---
whitelist = load_whitelist()
all_rows = []
csv_headers = ["Character Name", "Raw Artifact String", "Top Artifact Sets", "Common Sands", "Common Goblet", "Common Circlet", "Substat Priority"]

print(f"Reading JSONs from {SOURCE_FOLDER}...")

if os.path.exists(SOURCE_FOLDER):
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith(".json"):
            element_name = filename.rsplit('.', 1)[0].capitalize()

            with open(os.path.join(SOURCE_FOLDER, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for char in data:
                    raw_name = char['name'].strip()
                    name_upper = raw_name.upper()
                    
                    if name_upper == "TRAVELER":
                        lookup_name = "MC"
                        display_name = f"MC ({element_name})"
                    elif name_upper in CHAR_NAME_MAPPING:
                        lookup_name = CHAR_NAME_MAPPING[name_upper]
                        display_name = lookup_name
                    else:
                        lookup_name = raw_name.title()
                        display_name = lookup_name

                    if whitelist and lookup_name not in whitelist:
                        continue 

                    for build in char['builds']:
                        is_starred = "✩" in build['role']
                        limit = 2 if is_starred else 1
                        
                        final_artifacts_list = []
                        seen_artifacts = set()
                        raw_captured = [] 
                        
                        processed_standard_lines = 0
                        capture_mode = False 

                        raw_artifacts = build.get('artifacts', [])
                        
                        for art_line in raw_artifacts:
                            clean_line = art_line.strip()
                            lower_line = clean_line.lower()

                            if "conditional" in lower_line and "notes" in lower_line:
                                capture_mode = True
                                continue 
                            
                            skip_keywords = ["calculation", "http", "found here", "spreadsheet", "click here"]
                            if any(k in lower_line for k in skip_keywords):
                                continue

                            should_process = False

                            if capture_mode:
                                should_process = True
                            else:
                                if processed_standard_lines < limit:
                                    should_process = True

                            if should_process:
                                code_string = resolve_to_internal_code(clean_line, display_name)
                                
                                if code_string:
                                    raw_captured.append(clean_line) 
                                    
                                    individual_sets = [x.strip() for x in code_string.split(',')]
                                    sets_added_from_line = False
                                    
                                    for ind_set in individual_sets:
                                        if ind_set and ind_set not in seen_artifacts:
                                            final_artifacts_list.append(ind_set)
                                            seen_artifacts.add(ind_set)
                                            sets_added_from_line = True
                                    
                                    if not capture_mode and sets_added_from_line:
                                        processed_standard_lines += 1

                        artifacts_str = ", ".join(final_artifacts_list)
                        raw_artifacts_str = " | ".join(raw_captured) 

                        sands, goblet, circlet = [], [], []
                        for line in build['stats']['main']:
                            codes_list = extract_stat_codes([line])
                            codes_str = ", ".join(codes_list)
                            
                            lower = line.lower()
                            if "sands" in lower: sands.append(codes_str)
                            elif "goblet" in lower: goblet.append(codes_str)
                            elif "circlet" in lower: circlet.append(codes_str)

                        substats_list = extract_stat_codes(build['stats']['sub'])
                        
                        if len(substats_list) < 4:
                            for fill_stat in SUBSTAT_BACKFILL_PRIORITY:
                                if fill_stat not in substats_list:
                                    substats_list.append(fill_stat)
                                    if len(substats_list) >= 4:
                                        break
                        
                        substats_str = ", ".join(substats_list)

                        clean_role = build['role'].replace('✩', '').replace('\n', ' ').strip()
                        clean_role = " ".join(clean_role.split()) 
                        
                        character_with_role = f"{display_name}_{clean_role}"

                        row = [
                            character_with_role,
                            raw_artifacts_str,
                            artifacts_str,
                            ", ".join(sands),
                            ", ".join(goblet),
                            ", ".join(circlet),
                            substats_str
                        ]
                        all_rows.append(row)

# --- 4. WRITE CSV & ARCHIVE HISTORY ---
ARCHIVE_FOLDER = "csv_archive"

# Ensure the archive folder exists
if not os.path.exists(ARCHIVE_FOLDER):
    os.makedirs(ARCHIVE_FOLDER)

# If an old CSV exists, move it to the archive with a timestamp
if os.path.exists(OUTPUT_FILE):
    # Get the timestamp of when we are archiving it
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archived_filename = os.path.join(ARCHIVE_FOLDER, f"artifacts_usage_{timestamp}.csv")
    
    os.rename(OUTPUT_FILE, archived_filename)
    print(f"💾 Archived previous meta to {archived_filename}")

# Write the new fresh CSV
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(csv_headers)
    writer.writerows(all_rows)

print(f"✅ Generated {OUTPUT_FILE} with {len(all_rows)} rows (Standard + Conditionals merged).")