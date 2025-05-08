import pandas as pd
import sys
import os

def print_gpt_analysis(csv_file):
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        print(f"Successfully read {len(df)} contractors from {csv_file}")
        
        
        # Print analysis for each contractor
        for idx, row in df.iterrows():
            print("\n" + "="*80)
            print(f"Contractor #{idx+1}: {row['name']}")
            print(f"Rating: {row['rating_stars']}")
            print(f"Phone: {row['phone_number']}")
            print(f"Certifications: {row['certifications']}")
            print("-"*80)
            if 'gpt_analysis' in df.columns:
                print("GPT ANALYSIS:")
                print("-"*80)
                print(row['gpt_analysis'])
                print("="*80)
            
            # After each contractor, ask if the user wants to continue
            if idx < len(df) - 1:
                user_input = input("\nPress Enter to view the next contractor (or 'q' to quit): ")
                if user_input.lower() == 'q':
                    print("Exiting...")
                    break
        
        print("\nEnd of file.")
        
    except FileNotFoundError:
        print(f"Error: File {csv_file} not found.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")


if __name__ == "__main__":
    csv_file = "gaf_roofing_contractors_with_analysis.csv"
    
    # Print GPT analysis
    print_gpt_analysis(csv_file)