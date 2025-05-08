import requests
import json
import os
import pandas as pd
import time

def analyze_contractor_with_gpt(contractor_data, api_key):
    """
    Send contractor data to GPT for analysis.
    
    Args:
        contractor_data: Dictionary containing contractor information
        api_key: OpenAI API key
        
    Returns:
        str: GPT's analysis response
    """
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Create a prompt that includes all the contractor information
    prompt = f"""
    Please analyze the following roofing contractor information and provide a very brief summary:
    
    Contractor Name: {contractor_data['name']}
    Rating: {contractor_data['rating_stars']}
    Certifications: {contractor_data['certifications']}
    Phone Number: {contractor_data['phone_number']}
    
    About Section:
    {contractor_data['about_section']}
    
    Based on this information, please provide:
    1. SUMMARY: A brief summary of the contractor (1 short sentence)
    2. STRENGTHS: Key strengths based on certifications and about section (keep to a short statement, no bullet points)
    3. CONCERNS: Any red flags or concerns (short statement 1 sentence or less. DO NOT comment on grammatical issues in any way)
    4. RATING: Overall rating on a scale of 1-10 with a short explanation.

    And please use the provided labels on the list.
    """
    
    data = {
        "model": "o3-mini-2025-01-31",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert in evaluating roofing contractors based on their information. You are working with a materials distributor, specifically with their sales team. You are providing information to generate leads and insights for the sales team. Provide concise, valuable insights."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            analysis = response.json()['choices'][0]['message']['content']
            return analysis
        else:
            print(f"Error {response.status_code}: {response.text}")
            return "Error in API call"
    
    except Exception as e:
        print(f"Exception during API call: {e}")
        return "Error in API call"


def process_contractors_with_gpt(input_file, output_file, api_key):
    """
    Process contractors from CSV file through GPT and save results.
    
    Args:
        input_file: Path to input CSV with contractor data
        output_file: Path to output CSV for results
        api_key: OpenAI API key
    """
    try:
        # Read the input CSV file
        df = pd.read_csv(input_file)
        print(f"Successfully read {len(df)} contractors from {input_file}")
        
        # Add a new column for GPT analysis
        df['gpt_analysis'] = 'N/A'
        
        # Process each contractor
        for idx, row in df.iterrows():
            try:
                contractor_name = row['name']
                print(f"\nProcessing contractor {idx+1}/{len(df)}: {contractor_name}")
                
                # skip if already processed
                # for future if expanding dataset
                if row.get('gpt_analysis') != 'N/A' and not pd.isna(row.get('gpt_analysis')):
                    print(f"Contractor already processed. Skipping.")
                    continue
                
                # create contractor data dictionary
                contractor_data = row.to_dict()
                
                # analyze with GPT
                analysis = analyze_contractor_with_gpt(contractor_data, api_key)
                print(f"GPT Analysis: {analysis[:100]}..." if len(analysis) > 100 else f"GPT Analysis: {analysis}")
                
                # Update dataframe
                df.at[idx, 'gpt_analysis'] = analysis
                
                # Save progress after every 5 contractors or on the last one
                if (idx + 1) % 5 == 0 or idx == len(df) - 1:
                    print(f"Saving progress to {output_file}...")
                    df.to_csv(output_file, index=False)
                
                # Rate limit to avoid exceeding API limits
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing contractor {idx+1}: {e}")
                # Save progress in case of error
                df.to_csv(output_file, index=False)
                continue
        
        # Save final results
        print(f"Saving final results to {output_file}...")
        df.to_csv(output_file, index=False)
        print(f"Successfully processed {len(df)} contractors")
        
    except Exception as e:
        print(f"Error during processing: {e}")


if __name__ == "__main__":
    # Input and output file paths
    input_file = "gaf_roofing_contractors_with_about.csv"
    output_file = "gaf_roofing_contractors_with_analysis.csv"
    
    # Get API key
    # Removed key for git
    openai_api_key = ""
    
    # Process contractors with GPT
    process_contractors_with_gpt(input_file, output_file, openai_api_key)