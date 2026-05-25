import re

def clean_artifact_name(name):
    """
    Clean artifact set name by:
    1. Removing numbering (1., 2., etc.)
    2. Removing priority markers (*)
    3. Removing special characters (+, ≈, etc.)
    4. Removing spacing issues
    5. Extracting individual sets from combined entries
    """
    # Remove leading numbers and dots
    name = re.sub(r'^\d+\.\s*', '', name)
    
    # Remove special characters like â‰ˆ, ≈, and +
    name = re.sub(r'^[â‰ˆ≈+]\s*', '', name)
    name = name.replace('â‰ˆ', '').replace('≈', '').replace('+', '')
    
    # Remove asterisks
    name = name.replace('*', '')
    
    # Strip whitespace
    name = name.strip()
    
    return name

def extract_artifact_sets(entry):
    """
    Extract individual artifact sets from an entry.
    Handles patterns like:
    - "Set A (4)"
    - "Set A (2) / Set B (2)"
    - "Set A (2) Set B (2)" (without /)
    - "[Choose Two]" or similar instructions
    Returns set names WITHOUT (2) or (4) piece indicators
    """
    sets = []
    
    # Remove bracket instructions like [Choose Two], [Choose One], etc.
    entry = re.sub(r'\[.*?\]', '', entry)
    
    # Remove parenthetical notes at the end
    entry = re.sub(r'\(see notes\)', '', entry, flags=re.IGNORECASE)
    entry = re.sub(r'\(.*?only.*?\)', '', entry, flags=re.IGNORECASE)
    
    # Split by common delimiters
    if '/' in entry:
        parts = entry.split('/')
    elif ' and ' in entry.lower():
        parts = re.split(r'\s+and\s+', entry, flags=re.IGNORECASE)
    else:
        # Try to split by pattern ")(", which indicates multiple sets
        parts = re.split(r'\)\s+(?=[A-Z+])', entry)
    
    for part in parts:
        part = part.strip()
        
        # Skip empty parts or pure instructions
        if not part or 'choose' in part.lower():
            continue
        
        # Extract set name with piece count
        # Pattern: "Set Name (2)" or "Set Name (4)"
        match = re.search(r'(.+?)\s*\(([24])\)', part)
        if match:
            set_name = match.group(1).strip()
            # piece_count removed - we don't include it anymore
            
            # Skip generic descriptions
            if any(skip in set_name.lower() for skip in [
                'other', 'any', 'dps', 'conditional', 'see notes'
            ]):
                continue
            
            # Just return the set name without piece count
            sets.append(set_name)
    
    return sets

def process_artifact_dict(input_file):
    """
    Process the artifact mapping dictionary and output unique cleaned names.
    """
    unique_sets = {}
    removed_entries = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract dictionary entries
    dict_match = re.search(r'ARTIFACT_MAP\s*=\s*\{(.*?)\}', content, re.DOTALL)
    if not dict_match:
        print("Could not find ARTIFACT_MAP dictionary")
        return
    
    dict_content = dict_match.group(1)
    
    # Parse each line
    for line in dict_content.split('\n'):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Extract the key (artifact description)
        match = re.match(r'"(.+?)":\s*"', line)
        if not match:
            continue
        
        key = match.group(1)
        original_key = key  # Save for reporting
        
        # Clean the name
        cleaned = clean_artifact_name(key)
        
        # Skip if empty or obvious junk
        if not cleaned or len(cleaned) < 3:
            removed_entries.append({
                'original': original_key,
                'reason': 'Empty or too short after cleaning'
            })
            continue
        
        # Skip certain patterns
        skip_patterns = [
            'only used in',
            'prioritize this',
            'artifact calculations',
            'conditional',
            'choose',
            '**',
            'notes:',
        ]
        
        skip_reason = None
        for pattern in skip_patterns:
            if pattern in cleaned.lower():
                skip_reason = f'Contains skip pattern: "{pattern}"'
                break
        
        if skip_reason:
            removed_entries.append({
                'original': original_key,
                'reason': skip_reason
            })
            continue
        
        # Extract individual sets
        sets = extract_artifact_sets(cleaned)
        
        if not sets:
            removed_entries.append({
                'original': original_key,
                'cleaned': cleaned,
                'reason': 'No valid artifact sets extracted'
            })
            continue
        
        # Add to unique sets with source tracking
        for artifact_set in sets:
            if artifact_set not in unique_sets:
                unique_sets[artifact_set] = []
            unique_sets[artifact_set].append(original_key)
    
    # Print removed entries
    print("=" * 80)
    print("REMOVED ENTRIES (for review):")
    print("=" * 80)
    for i, entry in enumerate(removed_entries, 1):
        print(f"\n{i}. Original: \"{entry['original']}\"")
        if 'cleaned' in entry:
            print(f"   Cleaned: \"{entry['cleaned']}\"")
        print(f"   Reason: {entry['reason']}")
    
    print("\n" + "=" * 80)
    print(f"Total removed: {len(removed_entries)}")
    print("=" * 80)
    
    # Output clean dictionary
    print("\n" + "=" * 80)
    print("CLEAN_ARTIFACT_MAP WITH SOURCES:")
    print("=" * 80)
    for set_name in sorted(unique_sets.keys()):
        print(f'\n"{set_name}": "",')
        print(f'  # Sources ({len(unique_sets[set_name])}):', )
        for source in unique_sets[set_name][:3]:  # Show first 3 sources
            print(f'  #   - "{source}"')
        if len(unique_sets[set_name]) > 3:
            print(f'  #   ... and {len(unique_sets[set_name]) - 3} more')
    
    print("\n" + "=" * 80)
    print("CLEAN_ARTIFACT_MAP (without sources):")
    print("=" * 80)
    print("CLEAN_ARTIFACT_MAP = {")
    for set_name in sorted(unique_sets.keys()):
        print(f'    "{set_name}": "",')
    print("}")
    
    print(f"\n# Total unique artifact sets: {len(unique_sets)}")
    print("=" * 80)

# Run the script
if __name__ == "__main__":
    process_artifact_dict("artifact_db.txt")
