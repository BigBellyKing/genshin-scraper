import pandas as pd
import io
import requests
import json
import os

# --- CONFIGURATION ---
SHEET_ID = "1gNxZ2xab1J6o1TuNVWMeLOZ7TPOqrsf3SshP5DLvKzI"
OUTPUT_FOLDER = "genshin_json_output"

TABS = {
    "Anemo": "653464458", 
    "Geo": "1780570478",
    "Pyro": "954718212",
    "Hydro": "1354385732",
    "Electro": "408609723",
    "Dendro": "1468017260",
    "Cryo": "1169063456"
}

# --- CHANGE DETECTION FUNCTIONS ---

def normalize_data(data_list):
    """Converts a list of character dicts into a dictionary keyed by name for easy comparison."""
    return {char['name']: char for char in data_list}

def detect_changes(old_data, new_data, element_name):
    """Compares two datasets and prints a report of differences."""
    old_map = normalize_data(old_data)
    new_map = normalize_data(new_data)
    
    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())
    
    added = new_keys - old_keys
    removed = old_keys - new_keys
    common = old_keys & new_keys
    
    changes_found = False
    
    print(f"\n--- 📝 Change Report for {element_name} ---")

    # 1. New Characters
    if added:
        changes_found = True
        for name in added:
            print(f"🟢 [NEW CHAR] Added: {name}")

    # 2. Removed Characters
    if removed:
        changes_found = True
        for name in removed:
            print(f"🔴 [REMOVED] Deleted: {name}")

    # 3. Modified Characters
    for name in common:
        old_char = old_map[name]
        new_char = new_map[name]
        
        # We compare the JSON string representations to catch deep differences easily
        # Sorting keys ensures order doesn't trigger a false positive
        if json.dumps(old_char, sort_keys=True) != json.dumps(new_char, sort_keys=True):
            changes_found = True
            diff_details = []
            
            # Check specifically what changed inside the builds
            # Note: This compares the first build vs first build. 
            # If a char has multiple builds, this simple check might need expansion, 
            # but it covers 90% of cases.
            old_b = old_char.get('builds', [])
            new_b = new_char.get('builds', [])
            
            if len(old_b) != len(new_b):
                diff_details.append("Build count changed")
            else:
                for i in range(len(new_b)):
                    # Check Weapons
                    if old_b[i].get('weapons') != new_b[i].get('weapons'):
                        diff_details.append(f"Weapons (Build {i+1})")
                    # Check Artifacts
                    if old_b[i].get('artifacts') != new_b[i].get('artifacts'):
                        diff_details.append(f"Artifacts (Build {i+1})")
                    # Check Stats
                    if old_b[i].get('stats') != new_b[i].get('stats'):
                        diff_details.append(f"Stats (Build {i+1})")
                    # Check Tips
                    if old_b[i].get('tips') != new_b[i].get('tips'):
                        diff_details.append(f"Tips (Build {i+1})")

            # Fallback if we detected a change but the specific logic above missed it
            if not diff_details:
                diff_details.append("Metadata/Other")

            print(f"🟡 [UPDATED]  {name}: {', '.join(diff_details)}")

    if not changes_found:
        print("✨ No changes detected.")
    
    print("-" * 40)

# --- SCRAPING LOGIC ---

def scrape_genshin_sheet(element_name, gid):
    print(f"Fetching {element_name} (GID: {gid})...")
    
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    
    response = requests.get(url)
    response.raise_for_status()
    
    df = pd.read_csv(io.BytesIO(response.content), encoding='utf-8', header=None)
    
    df = df.iloc[:, 1:9] 
    df.columns = ["Character_Trigger", "Role", "Weapon", "Artifact", "Main_Stats", "Sub_Stats", "Talent", "Tips"]
    
    ignore_list = ["4 STAR", "5 STAR", "Weapons and Artifacts Info", "Image", "NOTES", "Last Updated", "Role", "ROLE"]
    
    df['Current_Character'] = None
    
    for index, row in df.iterrows():
        val_trigger = str(row['Character_Trigger']).strip()
        val_role = str(row['Role']).strip()
        
        if val_trigger != "nan" and (val_role == "nan" or val_role == ""):
            if not any(ignored in val_trigger for ignored in ignore_list):
                df.at[index, 'Current_Character'] = val_trigger
                
    df['Current_Character'] = df['Current_Character'].ffill()

    cols_to_inherit = ['Artifact', 'Main_Stats', 'Sub_Stats', 'Talent', 'Tips']
    df[cols_to_inherit] = df.groupby('Current_Character')[cols_to_inherit].ffill()

    def is_valid_role(role_text):
        text = str(role_text).strip()
        if len(text) > 80: return False 
        if "Regarding" in text: return False
        if "NOTES" in text: return False
        return True

    data_rows = df[
        (df['Role'].notna()) & 
        (df['Role'] != "ROLE") & 
        (df['Current_Character'].notna()) & 
        (df['Character_Trigger'] != "NOTES") & 
        (~df['Role'].str.contains("Last Updated", na=False)) &
        (df['Role'].apply(is_valid_role))
    ]
    
    results = []
    
    for char_name, group in data_rows.groupby("Current_Character", sort=False):
        char_data = {
            "name": char_name,
            "element": element_name,
            "builds": []
        }
        
        for _, row in group.iterrows():
            def clean_list(text):
                if pd.isna(text): return []
                cleaned_text = str(text).replace('\r', '')
                return [x.strip() for x in cleaned_text.split('\n') if x.strip()]

            build = {
                "role": row['Role'],
                "weapons": clean_list(row['Weapon']),
                "artifacts": clean_list(row['Artifact']),
                "stats": {
                    "main": clean_list(row['Main_Stats']),
                    "sub": clean_list(row['Sub_Stats'])
                },
                "talent_priority": clean_list(row['Talent']),
                "tips": row['Tips'] if pd.notna(row['Tips']) else ""
            }
            char_data["builds"].append(build)
        
        results.append(char_data)
        
    return results

# --- MAIN EXECUTION ---

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print(f"Outputting files to folder: ./{OUTPUT_FOLDER}/")

for element, gid in TABS.items():
    try:
        # 1. Scrape New Data
        new_data = scrape_genshin_sheet(element, gid)
        
        filename = f"{OUTPUT_FOLDER}/{element}.json"
        
        # 2. Load Old Data (if it exists)
        old_data = []
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
            except Exception as e:
                print(f"⚠️ Could not load existing file for diff: {e}")

        # 3. Detect Changes
        if old_data:
            detect_changes(old_data, new_data, element)
        else:
            print(f"ℹ️ First run for {element} (no history to compare).")

        # 4. Save New Data
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Saved {filename} ({len(new_data)} characters)\n")
        
    except Exception as e:
        print(f"❌ Error scraping {element}: {e}")

print("All done.")