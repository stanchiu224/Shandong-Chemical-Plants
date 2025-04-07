import pandas as pd

def extract_largest_companies(input_file, output_file, num_companies=200):
    """
    Extract the largest companies by registered capital from a CSV file
    and save them to a new CSV file.
    
    Parameters:
    input_file (str): Path to the input CSV file
    output_file (str): Path to the output CSV file
    num_companies (int): Number of largest companies to extract
    """
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
        return True
    
    except Exception as e:
        print(f"Error processing the file: {e}")
        return False

if __name__ == "__main__":
    # File paths
    input_file = "shandong_chemical_companies.csv"
    output_file = "200_largest_chemical_plants.csv"
    
    # Extract the 200 largest companies
    extract_largest_companies(input_file, output_file)