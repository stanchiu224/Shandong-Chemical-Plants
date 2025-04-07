import csv
import re

def extract_best_address(company_section):
    """
    Extract the most likely correct address from a company section in the text file
    """
    # First, check if there's a Primary Address section
    primary_address_match = re.search(r'Primary Address:\s*(.*?)(?:\n\s*Source:|$)', company_section, re.DOTALL)
    
    if primary_address_match:
        raw_address = primary_address_match.group(1).strip()
        
        # Extract the most likely address pattern from the raw text
        address_patterns = [
            # Most specific patterns first
            r'山东省[\w市县区]+[\w路街道]+\d+号',  # Standard address with number
            r'山东省[\w市县区]+经济技术开发区[\w路街道]+\d+号',  # Dev zone with number
            r'山东省[\w市县区]+[\w园区]+[\w路街道]+\d+号',  # Industrial park with number
            r'山东省[\w市县区]+[\w路街道]+[\w大厦]',  # Building name
            r'山东省[\w市县区]+[\w路街道]+',  # General address format
            r'山东省[\w市县区]+经济技术开发区[\w路街道]+',  # Dev zone without number
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, raw_address)
            if match:
                return match.group(0)
        
        # If no patterns match in the primary address, look for anything with 山东省
        if '山东省' in raw_address:
            # Try to extract a reasonable length sentence with 山东省
            sentences = re.findall(r'(山东省[^。，；\n]{5,60})', raw_address)
            if sentences:
                return sentences[0]
            else:
                # Just return the first 100 chars as fallback
                return raw_address[:100].strip()
    
    # If no primary address section, check the "All potential address matches" section
    all_matches_section = re.search(r'All potential address matches:(.*?)(?=\n-{10}|\Z)', company_section, re.DOTALL)
    
    if all_matches_section:
        matches_text = all_matches_section.group(1).strip()
        matches = re.findall(r'\d+\.\s*(.*?)(?:\n\s*Source:|$)', matches_text, re.DOTALL)
        
        # Go through each match and look for address patterns
        for match in matches:
            for pattern in [
                r'(山东省[\w市县区]+[\w路街道]+\d+号)',
                r'(山东省[\w市县区]+经济技术开发区[\w路街道]+\d+号)',
                r'(山东省[\w市县区]+[\w路街道]+[\w大厦])',
                r'(山东省[\w市县区]+[\w路街道]+)',
            ]:
                address_match = re.search(pattern, match)
                if address_match:
                    return address_match.group(1)
        
        # If no structured address found, return the first match that contains 山东省
        for match in matches:
            if '山东省' in match:
                sentences = re.findall(r'(山东省[^。，；\n]{5,60})', match)
                if sentences:
                    return sentences[0]
    
    # Last resort - try to find any address-like pattern in the entire company section
    for pattern in [
        r'(山东省[\w市县区]+[\w路街道]+\d+号)',
        r'(山东省[\w市县区]+经济技术开发区[\w路街道]+\d+号)',
        r'(山东省[\w市县区]+[\w路街道]+[\w大厦])',
        r'(山东省[\w市县区]+[\w路街道]+)',
    ]:
        address_match = re.search(pattern, company_section)
        if address_match:
            return address_match.group(1)
            
    return "Address not found"

def parse_addresses_file(file_path):
    """
    Parse the addresses file and extract company information with improved address extraction
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content into company sections using the divider lines
    company_sections = re.split(r'\n-{10,}\n', content)
    
    companies = []
    
    for section in company_sections:
        if not section.strip() or "Shandong Chemical Company Addresses" in section:
            continue
        
        # Extract company name
        company_match = re.match(r'([^:]+):', section.strip())
        if not company_match:
            continue
            
        company_name = company_match.group(1).strip()
        
        # Extract the best address from this section
        address = extract_best_address(section)
        
        companies.append({
            'chinese_name': company_name,
            'english_name': translate_company_name(company_name),
            'address': address,
            'latitude': '',
            'longitude': '',
            'main_products': get_main_products(company_name)
        })
    
    return companies

def translate_company_name(chinese_name):
    """Provide English translation for known company names"""
    # This could be expanded with more companies as needed
    translations = {
        "万华化学集团股份有限公司": "Wanhua Chemical Group Co., Ltd.",
        "山东东明化学集团有限公司": "Shandong Dongming Chemical Group Co., Ltd.",
        "利华益集团股份有限公司": "Liwayee Group Co., Ltd.",
        "万达控股集团股份有限公司": "Wanda Holdings Group Co., Ltd."
    }
    
    # If no translation exists, create a basic one
    if chinese_name not in translations:
        # This is a very basic translation approach - for production use,
        # consider using an actual translation API
        basic_translation = chinese_name
        basic_translation = basic_translation.replace("有限公司", "Co., Ltd.")
        basic_translation = basic_translation.replace("股份", "")
        basic_translation = basic_translation.replace("集团", "Group")
        basic_translation = basic_translation.replace("化学", "Chemical")
        basic_translation = basic_translation.replace("山东", "Shandong")
        return basic_translation
        
    return translations.get(chinese_name, chinese_name)

def get_main_products(company_name):
    """Return main products for each company based on research"""
    # This could be expanded with more companies as needed
    products = {
        "万华化学集团股份有限公司": "MDI, TDI, polyols, petrochemicals, fine chemicals",
        "山东东明化学集团有限公司": "Petroleum products, chemicals, petrochemical products",
        "利华益集团股份有限公司": "Refined petroleum products, pharmaceuticals, textiles",
        "万达控股集团股份有限公司": "Petroleum products, chemicals, energy"
    }
    
    # Default products for chemical companies
    return products.get(company_name, "Chemical products, petrochemicals")

def write_csv(companies, output_file):
    """Write the company data to a CSV file"""
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['Chinese Name', 'English Name', 'Address', 'Latitude', 'Longitude', 'Main Products'])
        
        # Write data
        for company in companies:
            writer.writerow([
                company['chinese_name'],
                company['english_name'],
                company['address'],
                company['latitude'],
                company['longitude'],
                company['main_products']
            ])
    
    return len(companies)

def main():
    input_file = 'shandong_chemical_addresses.txt'
    output_file = 'shandong_chemical_plants.csv'
    
    # Parse the file to extract company information
    companies = parse_addresses_file(input_file)
    
    # Add test data validation
    for company in companies:
        print(f"Company: {company['chinese_name']}")
        print(f"Address: {company['address']}")
        print("---")
    
    # Write to CSV
    count = write_csv(companies, output_file)
    
    print(f"\nSuccessfully created {output_file} with {count} companies")
    print("\nNote: Latitude and Longitude fields are empty. You'll need to geocode these addresses separately.")
    print("The English names for any new companies are auto-generated and may need manual verification.")

if __name__ == "__main__":
    main()