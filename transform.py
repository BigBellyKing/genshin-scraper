import json
import csv
import re
import os

# --- 1. CONFIGURATION ---

SOURCE_FOLDER = "genshin_json_output"
OUTPUT_FILE = "artifacts_usage_filtered.csv"
WHITELIST_FILE = "whitelist.txt"

# RAW Mapping: Source Name (Human Readable) -> Target Name (Whitelist/CSV Name)
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

# Convert keys to UPPERCASE for robust matching
CHAR_NAME_MAPPING = {k.upper(): v for k, v in CHAR_NAME_MAPPING_RAW.items()}

# Mapping human text to the specific codes used in your target CSV
STAT_MAP = {
    # Basic Stats
    "ATK%": "atk_", "HP%": "hp_", "DEF%": "def_",
    "Energy Recharge": "enerRech_", "Elemental Mastery": "eleMas", 
    "Crit Rate": "critRate_", "Crit DMG": "critDMG_", "Healing Bonus": "heal_",
    # Elemental DMG
    "Anemo DMG": "anemo_dmg_", "Geo DMG": "geo_dmg_",
    "Electro DMG": "electro_dmg_", "Dendro DMG": "dendro_dmg_",
    "Hydro DMG": "hydro_dmg_", "Pyro DMG": "pyro_dmg_",
    "Cryo DMG": "cryo_dmg_", "Physical DMG": "physical_dmg_",
}

# Priority list for backfilling substats if count < 4
SUBSTAT_BACKFILL_PRIORITY = ["critRate_", "critDMG_", "enerRech_", "atk_", "eleMas"]

# The dictionary from dict.txt
ARTIFACT_MAP = {
    "15% Anemo DMG set": "DesertPavilionChronicle, ViridescentVenerer",
    "15% Hydro DMG Bonus set": "HeartOfDepth, NymphsDream",
    "15% Hydro DMG set": "HeartOfDepth, NymphsDream",
    "18% ATK set": "ADayCarvedFromRisingWinds, FragmentOfHarmonicWhimsy, NighttimeWhispersInTheEchoingWoods, EchoesOfAnOffering, GladiatorsFinale, ShimenawasReminiscence, VermillionHereafter, UnfinishedReverie, DisenchantmentInDeepShadow",
    "20% ER Set": "SilkenMoonsSerenade, EmblemOfSeveredFate, CelestialGift",
    "20% ER set": "SilkenMoonsSerenade, EmblemOfSeveredFate, CelestialGift", # FIXED MISSING SPACE
    "20% Energy Recharge set": "SilkenMoonsSerenade, EmblemOfSeveredFate, CelestialGift",
    "80 EM set": "FlowerOfParadiseLost, GildedDreams, NightOfTheSkysUnveiling, AubadeOfMorningstarAndMoon, WanderersTroupe",
    "15% Cryo DMG set": "BlizzardStrayer, FinaleOfTheDeepGalleries",
    "15% Healing Bonus set": "MaidenBeloved, OceanHuedClam, SongOfDaysPast",
    "15% Hydro DMG set": "HeartOfDepth, NymphsDream",
    "20% HP set": "TenacityOfTheMillelith, VourukashasGlow",
    "25% Physical DMG set": "BloodstainedChivalry, PaleFlame",
    "80 EM": "FlowerOfParadiseLost, GildedDreams, NightOfTheSkysUnveiling, AubadeOfMorningstarAndMoon, WanderersTroupe",
    "A Day Carved From Rising Winds": "ADayCarvedFromRisingWinds",
    "Archaic Petra": "ArchaicPetra",
    "Aubade of Morningstar and Moon": "AubadeOfMorningstarAndMoon",
    "Blizzard Strayer": "BlizzardStrayer",
    "Bloodstained Chivalry": "BloodstainedChivalry",
    "Crimson Witch of Flames": "CrimsonWitchOfFlames",
    "Deepwood Memories": "DeepwoodMemories",
    "Desert Pavilion Chronicle": "DesertPavilionChronicle",
    "Desert Pavillion Chronicle": "DesertPavilionChronicle",
    "Echoes of an Offering": "EchoesOfAnOffering",
    "Emblem of Severed Fate": "EmblemOfSeveredFate",
    "Finale of the Deep Galleries": "FinaleOfTheDeepGalleries",
    "Flower of Paradise Lost": "FlowerOfParadiseLost",
    "Fragment of Harmonic Whimsy": "FragmentOfHarmonicWhimsy",
    "Gilded Dreams": "GildedDreams",
    "Gladiator's Finale": "GladiatorsFinale",
    "Golden Troupe": "GoldenTroupe",
    "Heart of Depth": "HeartOfDepth",
    "Husk of Opulent Dreams": "HuskOfOpulentDreams",
    "Instructor": "Instructor",
    "Lavawalker": "Lavawalker",
    "Long Night's Oath": "LongNightsOath",
    "Maiden Beloved": "MaidenBeloved",
    "Marechaussee Hunter": "MarechausseeHunter",
    "Night of the Sky's Unveiling": "NightOfTheSkysUnveiling",
    "Nighttime Whispers in the Echoing Woods": "NighttimeWhispersInTheEchoingWoods",
    "Noblesse Oblige": "NoblesseOblige",
    "Nymph's Dream": "NymphsDream",
    "Obsidian Codex": "ObsidianCodex",
    "Ocean Hued Clam": "OceanHuedClam",
    "Ocean-Hued Clam": "OceanHuedClam",
    "Pale Flame": "PaleFlame",
    "Retracing Bolide": "RetracingBolide",
    "Scroll of the Hero of Cinder City": "ScrollOfTheHeroOfCinderCity",
    "Shimenawa's Reminiscence": "ShimenawasReminiscence",
    "Silken Moon Serenade": "SilkenMoonsSerenade",
    "Silken Moon's Serenade": "SilkenMoonsSerenade",
    "Song of Days Past": "SongOfDaysPast",
    "Tenacity of the Millelith": "TenacityOfTheMillelith",
    "The Exile": "TheExile",
    "Thundering Fury": "ThunderingFury",
    "Thundersoother": "Thundersoother",
    "Unfinished Reverie": "UnfinishedReverie",
    "Vermillion Hereafter": "VermillionHereafter",
    "Viridescent Venerer": "ViridescentVenerer",
    "Vourukasha's Glow": "VourukashasGlow",
    "Wanderer's Troupe": "WanderersTroupe",
    "Husk of Opulent Dreams (2": "HuskOfOpulentDreams",
    "Noblesse Oblige (2": "NoblesseOblige",
    "Pale Flame (2": "PaleFlame",
    "A Day Carved from Rising Winds": "ADayCarvedFromRisingWinds",  # Used by: Razor, Varka
    "Celestial Gift": "CelestialGift",  # Used by: Durin, Prune
}

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

