import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import pandas as pd
import time
import random
import os
import re
from datetime import datetime


cities = [
    "Stamford,CT",
    "Norwalk,CT",
    "Darien,CT",
    "Wilton,CT",
    "New Canaan,CT"
]

SPECIAL_CITY_URLS = {
    "New Canaan,CT": "https://www.trulia.com/CT/New_Canaan/"
}

BASE_URL = "https://www.trulia.com/for_sale/{}/"

OUTPUT_FILE = "trulia_buy_data.csv"
VISITED_FILE = "visited_links_buy.csv"

MAX_PAGES = 20


# ---------------- DRIVER ---------------- #

def start_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    # 🔴 IMPORTANTE: versión correcta de tu Chrome
    driver = uc.Chrome(options=options, version_main=146)

    return driver


# ---------------- CAPTCHA ---------------- #

def captcha_present(driver):
    page = driver.page_source.lower()

    triggers = [
        "px-captcha",
        "verify you are human",
        "press & hold",
        "amzn-captcha"
    ]

    return any(t in page for t in triggers)


def wait_for_captcha(driver):
    if captcha_present(driver):
        print("\n⚠️ CAPTCHA DETECTED - solve manually")

        while captcha_present(driver):
            print("Waiting for captcha to be solved...")
            time.sleep(5)

        print("✅ Captcha solved\n")


# ---------------- FILE HANDLING ---------------- #

def load_visited_links():
    if os.path.exists(VISITED_FILE):
        df = pd.read_csv(VISITED_FILE)
        return set(df["URL"])
    return set()


def save_visited_link(link):
    df = pd.DataFrame([{"URL": link}])
    df.to_csv(VISITED_FILE, mode="a", header=not os.path.exists(VISITED_FILE), index=False)


def save_property(data):
    df = pd.DataFrame([data])
    df.to_csv(OUTPUT_FILE, mode="a", header=not os.path.exists(OUTPUT_FILE), index=False)


# ---------------- SCRAPING ---------------- #

def collect_links(driver, city):
    cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid='home-card-sale']")
    urls = []

    for card in cards:
        try:
            tags = card.find_elements(By.CSS_SELECTOR, "[data-testid^='property-tag']")

            if any("coming soon" in tag.text.lower() for tag in tags):
                print("Skipping COMING SOON")
                continue

            link_element = card.find_element(By.CSS_SELECTOR, "a")
            href = link_element.get_attribute("href")

            if href:
                urls.append(href.split("?")[0])

        except Exception as e:
            print("Error processing card:", e)

    return list(set(urls))


def extract_price(text):
    match = re.search(r"\$\d[\d,]*", text)
    return match.group() if match else ""


def extract_date(text):
    match = re.search(r'on (\w+ \d{1,2}, \d{4})', text)
    if match:
        return datetime.strptime(match.group(1), "%b %d, %Y").strftime("%m/%d/%Y")
    return ""


def scrape_property(driver, link, city):
    try:
        driver.get(link)
        time.sleep(random.uniform(5, 8))
        wait_for_captcha(driver)

        try:
            phone = driver.find_element(By.CSS_SELECTOR, "[data-testid='owner-phone']").text
            phone = phone.replace("Owner Phone:", "").strip()
        except:
            return None

        address = ""
        try:
            address = driver.find_element(By.CSS_SELECTOR, "[data-testid='home-details-summary-headline']").text
        except:
            pass

        price = ""
        try:
            price_text = driver.find_element(By.CSS_SELECTOR, "[data-testid='on-market-price-details']").text
            price = extract_price(price_text)
        except:
            pass

        date_posted = ""
        try:
            seo_text = driver.find_element(By.CSS_SELECTOR, "[data-testid='seo-description-paragraph']").text
            date_posted = extract_date(seo_text)
        except:
            pass

        return {
            "Scraping Date": datetime.now().strftime("%m/%d/%Y"),
            "Address": address,
            "City": city.split(",")[0],
            "URL Link": link,
            "Phone Number": phone,
            "Email": "",
            "Name of Person": "",
            "Source": "Trulia",
            "Date Posted": date_posted,
            "Rental / Buy": "Buy",
            "Price Point": price
        }

    except Exception as e:
        print("Error scraping property:", e)
        return None


def build_city_url(city, page):
    if city in SPECIAL_CITY_URLS:
        return SPECIAL_CITY_URLS[city] if page == 1 else SPECIAL_CITY_URLS[city] + f"{page}_p/"
    return BASE_URL.format(city) if page == 1 else f"https://www.trulia.com/for_sale/{city}/{page}_p/"


# ---------------- MAIN ---------------- #

def scrape_trulia():
    print("🚀 TRULIA SCRAPER STARTED")

    driver = start_driver()
    visited_links = load_visited_links()

    print("Visited links loaded:", len(visited_links))

    for city in cities:
        print(f"\n📍 CITY: {city}")

        page = 1

        while page <= MAX_PAGES:
            url = build_city_url(city, page)

            print("\n🌐 Opening:", url)
            driver.get(url)

            time.sleep(random.uniform(8, 15))
            wait_for_captcha(driver)

            # 🔴 SCROLL MANUAL (CLAVE)
            input(
                "\n⬇️ Scroll manually until ALL listings load\n"
                "Then press ENTER to continue..."
            )

            links = collect_links(driver, city)
            print("🔗 Listings found:", len(links))

            if not links:
                print("No listings found — stopping city.")
                break

            for link in links:
                if link in visited_links:
                    continue

                print("Scraping:", link)

                data = scrape_property(driver, link, city)

                visited_links.add(link)
                save_visited_link(link)

                if data:
                    save_property(data)
                    print("✅ Saved")

                time.sleep(random.uniform(4, 7))

            page += 1

    driver.quit()
    print("\n✅ SCRAPING FINISHED")


if __name__ == "__main__":
    scrape_trulia()