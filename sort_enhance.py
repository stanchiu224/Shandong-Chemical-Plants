import pandas as pd
import time
import sys
import os

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
            return pd.read_csv(output_file)
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


if __name__ == "__main__":
    # File paths
    input_file = "shandong_chemical_companies.csv"
    output_file = "200_largest_chemical_plants.csv"
    
    # Parse command line arguments for force flags
    import argparse
    parser = argparse.ArgumentParser(description='Process and translate chemical company data.')
    parser.add_argument('--force-extract', action='store_true', help='Force extraction even if output file exists')
    parser.add_argument('--force-translate', action='store_true', help='Force translation even if English names exist')
    args = parser.parse_args()
    
    # Extract the 200 largest companies
    result = extract_largest_companies(input_file, output_file, force_extract=args.force_extract)
    
    if result is not False:
        # Translate company names
        if translate_company_names(output_file, force_translate=args.force_translate):
            # Clean translations
            clean_translations(output_file)