import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("DISCOURSE_EMAIL")
PASSWORD = os.getenv("DISCOURSE_PASSWORD")
LOGIN_URL = "https://discourse.onlinedegree.iitm.ac.in/login"
CATEGORY_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"
BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"

def login_and_get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Remove this line if you want to see the browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(LOGIN_URL)

    wait = WebDriverWait(driver, 20)

    # Fill username/email
    email_input = wait.until(EC.presence_of_element_located((By.ID, "login-account-name")))
    email_input.clear()
    email_input.send_keys(EMAIL)

    # Fill password
    password_input = driver.find_element(By.ID, "login-account-password")
    password_input.clear()
    password_input.send_keys(PASSWORD)

    # Submit form
    password_input.send_keys(Keys.RETURN)

    # Wait until login finishes (look for user menu)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "header-dropdown-toggle")))

    return driver

def get_topic_urls(driver):
    driver.get(CATEGORY_URL)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    topic_urls = []
    for a_tag in soup.select("a.title.raw-link"):
        href = a_tag.get("href")
        if href and href.startswith("/t/"):
            full_url = BASE_URL + href
            if full_url not in topic_urls:
                topic_urls.append(full_url)

    return topic_urls

def scrape_topic(driver, url):
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = soup.find("title").text.strip()
    posts = soup.find_all("div", class_="cooked")
    content = [p.get_text(separator=" ", strip=True) for p in posts]

    return {
        "url": url,
        "title": title,
        "posts": content
    }

def main():
    driver = login_and_get_driver()
    urls = get_topic_urls(driver)

    all_data = []
    for url in urls:
        print(f"Scraping: {url}")
        try:
            data = scrape_topic(driver, url)
            all_data.append(data)
            time.sleep(1)
        except Exception as e:
            print(f"Error on {url}: {e}")

    driver.quit()

    with open("tds_discourse_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()