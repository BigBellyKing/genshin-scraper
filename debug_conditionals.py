import json
import os
import csv

# --- 1. CONFIGURATION ---

SOURCE_FOLDER = "genshin_json_output"
OUTPUT_FILE = "artifact_conditions_fixed.csv"

# Same mapping as your main script
CHAR_NAME_MAPPING_RAW = {
    "Kamisato Ayaka": "Ayaka",
    "Shikanoin Heizou": "Heizou",
    "Sangonomiya Kokomi": "Kokomi",
    "Kuki Shinobu": "Kuki",
    "Lan Yan": "Lanyan",
    "Yumemizuki Mizuki": "Mizuki",
    "Raiden Shogun": "Raiden",
    "Kujou Sara": "Sara",
    "Yae Miko": "Yaemiko",
    "Yun Jin": "Yunjin",
    "Hu Tao": "Hutao",
    "Kaedehara Kazuha": "Kazuha",
    "Arataki Itto": "Itto"
}
CHAR_NAME_MAPPING = {k.upper(): v for k, v in CHAR_NAME_MAPPING_RAW.items()}

# --- 2. PROCESSING ---

extracted_rows = []
csv_headers = ["Character", "Build Role", "Conditional Sets"]

print(f"🔍 Scanning JSONs in {SOURCE_FOLDER}...")

if os.path.exists(SOURCE_FOLDER):
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith(".json"):
            element_name = filename.rsplit('.', 1)[0].capitalize()

            with open(os.path.join(SOURCE_FOLDER, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)

                for char in data:
                    raw_name = char['name'].strip()
                    name_upper = raw_name.upper()

                    # 1. Normalize Name
                    if name_upper == "TRAVELER":
                        display_name = f"MC ({element_name})"
                    elif name_upper in CHAR_NAME_MAPPING:
                        display_name = CHAR_NAME_MAPPING[name_upper]
                    else:
                        display_name = raw_name.title()

                    # 2. Iterate Builds
                    for build in char['builds']:
                        role = build['role'].replace("\n", " ").strip()
                        artifacts_list = build.get('artifacts', [])
                        
                        captured_lines = []
                        capture_mode = False
                        
                        # 3. State-based extraction
                        for line in artifacts_list:
                            clean_line = line.strip()
                            
                            # Check if this line is the "Header"
                            # We look for "Conditional" AND "Notes" to be safe
                            if "conditional" in clean_line.lower() and "notes" in clean_line.lower():
                                capture_mode = True
                                continue # Skip the line that says "Conditional (See Notes):"
                            
                            # If we passed the header, capture everything else
                            if capture_mode:
                                # Optional: Stop capturing if we hit a standard ranked line (starts with digit)
                                # Uncomment the next two lines if you want to stop at the next numbered list
                                # if clean_line[0].isdigit(): 
                                #    capture_mode = False; continue

                                captured_lines.append(clean_line)

                        # 4. If we found data, save it
                        if captured_lines:
                            # Join multiple lines with a pipe symbol | for CSV readability
                            full_text = " | ".join(captured_lines)
                            extracted_rows.append([display_name, role, full_text])

# --- 3. WRITE CSV ---

with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(csv_headers)
    writer.writerows(extracted_rows)

print(f"✅ Extracted {len(extracted_rows)} conditional entries to {OUTPUT_FILE}.")