def clean_artifact_name(name):
    # Translate mojibake to standard symbol
    name = name.replace('â‰ˆ', '≈')
    
    # Strip leading numbers, symbols, and bullets
    name = re.sub(r'^\d+\.\s*', '', name)
    name = re.sub(r'^[≈+]\s*', '', name)
    
    # Strip inline symbols that break mappings
    name = name.replace('≈', '')
    name = name.replace('*', '')
    return name.strip()

def extract_artifact_sets(entry):
    sets = []
    entry = entry.replace("Aubade of Morningstar and Moon", "Aubade of Morningstar & Moon")
    entry = re.sub(r'\[.*?\]', '', entry)
    entry = re.sub(r'\(see notes\)', '', entry, flags=re.IGNORECASE)
    entry = re.sub(r'\(.*?only.*?\)', '', entry, flags=re.IGNORECASE)
    
    if '/' in entry:
        parts = entry.split('/')
    elif ' and ' in entry.lower():
        parts = re.split(r'\s+and\s+', entry, flags=re.IGNORECASE)
    elif '+' in entry:
        parts = entry.split('+')
    else:
        parts = re.split(r'\)\s+(?=[A-Z0-9])', entry)
    
    for part in parts:
        part = part.strip()
        if not part or 'choose' in part.lower():
            continue
        
        match = re.search(r'(.+?)\s*\(([24])\)', part)
        if not match:
             clean_part = part.strip().lstrip('+').strip()
             if clean_part in ARTIFACT_MAP:
                 sets.append(clean_part)
                 continue

        if match:
            set_name = match.group(1).strip()
            set_name = set_name.lstrip('+').strip()
            if "Aubade of Morningstar & Moon" in set_name:
                set_name = set_name.replace("&", "and")
            
            skip_keywords = ['other', 'any', 'dps', 'conditional', 'see notes']
            should_skip = False
            lower_name = set_name.lower()
            
            for k in skip_keywords:
                if k in lower_name:
                    # Exception: If the set is Thundersoother, ignore the "other" trigger
                    if k == 'other' and 'thundersoother' in lower_name:
                        continue
                    should_skip = True
                    break
            
            if should_skip: continue
            
            sets.append(set_name)
    return sets

