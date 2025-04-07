import pandas as pd
import time
import sys
import os
import requests
import json
import numpy as np

# --- Constants ---
# Assume the address column name is 'Address'. 
# !!! IMPORTANT: Change this if your CSV uses a different column name !!!
ADDRESS_COLUMN = 'Address' 

# Delay between API calls in seconds to avoid hitting rate limits
GEOCODE_DELAY = 0.1 

def extract_largest_companies(input_file, output_file, num_companies=200, force_extract=False):
    """
    Extract the largest companies by registered capital from a CSV file
    and save them to a new CSV file. Skip if output file already exists.
    
    Parameters:
    input_file (str): Path to the input CSV file
    output_file (str): Path to the output CSV file
    num_companies (int): Number of largest companies to extract
    force_extract (bool): Whether to extract even if output file exists
    
    Returns:
    DataFrame or False: Extracted companies data or False if failed
    """
    # Check if output file already exists
    if os.path.exists(output_file) and not force_extract:
        print(f"Output file {output_file} already exists. Reading existing data.")
        try:
            # Read existing data, ensuring correct types for lat/lon if they exist
            dtype_spec = {}
            # Check if lat/lon columns exist by reading just the header
            try:
                header_df = pd.read_csv(output_file, nrows=0)
                if 'Latitude' in header_df.columns:
                    dtype_spec['Latitude'] = float
                if 'Longitude' in header_df.columns:
                    dtype_spec['Longitude'] = float
            except Exception:
                pass # Ignore errors if file is empty or malformed initially
                
                return pd.read_csv(output_file, dtype=dtype_spec)
        except Exception as e:
            print(f"Error reading existing file: {e}")
            return False
        
    
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Check if the required column exists
        if 'Registered Capital (RMB)' not in df.columns:
            print("Error: Could not find 'Registered Capital (RMB)' column in the CSV file.")
            return False
        
        # Sort the dataframe by registered capital in descending order
        sorted_df = df.sort_values(by='Registered Capital (RMB)', ascending=False)
        
        # Extract the top companies
        top_companies = sorted_df.head(num_companies)
        
        # Save to a new CSV file
        top_companies.to_csv(output_file, index=False)
        
        print(f"Successfully extracted the {num_companies} largest companies to {output_file}")
        
        # Return the dataframe for potential further processing
        return top_companies
    
    except Exception as e:
        print(f"Error processing the file: {e}")
        return False


