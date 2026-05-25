import json
import re
import os

# --- 1. CONFIGURATION ---

SOURCE_FOLDER = "genshin_json_output"

# Mapping for consistent naming (Copied from transform.py)
CHAR_NAME_MAPPING_RAW = {
    "Kamisato Ayaka": "Ayaka", "Shikanoin Heizou": "Heizou", "Sangonomiya Kokomi": "Kokomi",
    "Kuki Shinobu": "Kuki", "Lan Yan": "Lanyan", "Yumemizuki Mizuki": "Mizuki",
    "Raiden Shogun": "Raiden", "Kujou Sara": "Sara", "Yae Miko": "Yaemiko",
    "Yun Jin": "Yunjin", "Hu Tao": "Hutao", "Kaedehara Kazuha": "Kazuha", "Arataki Itto": "Itto"
}
CHAR_NAME_MAPPING = {k.upper(): v for k, v in CHAR_NAME_MAPPING_RAW.items()}

# PASTE YOUR CURRENT ARTIFACT_MAP HERE
ARTIFACT_MAP = {
    "15% Anemo DMG set": "DesertPavilionChronicle, ViridescentVenerer",
    "15% Hydro DMG Bonus set": "HeartOfDepth, NymphsDream",
    "15% Hydro DMG set": "HeartOfDepth, NymphsDream",
    "18% ATK set": "ADayCarvedFromRisingWinds, FragmentOfHarmonicWhimsy, NighttimeWhispersInTheEchoingWoods, EchoesOfAnOffering, GladiatorsFinale, ShimenawasReminiscence, VermillionHereafter, UnfinishedReverie, DisenchantmentInDeepShadow",
    "20% ER Set": "SilkenMoonsSerenade, EmblemOfSeveredFate, CelestialGift",
    "20% ER set": "SilkenMoonsSerenade, EmblemOfSeveredFate,CelestialGift",
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

def clean_artifact_name(name):
    name = re.sub(r'^\d+\.\s*', '', name)
    name = re.sub(r'^[â‰ˆ≈+]\s*', '', name)
    name = name.replace('â‰ˆ', '').replace('≈', '')
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
             sets.append(clean_part)
             continue

        if match:
            set_name = match.group(1).strip()
            set_name = set_name.lstrip('+').strip()
            if "Aubade of Morningstar & Moon" in set_name:
                set_name = set_name.replace("&", "and")
            
            skip = ['other', 'any', 'dps', 'conditional', 'see notes']
            if any(s in set_name.lower() for s in skip): continue
            
            sets.append(set_name)
    return sets

# --- 3. MAIN PROCESSING ---

# Dictionary to store: { "Unmapped Artifact Name": set("Char1", "Char2") }
missing_map = {}

print(f"🔍 Scanning {SOURCE_FOLDER}...")

if os.path.exists(SOURCE_FOLDER):
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith(".json"):
            element_name = filename.rsplit('.', 1)[0].capitalize()

            with open(os.path.join(SOURCE_FOLDER, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for char in data:
                    raw_name = char['name'].strip()
                    name_upper = raw_name.upper()
                    
                    # Resolve Character Name (for readable output)
                    if name_upper == "TRAVELER":
                        display_name = f"MC ({element_name})"
                    elif name_upper in CHAR_NAME_MAPPING:
                        display_name = CHAR_NAME_MAPPING[name_upper]
                    else:
                        display_name = raw_name.title()

                    for build in char['builds']:
                        is_starred = "✩" in build['role']
                        limit = 2 if is_starred else 1
                        
                        # --- TRANSFORM.PY STATE LOGIC ---
                        processed_standard_lines = 0
                        capture_mode = False 

                        raw_artifacts = build.get('artifacts', [])
                        
                        for art_line in raw_artifacts:
                            clean_line = art_line.strip()
                            lower_line = clean_line.lower()

                            # 1. Header Check
                            if "conditional" in lower_line and "notes" in lower_line:
                                capture_mode = True
                                continue 
                            
                            # 2. Skip Keywords
                            skip_keywords = ["calculation", "http", "found here", "spreadsheet", "click here"]
                            if any(k in lower_line for k in skip_keywords):
                                continue

                            # 3. Determine Processing
                            should_process = False
                            if capture_mode:
                                should_process = True
                            else:
                                if processed_standard_lines < limit:
                                    should_process = True

                            if should_process:
                                cleaned_text = clean_artifact_name(clean_line)
                                potential_sets = extract_artifact_sets(cleaned_text)
                                
                                sets_added_from_line = False
                                for s in potential_sets:
                                    if not s: continue
                                    
                                    # --- CHECK MAP & TRACK CHARACTER ---
                                    if s not in ARTIFACT_MAP:
                                        if s not in missing_map:
                                            missing_map[s] = set()
                                        missing_map[s].add(display_name)
                                    # -----------------------------------

                                    sets_added_from_line = True
                                    
                                if not capture_mode and sets_added_from_line:
                                    processed_standard_lines += 1

# --- 4. OUTPUT REPORT ---

print("---------------------------------------------------")
if not missing_map:
    print("🎉 All artifacts are mapped! No action needed.")
else:
    print(f"⚠️  Found {len(missing_map)} UNMAPPED artifacts.")
    print("Copy the code block below into your dictionary.\n")
    print("---------------------------------------------------")
    
    sorted_artifacts = sorted(list(missing_map.keys()))
    
    for art in sorted_artifacts:
        users = ", ".join(sorted(missing_map[art]))
        # CamelCase Guess
        camel_guess = art.title().replace(" ", "").replace("'", "").replace("-", "").replace("+", "")
        
        # Python Dict Format with Comment
        print(f'    "{art}": "{camel_guess}",  # Used by: {users}')

    print("---------------------------------------------------")