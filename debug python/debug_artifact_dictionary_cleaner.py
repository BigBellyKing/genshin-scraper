import re

def clean_artifact_name(name):
    """
    Clean artifact set name.
    FIX: Now preserves internal '+' signs to use as delimiters.
    """
    # Remove leading numbers and dots (e.g., "1. ")
    name = re.sub(r'^\d+\.\s*', '', name)
    
    # Remove special characters ONLY from the start
    name = re.sub(r'^[â‰ˆ≈+]\s*', '', name)
    name = name.replace('â‰ˆ', '').replace('≈', '')
    
    # --- CHANGE: Do NOT remove all '+' signs globally. ---
    # We only remove asterisks globally.
    name = name.replace('*', '')
    
    return name.strip()


def extract_artifact_sets(entry):
    """
    Extract individual artifact sets.
    FIX: Recognizes numbers (like "15%") as the start of a new set.
    """
    sets = []
    
    # Protect specific names containing "and"
    entry = entry.replace("Aubade of Morningstar and Moon", "Aubade of Morningstar & Moon")

    # Remove bracket instructions and parenthetical notes
    entry = re.sub(r'\[.*?\]', '', entry)
    entry = re.sub(r'\(see notes\)', '', entry, flags=re.IGNORECASE)
    entry = re.sub(r'\(.*?only.*?\)', '', entry, flags=re.IGNORECASE)
    
    # Split by common delimiters
    # 1. Handle explicit slash
    if '/' in entry:
        parts = entry.split('/')
    
    # 2. Handle explicit "and" (ignoring case)
    elif ' and ' in entry.lower():
        parts = re.split(r'\s+and\s+', entry, flags=re.IGNORECASE)
    
    # 3. Handle "+" delimiter (This helps with "Set A + Set B")
    elif '+' in entry:
        parts = entry.split('+')
        
    # 4. Fallback: Split on closing parenthesis followed by Capital Letter OR Number
    else:
        # --- CHANGE: Added 0-9 to the lookahead ---
        parts = re.split(r'\)\s+(?=[A-Z0-9])', entry)
    
    for part in parts:
        part = part.strip()
        
        if not part or 'choose' in part.lower():
            continue
        
        # Extract set name with piece count
        match = re.search(r'(.+?)\s*\(([24])\)', part)
        if match:
            set_name = match.group(1).strip()
            
            # Restore protected name
            if "Aubade of Morningstar & Moon" in set_name:
                set_name = set_name.replace("&", "and")
            
            # Skip generic descriptions
            if any(skip in set_name.lower() for skip in [
                'other', 'any', 'dps', 'conditional', 'see notes'
            ]):
                continue
            
            sets.append(set_name)
    
    return sets

def process_artifact_dict(input_file):
    unique_sets = {}
    removed_entries = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return
    
    dict_match = re.search(r'ARTIFACT_MAP\s*=\s*\{(.*?)\}', content, re.DOTALL)
    if not dict_match:
        print("Could not find ARTIFACT_MAP dictionary")
        return
    
    dict_content = dict_match.group(1)
    
    for line in dict_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'): continue
        
        match = re.match(r'"(.+?)":\s*"', line)
        if not match: continue
        
        key = match.group(1)
        original_key = key
        
        cleaned = clean_artifact_name(key)
        
        if not cleaned or len(cleaned) < 3:
            removed_entries.append({'original': original_key, 'reason': 'Too short'})
            continue
        
        skip_patterns = ['only used in', 'prioritize this', 'artifact calculations', 
                         'conditional', 'choose', '**', 'notes:']
        
        if any(p in cleaned.lower() for p in skip_patterns):
            removed_entries.append({'original': original_key, 'reason': 'Skip pattern'})
            continue
        
        extracted = extract_artifact_sets(cleaned)
        
        if not extracted:
            removed_entries.append({'original': original_key, 'reason': 'No valid sets'})
            continue
        
        for s in extracted:
            if s not in unique_sets: unique_sets[s] = []
            unique_sets[s].append(original_key)
    
    # Output
    print("=" * 80)
    print("CLEAN_ARTIFACT_MAP = {")
    for set_name in sorted(unique_sets.keys()):
        print(f'    "{set_name}": "",')
    print("}")
    print("=" * 80)

if __name__ == "__main__":
    process_artifact_dict("artifact_db.txt")