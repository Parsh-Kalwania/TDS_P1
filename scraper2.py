# scraper_course.py

from playwright.sync_api import sync_playwright
import json
import time

def scrape_tds_course():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set True if you don't want the browser UI
        page = browser.new_page()
        page.goto("https://tds.s-anand.net/#/2025-01/")

        print("⏳ Waiting for content to load...")
        page.wait_for_selector("nav", timeout=10000)
        time.sleep(2)

        print("📜 Extracting sidebar links...")
        sidebar_links = page.query_selector_all("nav a")
        content_data = []

        for link in sidebar_links:
            href = link.get_attribute("href")
            title = link.inner_text().strip()
            print(f"🔗 Visiting: {title}")

            # Navigate to the section
            page.goto(f"https://tds.s-anand.net{href}")
            page.wait_for_selector("article", timeout=5000)
            time.sleep(0.5)

            content = page.query_selector("article").inner_text().strip()

            content_data.append({
                "title": title,
                "url": f"https://tds.s-anand.net{href}",
                "content": content
            })

        browser.close()

        # Save as JSON
        with open("tds_course_content.json", "w", encoding="utf-8") as f:
            json.dump(content_data, f, indent=2, ensure_ascii=False)

        print("✅ Saved to tds_course_content.json")

if __name__ == "__main__":
    scrape_tds_course()
