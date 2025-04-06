import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import re

def search_company_address_bing(driver, company_name):
    """
    Search for company address using Bing with Selenium to wait for AI-generated content
    
    Args:
        driver: Selenium WebDriver instance
        company_name (str): Name of the company
        
    Returns:
        dict: Dictionary with address information and source
    """
    # Format search query specifically for address in Shandong
    search_query = f"{company_name} 山东 工厂地址"
    
    result = {
        "company": company_name,
        "address": None,
        "source": None,
        "all_matches": []  # Store all potential address matches
    }
    
    try:
        # Navigate to Bing search
        driver.get(f"https://www.bing.com/search?q={search_query}&setlang=zh-CN")
        
        # Wait for page to load and AI-generated content to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "b_algo"))
        )
        
        # Take a screenshot to debug if needed
        driver.save_screenshot(f"{company_name}_search.png")
        
        # Additional wait for potentially dynamic content
        time.sleep(7)  # Wait longer for AI-generated summary to appear
        
        # Save a screenshot after waiting to see if content loaded
        driver.save_screenshot(f"{company_name}_after_wait.png")
        
        print(f"Looking for address for {company_name}...")
        
        # Try to find the address in the main AI snippet first
        try:
            # Check for the featured snippet (like in the screenshot)
            main_snippets = driver.find_elements(By.CSS_SELECTOR, "div.b_snippetBigText, div.b_caption, h2")
            for snippet in main_snippets:
                text = snippet.text.strip()
                if "山东" in text and any(marker in text for marker in ["号", "路", "经济技术开发区", "工业园"]):
                    result["address"] = text
                    result["source"] = "Bing Featured Snippet"
                    result["all_matches"].append({"text": text, "source": "Featured Snippet"})
                    print(f"Found in featured snippet: {text}")
        except Exception as e:
            print(f"Error finding featured snippet: {e}")
        
        # If no specific address found yet, get the entire page text
        if not result["address"]:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Look for specific address patterns in the entire page
            address_patterns = [
                r"山东省[^\n\.。,，:：]{5,60}号",
                r"山东省[^\n\.。,，:：]{5,60}路",
                r"山东省[^\n\.。,，:：]{5,60}街",
                r"山东省[^\n\.。,，:：]{5,60}工业园",
                r"山东省[^\n\.。,，:：]{5,60}开发区"
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    result["all_matches"].append({"text": match, "source": "Page Text Regex"})
                    print(f"Found potential address: {match}")
                    
                    # If we don't have an address yet, use the first match
                    if not result["address"] and len(match) < 200:
                        result["address"] = match
                        result["source"] = "Page Text Regex"
            
            # If still no match, try broader pattern
            if not result["address"]:
                broad_pattern = r"(山东省[^，。\n]{10,100})"
                matches = re.findall(broad_pattern, page_text)
                for match in matches:
                    if any(marker in match for marker in ["号", "路", "经济技术开发区", "工业园"]):
                        result["all_matches"].append({"text": match, "source": "Broad Regex"})
                        if not result["address"]:
                            result["address"] = match
                            result["source"] = "Broad Regex"
                            print(f"Found with broad pattern: {match}")
                
    except Exception as e:
        print(f"Error searching for {company_name}: {str(e)}")
    
    return result

def main():
    # List of companies to search for
    companies = [
        "万华化学集团股份有限公司",
        "山东东明化学集团有限公司",
        "利华益集团股份有限公司",
        "万达控股集团股份有限公司"
    ]
    
    # Configure Chrome options for running in a Codespace
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # These additional options might help in container environments
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-features=NetworkService")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-software-rasterizer")
    
    # Set up Chrome driver with specific binary location for Codespace
    print("Setting up Chrome driver...")
    service = Service(ChromeDriverManager().install())
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome driver initialized successfully")
        
        # Search for each company's address
        print("\nSearching for company addresses in Shandong Province...\n")
        
        results = []
        
        for company in companies:
            print(f"\nSearching for {company}...")
            result = search_company_address_bing(driver, company)
            
            if result["address"]:
                print(f"✓ Found primary address: {result['address']}")
                print(f"  Source: {result['source']}\n")
                print(f"  Total potential matches: {len(result['all_matches'])}")
            else:
                print(f"× No address found for {company}\n")
                
            results.append(result)
            
            # Delay between searches to avoid being blocked
            time.sleep(random.uniform(5, 8))
        
        # Output summary
        print("\n============ SUMMARY ============")
        for result in results:
            print(f"\n{result['company']}:")
            if result["address"]:
                print(f"  Primary Address: {result['address']}")
                print(f"  Source: {result['source']}")
                print(f"  All potential matches: {len(result['all_matches'])}")
            else:
                print("  No address found.")
        
        # Save results to a file with more detailed information
        with open("shandong_chemical_addresses.txt", "w", encoding="utf-8") as f:
            f.write("Shandong Chemical Company Addresses\n")
            f.write("==================================\n\n")
            for result in results:
                f.write(f"{result['company']}:\n")
                if result["address"]:
                    f.write(f"  Primary Address: {result['address']}\n")
                    f.write(f"  Source: {result['source']}\n\n")
                    
                    # Write all potential matches for manual review
                    f.write("  All potential address matches:\n")
                    for i, match in enumerate(result['all_matches'], 1):
                        f.write(f"    {i}. {match['text']}\n")
                        f.write(f"       Source: {match['source']}\n")
                else:
                    f.write("  No address found.\n")
                f.write("\n" + "-"*50 + "\n\n")
        
        print("\nResults saved to shandong_chemical_addresses.txt")
            
    except Exception as e:
        print(f"Failed to initialize Chrome driver: {str(e)}")
    finally:
        # Close the browser
        try:
            driver.quit()
            print("Browser closed successfully")
        except:
            pass

if __name__ == "__main__":
    main()