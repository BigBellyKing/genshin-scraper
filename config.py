import re
import os

# --- FILE PATHS ---
WHITELIST_FILE = "whitelist.txt"

# --- CHARACTER MAPPING ---
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

# --- STAT MAPPING ---
STAT_MAP = {
    "ATK%": "atk_", "HP%": "hp_", "DEF%": "def_",
    "Energy Recharge": "enerRech_", "Elemental Mastery": "eleMas", 
    "Crit Rate": "critRate_", "Crit DMG": "critDMG_", "Healing Bonus": "heal_",
    "Anemo DMG": "anemo_dmg_", "Geo DMG": "geo_dmg_",
    "Electro DMG": "electro_dmg_", "Dendro DMG": "dendro_dmg_",
    "Hydro DMG": "hydro_dmg_", "Pyro DMG": "pyro_dmg_",
    "Cryo DMG": "cryo_dmg_", "Physical DMG": "physical_dmg_",
}

SUBSTAT_BACKFILL_PRIORITY = ["critRate_", "critDMG_", "enerRech_", "atk_", "eleMas"]

# --- ARTIFACT MAPPING ---
ARTIFACT_MAP = {
    "15% Anemo DMG set": "DesertPavilionChronicle, ViridescentVenerer",
    "15% Hydro DMG Bonus set": "HeartOfDepth, NymphsDream",
    "15% Hydro DMG set": "HeartOfDepth, NymphsDream",
    "18% ATK set": "ADayCarvedFromRisingWinds, FragmentOfHarmonicWhimsy, NighttimeWhispersInTheEchoingWoods, EchoesOfAnOffering, GladiatorsFinale, ShimenawasReminiscence, VermillionHereafter, UnfinishedReverie, DisenchantmentInDeepShadow",
    "20% ER Set": "SilkenMoonsSerenade, EmblemOfSeveredFate, CelestialGift",
    "20% ER set": "SilkenMoonsSerenade, EmblemOfSeveredFate, CelestialGift",
    "20% Energy Recharge set": "SilkenMoonsSerenade, EmblemOfSeveredFate, CelestialGift",
    "80 EM set": "FlowerOfParadiseLost, GildedDreams, NightOfTheSkysUnveiling, AubadeOfMorningstarAndMoon, WanderersTroupe",
    "15% Cryo DMG set": "BlizzardStrayer, FinaleOfTheDeepGalleries",
    "15% Healing Bonus set": "MaidenBeloved, OceanHuedClam, SongOfDaysPast",
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
    "A Day Carved from Rising Winds": "ADayCarvedFromRisingWinds",
    "Celestial Gift": "CelestialGift",
}

# --- REGEX & CLEANING LOGIC ---
def clean_artifact_name(name):
    name = name.replace('â‰ˆ', '≈')
    name = re.sub(r'^\d+\.\s*', '', name)
    name = re.sub(r'^[≈+]\s*', '', name)
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
                    if k == 'other' and 'thundersoother' in lower_name:
                        continue
                    should_skip = True
                    break
            
            if should_skip: continue
            sets.append(set_name)
    return sets