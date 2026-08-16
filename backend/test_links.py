import sys
sys.path.append('d:/jobfinder/Jobistan/backend')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://thejobcompany.co.in/job-category/batch/2027', wait_until='networkidle')
    raw = page.evaluate('Array.from(document.querySelectorAll("a")).map(a => ({text: a.innerText.trim(), href: a.href}))')
    
    for l in raw:
        href = l.get('href', '').lower()
        text = l.get('text', '').lower()
        if 'job' in href or 'job' in text:
            print(f"LINK: {text} -> {href}")
    browser.close()
