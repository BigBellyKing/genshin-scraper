import csv

# 1. DEFINING THE VALID DICTIONARY
# (Derived from your dict.txt - we extract the VALUES as the valid codes)
ARTIFACT_MAP = {
    "15% Anemo DMG set": "DesertPavilionChronicle,ViridescentVenerer",
    "15% Hydro DMG Bonus set": "HeartOfDepth,NymphsDream",
    "15% Hydro DMG set": "HeartOfDepth,NymphsDream",
    "18% ATK set": "ADayCarvedFromRisingWinds,FragmentOfHarmonicWhimsy,NighttimeWhispersInTheEchoingWoods,EchoesOfAnOffering,GladiatorsFinale,ShimenawasReminiscence,VermillionHereafter,UnfinishedReverie",
    "20% ER Set": "SilkenMoonsSerenade,EmblemOfSeveredFate",
    "20% ER set": "SilkenMoonsSerenade,EmblemOfSeveredFate",
    "20% Energy Recharge set": "SilkenMoonsSerenade,EmblemOfSeveredFate",
    "20% HP set": "TenacityOfTheMillelith,VourukashasGlow",
    "25% Physical DMG set": "BloodstainedChivalry,PaleFlame",
    "80 EM": "FlowerOfParadiseLost,GildedDreams,NightOfTheSkysUnveiling,AubadeOfMorningstarAndMoon,WanderersTroupe",
    "80 EM set": "FlowerOfParadiseLost,GildedDreams,NightOfTheSkysUnveiling,AubadeOfMorningstarAndMoon,WanderersTroupe",
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
    "Unfinished Reverie": "UnfinishedReverie",
    "Vermillion Hereafter": "VermillionHereafter",
    "Viridescent Venerer": "ViridescentVenerer",
    "Vourukasha's Glow": "VourukashasGlow",
    "Wanderer's Troupe": "WanderersTroupe",
}

# 2. CONFIGURATION
csv_file = 'artifacts_usage_starred_cleaned.csv'
target_column = 'Top Artifact Sets'

def validate_csv_artifacts():
    # A. Build the master set of valid artifact CODES from the dictionary values
    valid_codes = set()
    for val_str in ARTIFACT_MAP.values():
        # Split by comma in case the dict value is "SetA,SetB"
        parts = val_str.split(',')
        for p in parts:
            valid_codes.add(p.strip())

    mismatches = set()
    rows_with_errors = []

    try:
        # B. Read the CSV
        with open(csv_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if target_column not in reader.fieldnames:
                print(f"Error: Column '{target_column}' not found.")
                return

            for line_num, row in enumerate(reader, start=2): # start=2 accounts for header
                cell_content = row[target_column]
                if not cell_content:
                    continue

                # C. Split the cell content (e.g., "ViridescentVenerer, Instructor")
                artifacts_in_cell = [x.strip() for x in cell_content.split(',')]
                
                for art in artifacts_in_cell:
                    # Ignore empty strings that might result from trailing commas
                    if art and art not in valid_codes:
                        mismatches.add(art)
                        rows_with_errors.append((line_num, row['Character Name'], art))

        # D. Report Results
        print("-" * 50)
        print("MISMATCH REPORT")
        print("-" * 50)
        
        if not mismatches:
            print("All artifacts in the CSV match the Dictionary!")
        else:
            print(f"Found {len(mismatches)} unique undefined strings:\n")
            for m in mismatches:
                print(f"• {m}")
            
            print("\n" + "-" * 50)
            print("DETAILED LOCATIONS")
            print("-" * 50)
            for line, char, bad_str in rows_with_errors:
                print(f"Row {line} | {char}: '{bad_str}'")

    except FileNotFoundError:
        print(f"Error: Could not find file '{csv_file}'")

if __name__ == "__main__":
    validate_csv_artifacts()