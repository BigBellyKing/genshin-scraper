import csv
import re

# CONFIGURATION
input_file = 'artifacts_usage_starred.csv'
output_file = 'artifacts_usage_starred_cleaned.csv'
target_column = 'Top Artifact Sets'

# THE LOGIC
def add_spaces_after_commas():
    # The user's regex: Matches a comma NOT followed by a whitespace
    # We will replace it with ", "
    pattern = re.compile(r',(?!\s)')
    
    try:
        with open(input_file, mode='r', encoding='utf-8', newline='') as infile:
            reader = csv.DictReader(infile)
            
            # verify column exists
            if target_column not in reader.fieldnames:
                print(f"Error: Column '{target_column}' not found in CSV.")
                return

            # Prepare output
            with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
                writer.writeheader()

                changes_count = 0
                
                for row in reader:
                    original_value = row[target_column]
                    
                    # Apply regex only if there is data in that column
                    if original_value:
                        # process the string
                        new_value = pattern.sub(', ', original_value)
                        
                        if new_value != original_value:
                            row[target_column] = new_value
                            changes_count += 1
                    
                    writer.writerow(row)

        print(f"Success. Processed file.")
        print(f"Fixed formatting in {changes_count} rows.")
        print(f"Saved to: {output_file}")

    except FileNotFoundError:
        print(f"Error: Could not find file '{input_file}'. Make sure it is in the same folder.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    add_spaces_after_commas()