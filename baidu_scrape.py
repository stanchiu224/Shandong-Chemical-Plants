import csv
import time
import random
import re
import os
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Load company names
input_file = "shandong_chemical_plant_list.csv"
df = pd.read_csv(input_file)
if "Company" not in df.columns:
    raise ValueError("The input CSV must contain a column named 'Company'")
companies = df["Company"].tolist()

# Determine where to resume from
existing_addresses = {}
if os.path.exists("addresses.csv"):
    with open("addresses.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) == 2:
                existing_addresses[row[0]] = row[1]

# Filter companies that haven't been processed yet
unprocessed_companies = [c for c in companies if c not in existing_addresses]

# Set up Selenium
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument(f'user-agent={random.choice([
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.117 Safari/537.36"
])}')
driver = webdriver.Chrome(options=chrome_options)

results = list(existing_addresses.items())

for idx, company in enumerate(unprocessed_companies):
    query = f"{company} 山东工厂 地址"
    url = f"https://www.baidu.com/s?wd={query}"

    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))  # Wait for content to load
        soup = BeautifulSoup(driver.page_source, "html.parser")
        address = ""

        # First: AI box
        ai_box = soup.select_one('.op-smart-answer-new-promotion-line')
        if ai_box:
            ai_text = ai_box.get_text()
            match = re.search(r"地址[:：]?(.*?)(\n|\s|点击查看地图|$)", ai_text)
            if match:
                address = match.group(1).strip()

        # Second: Map snippet fallback
        if not address:
            map_match = re.search(r"地址[:：]?(.*?)(\n|\s|附近企业|点击查看地图|$)", soup.get_text())
            if map_match:
                address = map_match.group(1).strip()

        # Third: General fallback from top search results
        if not address:
            search_results = soup.select("div.result")
            for result in search_results:
                result_text = result.get_text()
                fallback_match = re.search(r"地址[:：]?(.*?)(\n|\s|$)", result_text)
                if fallback_match:
                    address = fallback_match.group(1).strip()
                    if address:
                        break

        if not address:
            address = "address not found"

        print(f"{company} --> {address}")
        results.append((company, address))

        if len(results) % 10 == 0:
            with open("addresses.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Company", "Address"])
                writer.writerows(results)

        time.sleep(random.uniform(5, 10))

    except Exception as e:
        print(f"{company} --> Error: {e}")
        results.append((company, "error"))
        break  # assume block, halt batch

# Final write
with open("addresses.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Company", "Address"])
    writer.writerows(results)

driver.quit()
print("Scraping complete or interrupted. Saved to addresses.csv")
