import pandas as pd
import json
import os

# Define expected artifact sets from your dictionary values
with open("whitelist.txt", "r") as f:
    whitelist = set(line.strip() for line in f if line.strip())

def run_health_check():
    print("📋 Running Consolidated Pipeline Health Check...")
    
    # 1. Check for blank or corrupted outputs
    if not os.path.exists("artifacts_usage_filtered.csv"):
        print("❌ CRITICAL: artifacts_usage_filtered.csv is missing!")
        return

    df = pd.read_csv("artifacts_usage_filtered.csv")
    
    # 2. Check for missing critical characters
    output_chars = set(name.split('_')[0] for name in df['Character Name'])
    missing_whitelisted = whitelist - output_chars
    if missing_whitelisted:
        print(f"⚠️  WARNING: Whitelisted characters missing from final output: {missing_whitelisted}")
    
    # 3. Check for empty key fields
    empty_artifacts = df[df['Top Artifact Sets'].isna() | (df['Top Artifact Sets'] == "")]
    if not empty_artifacts.empty:
        print(f"⚠️  WARNING: Found rows with completely empty artifacts:")
        for _, row in empty_artifacts.iterrows():
            print(f"  - {row['Character Name']}")
            
    # 4. Check for unspaced commas (Your formatting fix)
    # Checks if we have commas without spaces
    comma_faults = df[df['Top Artifact Sets'].str.contains(r',(?!\s)', regex=True, na=False)]
    if not comma_faults.empty:
        print(f"⚠️  WARNING: {len(comma_faults)} rows have bad comma spacing in Top Artifact Sets. Run format spacing fix.")

    print("✨ Health check complete.")

if __name__ == "__main__":
    run_health_check()