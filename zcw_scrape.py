from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import csv
import re
import time

# Setup headless Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

# Load page and wait
url = "http://zctpt.com/chem/13818.html"
driver.get(url)
time.sleep(3)  # Let JS load

# Get full rendered HTML
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Now parse the dynamic content
content_div = soup.find("div", class_="article_content")
if not content_div:
    raise RuntimeError("Could not find article_content div.")

# Proceed as before...
raw_html = content_div.decode_contents()
blocks = re.split(r'<br\s*/?>\s*<br\s*/?>', raw_html)

# Same regex logic as before
patterns = {
    "company": re.compile(r'^(.+?有限公司)'),
    "legal": re.compile(r'法定代表人[（(]董事长、总经理[）)][:：] ?(.+?) '),
    "capital": re.compile(r'注册资本[:：]?([\d.]+)万人民币元'),
    "year": re.compile(r'成立时间[:：]?(\d{4}-\d{2}-\d{2})'),
    "email": re.compile(r'邮箱[:：]?([^\s<]+)'),
    "phone": re.compile(r'联系电话[:：]?([0-9\-]+)'),
    "address": re.compile(r'公司地址[:：]?(.+)')
}

companies = []
for block in blocks:
    text = ' '.join(BeautifulSoup(block, 'html.parser').stripped_strings)
    if not text.strip():
        continue

    company = {
        "Chinese Name": "",
        "English Name": "",
        "Address": "",
        "Latitude": "",
        "Longitude": "",
        "Main Products": "",
        "Registered Capital (RMB)": "",
        "Opening Year": ""
    }

    # Extract raw values using regex
    extracted = {}
    for key, pattern in patterns.items():
        match = pattern.search(text)
        if match:
            extracted[key] = match.group(1).strip()

    # Assign mapped fields
    company["Chinese Name"] = extracted.get("company", "")
    company["Address"] = extracted.get("address", "")
    
    # Registered Capital: convert to full RMB value
    raw_cap = extracted.get("capital", "")
    if raw_cap:
        try:
            company["Registered Capital (RMB)"] = str(int(float(raw_cap) * 10000))
        except ValueError:
            company["Registered Capital (RMB)"] = ""

    # Opening Year: just extract the year
    raw_date = extracted.get("year", "")
    if raw_date:
        company["Opening Year"] = raw_date[:4]

    if company["Chinese Name"]:
        companies.append(company)

# Write to CSV
with open("shandong_chemical_companies.csv", "w", newline='', encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=company.keys())
    writer.writeheader()
    writer.writerows(companies)

print(f"✅ Extracted {len(companies)} companies.")
