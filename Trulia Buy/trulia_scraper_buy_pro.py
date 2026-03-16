import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import pandas as pd
import time
import random
import os
import re
from datetime import datetime


# ================================
# CONFIG
# ================================

cities = [
    "Stamford",
    "Norwalk",
    "Darien",
    "Wilton",
    "New_Canaan"
]

BASE_URL = "https://www.trulia.com/CT/{}/"

OUTPUT_FILE = "trulia_buy_data.csv"
VISITED_FILE = "visited_links_buy.csv"

MAX_PAGES = 10


# ================================
# DRIVER
# ================================

def start_driver():

    options = uc.ChromeOptions()

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")

    driver = uc.Chrome(options=options, version_main=145)

    return driver


# ================================
# CAPTCHA DETECTION
# ================================

def captcha_detected(driver):

    page = driver.page_source.lower()

    words = [
        "captcha",
        "verify you are human",
        "security check"
    ]

    return any(w in page for w in words)


# ================================
# VISITED LINKS
# ================================

def load_visited_links():

    if os.path.exists(VISITED_FILE):

        df = pd.read_csv(VISITED_FILE)

        return set(df["URL"])

    return set()


def save_visited_link(link):

    df = pd.DataFrame([{"URL": link}])

    if not os.path.exists(VISITED_FILE):

        df.to_csv(VISITED_FILE, index=False)

    else:

        df.to_csv(VISITED_FILE, mode="a", header=False, index=False)


# ================================
# SAVE PROPERTY
# ================================

def save_property(data):

    df = pd.DataFrame([data])

    if not os.path.exists(OUTPUT_FILE):

        df.to_csv(OUTPUT_FILE, index=False)

    else:

        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)


# ================================
# COLLECT LINKS
# ================================

def collect_links(driver):

    cards = driver.find_elements(
        By.CSS_SELECTOR,
        "a[data-testid='property-card-link']"
    )

    urls = []

    for card in cards:

        try:

            link = card.get_attribute("href")

            if link and "/home/" in link:

                link = link.split("?")[0]

                urls.append(link)

        except:
            continue

    return list(set(urls))


# ================================
# PHONE EXTRACT
# ================================

def extract_phone(text):

    match = re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", text)

    if match:
        return match.group()

    return ""


# ================================
# PRICE EXTRACT
# ================================

def extract_price(text):

    match = re.search(r"\$\d[\d,]*", text)

    if match:
        return match.group()

    return ""


# ================================
# DATE EXTRACT
# ================================

def extract_date(text):

    match = re.search(r'on (\w+ \d{1,2}, \d{4})', text)

    if match:

        raw_date = match.group(1)

        date_obj = datetime.strptime(raw_date, "%b %d, %Y")

        return date_obj.strftime("%m/%d/%Y")

    return ""


# ================================
# OPEN TAB
# ================================

def open_new_tab(driver, link):

    driver.execute_script(f"window.open('{link}','_blank');")

    driver.switch_to.window(driver.window_handles[-1])


def close_tab(driver):

    driver.close()

    driver.switch_to.window(driver.window_handles[0])


# ================================
# SCRAPE PROPERTY
# ================================

def scrape_property(driver, link, city):

    try:

        open_new_tab(driver, link)

        time.sleep(random.uniform(6,9))

        if captcha_detected(driver):

            input("Solve CAPTCHA then press ENTER")

        # OWNER PHONE (FILTER)

        try:

            phone_element = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='owner-phone']"
            )

            phone = extract_phone(phone_element.text)

            if phone == "":
                close_tab(driver)
                return None

        except:
            close_tab(driver)
            return None

        # ADDRESS

        address = ""

        try:

            street = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='home-details-summary-headline']"
            ).text

            city_state = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='home-details-summary-city-state']"
            ).text

            address = f"{street}, {city_state}"

        except:
            pass

        # PRICE

        price = ""

        try:

            price = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='on-market-price-details']"
            ).text

        except:
            pass

        # DATE POSTED

        date_posted = ""

        try:

            seo_text = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='seo-description-paragraph']"
            ).text

            date_posted = extract_date(seo_text)

        except:
            pass

        scraping_date = datetime.now().strftime("%m/%d/%Y")

        data = {

            "Scraping Date": scraping_date,
            "Address": address,
            "City": city,
            "URL Link": link,
            "Phone Number": phone,
            "Email": "",
            "Name of Person": "",
            "Source": "Trulia",
            "Date Posted": date_posted,
            "Rental / Buy": "Buy",
            "Price Point": price

        }

        close_tab(driver)

        return data

    except Exception as e:

        print("Error scraping:", e)

        close_tab(driver)

        return None


# ================================
# MAIN SCRAPER
# ================================

def scrape_trulia():

    print("TRULIA BUY SCRAPER STARTED")

    driver = start_driver()

    visited_links = load_visited_links()

    print("Visited links loaded:", len(visited_links))

    for city in cities:

        print("\n===================================")
        print("CITY:", city)
        print("===================================")

        page = 1

        while page <= MAX_PAGES:

            if page == 1:

                url = BASE_URL.format(city)

            else:

                url = f"https://www.trulia.com/CT/{city}/{page}_p/"

            print("Opening:", url)

            driver.get(url)

            time.sleep(random.uniform(8,12))

            if captcha_detected(driver):

                input("Solve CAPTCHA then press ENTER")

            input(
                "\nScroll manually until listings load\n"
                "Press ENTER when ready..."
            )

            links = collect_links(driver)

            print("Listings found:", len(links))

            if len(links) == 0:
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

                    print("PROPERTY SAVED")

                else:

                    print("NO OWNER PHONE")

                time.sleep(random.uniform(7,11))

            page += 1

    driver.quit()

    print("\nSCRAPING FINISHED")


# ================================
# RUN
# ================================

if __name__ == "__main__":

    scrape_trulia()