def resolve_to_internal_code(raw_string, char_name):
    cleaned = clean_artifact_name(raw_string)
    extracted_sets = extract_artifact_sets(cleaned)
    final_codes = []
    
    for s in extracted_sets:
        if s in ARTIFACT_MAP:
            final_codes.append(ARTIFACT_MAP[s])
        else:
            # Fallback logic: removing spaces/symbols
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
# ADDED Raw Artifact String to CSV headers
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
                    
                    # 1. Determine Identity
                    if name_upper == "TRAVELER":
                        lookup_name = "MC"
                        display_name = f"MC ({element_name})"
                    elif name_upper in CHAR_NAME_MAPPING:
                        lookup_name = CHAR_NAME_MAPPING[name_upper]
                        display_name = lookup_name
                    else:
                        lookup_name = raw_name.title()
                        display_name = lookup_name

                    # 2. Check Whitelist
                    if whitelist and lookup_name not in whitelist:
                        continue 

                    # 3. Process Builds
                    for build in char['builds']:
                        is_starred = "✩" in build['role']
                        limit = 2 if is_starred else 1
                        
                        final_artifacts_list = []
                        seen_artifacts = set()
                        raw_captured = [] # ADDED list to store raw lines
                        
                        # We track how many 'standard' lines we have processed.
                        processed_standard_lines = 0
                        capture_mode = False # Becomes True once we hit "Conditional"

                        raw_artifacts = build.get('artifacts', [])
                        
                        for art_line in raw_artifacts:
                            clean_line = art_line.strip()
                            lower_line = clean_line.lower()

                            # A. Check for Conditional Header
                            if "conditional" in lower_line and "notes" in lower_line:
                                capture_mode = True
                                continue # Skip the header itself
                            
                            # B. Filter out "Edge Case" notes (URLs, calculations)
                            skip_keywords = ["calculation", "http", "found here", "spreadsheet", "click here"]
                            if any(k in lower_line for k in skip_keywords):
                                continue

                            # C. Determine if we should process this line
                            should_process = False

                            if capture_mode:
                                # In Conditional Mode: We take EVERYTHING (that isn't a note)
                                should_process = True
                            else:
                                # In Standard Mode: We only take up to 'limit'
                                if processed_standard_lines < limit:
                                    should_process = True

                            if should_process:
                                # UPDATED to pass display_name
                                code_string = resolve_to_internal_code(clean_line, display_name)
                                
                                # Only add if it actually resolved to something (filters out empty lines or pure text)
                                if code_string:
                                    raw_captured.append(clean_line) # Track raw string for CSV
                                    
                                    # Split in case resolve returned multiple sets "SetA, SetB"
                                    individual_sets = [x.strip() for x in code_string.split(',')]
                                    
                                    sets_added_from_line = False
                                    for ind_set in individual_sets:
                                        if ind_set and ind_set not in seen_artifacts:
                                            final_artifacts_list.append(ind_set)
                                            seen_artifacts.add(ind_set)
                                            sets_added_from_line = True
                                    
                                    # Increment standard count only if we weren't in capture mode
                                    if not capture_mode and sets_added_from_line:
                                        processed_standard_lines += 1

                        artifacts_str = ", ".join(final_artifacts_list)
                        raw_artifacts_str = " | ".join(raw_captured) # Join raw strings with pipe for CSV

                        # Main Stat Processing
                        sands, goblet, circlet = [], [], []
                        for line in build['stats']['main']:
                            # Get list, join immediately for main stats
                            codes_list = extract_stat_codes([line])
                            codes_str = ", ".join(codes_list)
                            
                            lower = line.lower()
                            if "sands" in lower: sands.append(codes_str)
                            elif "goblet" in lower: goblet.append(codes_str)
                            elif "circlet" in lower: circlet.append(codes_str)

                        # Substat Processing with BACKFILL
                        substats_list = extract_stat_codes(build['stats']['sub'])
                        
                        if len(substats_list) < 4:
                            for fill_stat in SUBSTAT_BACKFILL_PRIORITY:
                                if fill_stat not in substats_list:
                                    substats_list.append(fill_stat)
                                    if len(substats_list) >= 4:
                                        break
                        
                        substats_str = ", ".join(substats_list)

                        # Clean role name (replace newlines with space, strip stars, remove double spaces)
                        clean_role = build['role'].replace('✩', '').replace('\n', ' ').strip()
                        clean_role = " ".join(clean_role.split()) 
                        
                        # Create character_role format
                        character_with_role = f"{display_name}_{clean_role}"

                        row = [
                            character_with_role,
                            raw_artifacts_str, # ADDED to CSV row
                            artifacts_str,
                            ", ".join(sands),
                            ", ".join(goblet),
                            ", ".join(circlet),
                            substats_str
                        ]
                        all_rows.append(row)

# --- 4. WRITE CSV ---

with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(csv_headers)
    writer.writerows(all_rows)

print(f"✅ Generated {OUTPUT_FILE} with {len(all_rows)} rows (Standard + Conditionals merged).")