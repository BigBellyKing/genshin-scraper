import pandas as pd
import re

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & LOAD
# -----------------------------------------------------------------------------
# Replace these filenames with your actual local paths
file1_path = 'artifacts_usage_starred_cleaned.csv'
file2_path = 'artifacts_usage.csv'

def load_data(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

df1 = load_data(file1_path)
df2 = load_data(file2_path)

if df1 is None or df2 is None:
    exit()

# -----------------------------------------------------------------------------
# 2. NORMALIZATION FUNCTIONS
# -----------------------------------------------------------------------------

def normalize_string(s):
    """Lowercases and removes non-alphanumeric chars (for sets/stats)."""
    if not isinstance(s, str): return ""
    return re.sub(r'[^a-z0-9]', '', s.lower())

def normalize_list(s):
    """Turns 'Set A, Set B' into a sorted, normalized list ['seta', 'setb']"""
    if not isinstance(s, str): return set()
    # Split by comma, normalize each item, remove empty strings
    items = [normalize_string(x) for x in s.split(',')]
    return set(filter(None, items))

def clean_char_name(name):
    """Standardizes character names for matching."""
    if not isinstance(name, str): return ""
    # Remove parens like (Anemo), remove whitespace, upper case
    name = re.sub(r'\(.*?\)', '', name) 
    return re.sub(r'[^A-Z0-9]', '', name.upper())

# -----------------------------------------------------------------------------
# 3. PRE-PROCESSING
# -----------------------------------------------------------------------------

# Standardize Column Headers for easier access
df1.columns = ['Name', 'Sets', 'Sands', 'Goblet', 'Circlet', 'Substats']
df2.columns = ['Name', 'Sets', 'Sands', 'Goblet', 'Circlet', 'Substats']

# Create a "Match Key" for joining
df1['MatchKey'] = df1['Name'].apply(clean_char_name)
df2['MatchKey'] = df2['Name'].apply(clean_char_name)

# -----------------------------------------------------------------------------
# 4. LOGIC: FUZZY MERGE
# -----------------------------------------------------------------------------
# We need to handle cases like "HEIZOU" (File 2) vs "SHIKANOINHEIZOU" (File 1)

unique_keys_1 = df1['MatchKey'].unique()
unique_keys_2 = df2['MatchKey'].unique()

mapping = {}

# Try to map Key 2 to Key 1 (assuming File 2 often has shorter names)
for k2 in unique_keys_2:
    match_found = False
    # Exact match
    if k2 in unique_keys_1:
        mapping[k2] = k2
        match_found = True
    else:
        # Substring match (e.g., HEIZOU in SHIKANOINHEIZOU)
        for k1 in unique_keys_1:
            if k2 in k1 or k1 in k2:
                mapping[k2] = k1
                match_found = True
                break
    
    if not match_found:
        mapping[k2] = None # Will show as unmapped

# Apply mapping to DF2 to align it with DF1
df2['MatchKey'] = df2['MatchKey'].map(mapping).fillna(df2['MatchKey'])

# -----------------------------------------------------------------------------
# 5. COMPARISON EXECUTION
# -----------------------------------------------------------------------------

results = []

# Iterate through File 1 (Base/Guide Data)
for index, row1 in df1.iterrows():
    char_key = row1['MatchKey']
    
    # Find corresponding row in File 2 (Usage Data)
    row2_match = df2[df2['MatchKey'] == char_key]
    
    if row2_match.empty:
        results.append({
            'Character': row1['Name'],
            'Status': 'Only in File 1 (New/Starred)',
            'Set_Match': 'N/A',
            'MainStat_Match': 'N/A'
        })
        continue
    
    # If multiple matches in File 2 (rare), take the first
    row2 = row2_match.iloc[0]

    # --- COMPARE SETS ---
    set1 = normalize_list(row1['Sets'])
    set2 = normalize_list(row2['Sets'])
    
    # Jaccard Index for set similarity (Intersection over Union)
    if not set1 and not set2:
        set_score = 1.0
    else:
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        set_score = intersection / union if union > 0 else 0

    # --- COMPARE MAIN STATS (Aggregated Sands/Goblet/Circlet) ---
    stats1 = normalize_list(row1['Sands']) | normalize_list(row1['Goblet']) | normalize_list(row1['Circlet'])
    stats2 = normalize_list(row2['Sands']) | normalize_list(row2['Goblet']) | normalize_list(row2['Circlet'])
    
    missing_stats_in_file2 = stats1 - stats2
    extra_stats_in_file2 = stats2 - stats1

    # Define a simple "Match Quality" string
    if set_score == 1.0:
        set_status = "Exact Match"
    elif set_score > 0.5:
        set_status = "Partial Match"
    elif set_score > 0:
        set_status = "Weak Match"
    else:
        set_status = "Complete Mismatch"

    results.append({
        'Character': row1['Name'],
        'Status': 'Compared',
        'Set_Status': set_status,
        'Missing_Sets_in_Usage': ", ".join(set1 - set2),
        'Extra_Sets_in_Usage': ", ".join(set2 - set1),
        'Stats_Discrepancy': f"Guide suggests {list(missing_stats_in_file2)} not found in top usage" if missing_stats_in_file2 else "Matches usage stats"
    })

# Check for characters in File 2 that are NOT in File 1
file1_keys = set(df1['MatchKey'])
file2_only = df2[~df2['MatchKey'].isin(file1_keys)]

for index, row in file2_only.iterrows():
    results.append({
        'Character': row['Name'],
        'Status': 'Only in File 2 (Old/Usage)',
        'Set_Status': 'N/A',
        'Missing_Sets_in_Usage': 'N/A',
        'Extra_Sets_in_Usage': 'N/A',
        'Stats_Discrepancy': 'N/A'
    })

# -----------------------------------------------------------------------------
# 6. OUTPUT
# -----------------------------------------------------------------------------
output_df = pd.DataFrame(results)

# Prioritize the "Mismatches" for the user to see
output_df = output_df.sort_values(by=['Status', 'Character'])

print("--- COMPARISON SUMMARY ---")
print(output_df['Status'].value_counts())
print("\n--- SAMPLE DISCREPANCIES (Top 5) ---")
print(output_df[output_df['Set_Status'] == 'Complete Mismatch'].head(5)[['Character', 'Missing_Sets_in_Usage', 'Extra_Sets_in_Usage']])

# Save to CSV
output_filename = 'artifact_comparison_report.csv'
output_df.to_csv(output_filename, index=False)
print(f"\nDetailed report saved to: {output_filename}")