def setup_translator():
    """
    Set up the translator with the correct googletrans version
    """
    try:
        # First check if googletrans is installed
        try:
            import googletrans
            print(f"Found googletrans version: {googletrans.__version__}")
            
            # If it's not version 4.0.0-rc1, suggest reinstalling
            if googletrans.__version__ != '4.0.0-rc1':
                print("Warning: You're using an unsupported version of googletrans.")
                print("For best results, please run: pip uninstall -y googletrans && pip install googletrans==4.0.0-rc1")
                print("Continuing with current version, but translation may fail...")
        
        except ImportError:
            print("googletrans not found. Installing recommended version...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "googletrans==4.0.0-rc1"])
            print("Successfully installed googletrans 4.0.0-rc1")
        
        # Import the translator class (this will be from whatever version is installed)
        from googletrans import Translator
        translator = Translator(service_urls=['translate.google.com'])
        
        # Test the translator with a simple phrase
        try:
            test_result = translator.translate('测试', src='zh-cn', dest='en')
            print(f"Translator test: '测试' -> '{test_result.text}'")
            return translator
        except Exception as e:
            print(f"Translator test failed: {e}")
            return None
            
    except Exception as e:
        print(f"Error setting up translator: {e}")
        return None


def translate_company_names(csv_file, force_translate=False):
    """
    Translate Chinese company names to English in the CSV file and update it.
    Skip if English names already exist.
    
    Parameters:
    csv_file (str): Path to the CSV file containing company data
    force_translate (bool): Whether to translate even if English names exist
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Check if the required column exists
        if 'Chinese Name' not in df.columns:
            print("Error: Could not find 'Chinese Name' column in the CSV file.")
            return False
        
        # Ensure 'English Name' column exists and is of string type
        if 'English Name' not in df.columns:
            df['English Name'] = ""
        
        # Check if translations already exist
        if not force_translate and df['English Name'].notna().sum() > 0:
            print(f"English names already exist in {csv_file}. Skipping translation.")
            return True
        
        # Convert all columns to string to avoid dtype issues
        for col in df.columns:
            df[col] = df[col].astype(str)
        
        # Where values are 'nan', replace with empty string
        df.replace('nan', '', inplace=True)
            
        print("Setting up translator...")
        translator = setup_translator()
        
        if translator is None:
            print("Failed to set up translator. Cannot proceed with translation.")
            return False
            
        print("Starting translation of company names...")
        
        # Total rows to translate
        total_rows = len(df)
        translated_count = 0
        
        # Process each row individually
        for i in range(total_rows):
            chinese_name = df.loc[i, 'Chinese Name']
            
            # Skip empty values
            if chinese_name == '':
                continue
                
            try:
                # Skip if already has non-empty English name and not forcing translation
                if not force_translate and df.loc[i, 'English Name'] != '':
                    continue
                
                # Try to translate the name
                translation = translator.translate(chinese_name, src='zh-cn', dest='en')
                df.loc[i, 'English Name'] = translation.text
                
                # Update progress
                translated_count += 1
                if translated_count % 5 == 0:
                    print(f"Translated {translated_count} company names...")
                
                # Small delay to avoid potential rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error translating '{chinese_name}': {e}")
                # Leave the existing value or empty string
                if df.loc[i, 'English Name'] == 'nan':
                    df.loc[i, 'English Name'] = ''
        
        # Save the updated dataframe
        df.to_csv(csv_file, index=False)
        print(f"Successfully updated {csv_file} with {translated_count} English translations")
        return True
        
    except Exception as e:
        print(f"Error translating company names: {e}")
        return False


def clean_translations(csv_file):
    """
    Remove quotation marks from English translations in the CSV file.
    
    Parameters:
    csv_file (str): Path to the CSV file containing company data with translations
    """
    try:
        # Read the CSV file
        print(f"Reading file: {csv_file}")
        df = pd.read_csv(csv_file)
        
        # Check if the required column exists
        if 'English Name' not in df.columns:
            print("Error: Could not find 'English Name' column in the CSV file.")
            return False
        
        # Count rows with quotation marks
        quote_count = 0
        
        # Process each English name
        for i in range(len(df)):
            if pd.notna(df.loc[i, 'English Name']):
                english_name = str(df.loc[i, 'English Name'])
                
                # Remove quotation marks if present
                if english_name.startswith('"') and english_name.endswith('"'):
                    df.loc[i, 'English Name'] = english_name[1:-1]
                    quote_count += 1
                # Also handle single quotes
                elif english_name.startswith("'") and english_name.endswith("'"):
                    df.loc[i, 'English Name'] = english_name[1:-1]
                    quote_count += 1
        
        # Save the updated dataframe
        df.to_csv(csv_file, index=False)
        print(f"Successfully cleaned {quote_count} translations in {csv_file}")
        return True
        
    except Exception as e:
        print(f"Error cleaning translations: {e}")
        return False

def get_lat_long(address, api_key):
    """
    Geocode an address using Google Maps Geocoding API.
    
    Parameters:
    address (str): The address to geocode.
    api_key (str): Your Google Maps API key.
    
    Returns:
    tuple: (latitude, longitude) or (None, None) if failed.
    """
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': api_key
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        results = response.json()
        
        if results['status'] == 'OK':
            location = results['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        elif results['status'] == 'ZERO_RESULTS':
            print(f"Warning: Geocoding API found no results for address: '{address}'")
            return None, None
        else:
            # Log other potential errors like OVER_QUERY_LIMIT, REQUEST_DENIED, INVALID_REQUEST
            print(f"Warning: Geocoding API error for address '{address}'. Status: {results['status']}. Message: {results.get('error_message', 'N/A')}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        print(f"Error during Geocoding API request for '{address}': {e}")
        return None, None
    except Exception as e:
        print(f"Error processing geocoding result for '{address}': {e}")
        return None, None


def geocode_addresses(csv_file, force_geocode=False):
    """
    Add latitude and longitude to the CSV file using Google Maps Geocoding API.
    Skips if Latitude/Longitude columns exist and have data, unless force_geocode is True.
    
    Parameters:
    csv_file (str): Path to the CSV file.
    force_geocode (bool): Whether to geocode even if lat/lon data exists.
    
    Returns:
    bool: True if successful or skipped, False otherwise.
    """
    # --- 1. Get API Key ---
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Please set the GOOGLE_API_KEY environment variable with your Google Maps API key.")
        # Example for bash/zsh: export GOOGLE_API_KEY='YOUR_API_KEY_HERE'
        # Example for GitHub Codespaces: Add it as a secret named GOOGLE_API_KEY
        return False
        
    # --- 2. Read CSV and Check Columns ---
    try:
        # Read with specific dtypes if columns exist
        dtype_spec = {}
        try:
            header_df = pd.read_csv(csv_file, nrows=0)
            if 'Latitude' in header_df.columns:
                dtype_spec['Latitude'] = float
            if 'Longitude' in header_df.columns:
                dtype_spec['Longitude'] = float
        except Exception:
             pass # Ignore if file doesn't exist or is empty

        df = pd.read_csv(csv_file, dtype=dtype_spec)

        # Check if address column exists
        if ADDRESS_COLUMN not in df.columns:
            print(f"Error: Address column '{ADDRESS_COLUMN}' not found in {csv_file}.")
            print("Please ensure the address column name is correct (check ADDRESS_COLUMN constant).")
            return False

        # Add Latitude/Longitude columns if they don't exist
        if 'Latitude' not in df.columns:
            df['Latitude'] = pd.NA # Use pandas NA for missing floats
        if 'Longitude' not in df.columns:
            df['Longitude'] = pd.NA
            
        # Ensure correct data types (float for coordinates)
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')

    except FileNotFoundError:
        print(f"Error: CSV file not found: {csv_file}")
        return False
    except Exception as e:
        print(f"Error reading or preparing CSV file {csv_file}: {e}")
        return False

    # --- 3. Identify Rows to Geocode ---
    # Rows that need geocoding: EITHER Latitude is missing OR force_geocode is True
    needs_geocoding = df['Latitude'].isna()
    if not force_geocode and not needs_geocoding.any():
        print(f"Latitude/Longitude data already exists for all entries in {csv_file}. Skipping geocoding.")
        return True
        
    rows_to_process_indices = df.index[needs_geocoding | force_geocode]
    total_to_geocode = len(rows_to_process_indices)
    
    if total_to_geocode == 0:
         print("No addresses need geocoding.")
         return True

    print(f"Starting geocoding for {total_to_geocode} addresses...")
    geocoded_count = 0
    
    # --- 4. Iterate and Geocode ---
    for index in rows_to_process_indices:
        address = df.loc[index, ADDRESS_COLUMN]
        
        # Skip if address is empty or NaN
        if pd.isna(address) or not str(address).strip():
            print(f"Skipping row {index}: Empty address.")
            continue
            
        address = str(address).strip() # Ensure it's a clean string

        # Enhance address: Add "山东省" if not present
        province_name = "山东省"
        if province_name not in address:
            # Prepend for clarity, common in Chinese addresses
            enhanced_address = province_name + address 
        else:
            enhanced_address = address
            
        # Call the geocoding function
        lat, lon = get_lat_long(enhanced_address, api_key)
        
        # Update DataFrame
        df.loc[index, 'Latitude'] = lat
        df.loc[index, 'Longitude'] = lon
        
        geocoded_count += 1
        if geocoded_count % 10 == 0: # Print progress every 10 addresses
            print(f"Geocoded {geocoded_count}/{total_to_geocode} addresses...")
            
        # Delay between requests
        time.sleep(GEOCODE_DELAY) 

    # --- 5. Save Updated CSV ---
    try:
        df.to_csv(csv_file, index=False)
        print(f"Successfully geocoded {geocoded_count} addresses and updated {csv_file}.")
        return True
    except Exception as e:
        print(f"Error saving updated CSV file {csv_file}: {e}")
        return False

# --- Main Execution Block ---    
if __name__ == "__main__":
    # File paths
    input_file = "shandong_chemical_companies.csv"
    output_file = "200_largest_chemical_plants.csv"
    
    # Parse command line arguments for force flags
    import argparse
    parser = argparse.ArgumentParser(description='Process and translate, and geocode chemical company data.')
    parser.add_argument('--force-extract', action='store_true', help='Force extraction even if output file exists')
    parser.add_argument('--force-translate', action='store_true', help='Force translation even if English names exist')
    parser.add_argument('--force-geocode', action='store_true', help='Force geocoding even if Latitude/Longitude data exists')
    args = parser.parse_args()
    
# --- Step 1: Extract Largest Companies ---
    print("--- Step 1: Extracting Largest Companies ---")
    result_df = extract_largest_companies(input_file, output_file, force_extract=args.force_extract)
    
    if result_df is False:
        print("Extraction failed. Exiting.")
        sys.exit(1) # Exit if extraction fails

    # --- Step 2: Translate Company Names ---
    print("\n--- Step 2: Translating Company Names ---")
    if not translate_company_names(output_file, force_translate=args.force_translate):
        print("Translation step failed or was skipped due to errors. Continuing...")
        # Decide if you want to exit here or continue to geocoding
        # sys.exit(1) 

    # --- Step 3: Clean Translations ---
    print("\n--- Step 3: Cleaning Translations ---")
    if not clean_translations(output_file):
         print("Cleaning translations failed. Continuing...")
         # Decide if you want to exit here or continue to geocoding
         # sys.exit(1)

    # --- Step 4: Geocode Addresses ---
    print("\n--- Step 4: Geocoding Addresses ---")
    # Check if the required library 'requests' is installed
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found. Please install it: pip install requests")
        sys.exit(1)
        
    if not geocode_addresses(output_file, force_geocode=args.force_geocode):
        print("Geocoding step failed or was skipped due to errors.")
        # Decide if you want to exit here
        # sys.exit(1) 
        
    print("\n--- Processing Complete ---")

