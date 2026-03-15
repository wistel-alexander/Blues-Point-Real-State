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
    "Stamford,CT",
    "Norwalk,CT",
    "Darien,CT",
    "Wilton,CT",
    "New_Canaan,CT"
]

BASE_URL = "https://www.trulia.com/for_sale/{}/fsbo_lt/"

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
# CAPTCHA
# ================================

def captcha_detected(driver):

    page = driver.page_source.lower()

    triggers = ["captcha", "verify you are human", "security check"]

    return any(t in page for t in triggers)


# ================================
# DETECT LAST PAGE
# ================================

def nearby_section_detected(driver):

    page = driver.page_source.lower()

    triggers = [
        "homes for sale near",
        "matching your filters just outside"
    ]

    return any(t in page for t in triggers)


# ================================
# COLLECT LINKS
# ================================

def collect_links(driver):

    cards = driver.find_elements(
        By.CSS_SELECTOR,
        "[data-testid='property-card-link']"
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
# CLEAN PRICE
# ================================

def extract_price(price_text):

    match = re.search(r"\$\d[\d,]*", price_text)

    if match:
        return match.group()

    return ""


# ================================
# EXTRACT DATE
# ================================

def extract_date(text):

    match = re.search(r'on (\w+ \d{1,2}, \d{4})', text)

    if match:

        raw_date = match.group(1)

        date_obj = datetime.strptime(raw_date, "%b %d, %Y")

        return date_obj.strftime("%m/%d/%Y")

    return ""


# ================================
# SCRAPE PROPERTY
# ================================

def scrape_property(driver, link, city):

    try:

        driver.get(link)

        time.sleep(random.uniform(5,9))

        if captcha_detected(driver):

            input("Solve CAPTCHA then press ENTER")


        # ================================
        # OWNER PHONE (MAIN CRITERIA)
        # ================================

        try:

            phone_element = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='owner-phone']"
            )

            phone = phone_element.text.replace("Owner Phone:", "").strip()

        except:
            print("No owner phone detected → skipping")
            return None


        # ================================
        # ADDRESS
        # ================================

        address = ""

        try:

            address = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='home-details-summary-headline']"
            ).text

        except:
            pass


        # ================================
        # PRICE
        # ================================

        price = ""

        try:

            price_text = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='home-details-summary-price']"
            ).text

            price = extract_price(price_text)

        except:
            pass


        # ================================
        # DATE POSTED
        # ================================

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

        return data

    except Exception as e:

        print("Error scraping:", e)

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

                url = f"https://www.trulia.com/for_sale/{city}/fsbo_lt/{page}_p/"

            print("Opening:", url)

            driver.get(url)

            time.sleep(random.uniform(6,10))


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

                time.sleep(random.uniform(4,8))


            if nearby_section_detected(driver):

                print("LAST PAGE DETECTED")

                break


            page += 1


    driver.quit()

    print("\nSCRAPING FINISHED")


# ================================
# RUN
# ================================

if __name__ == "__main__":

    scrape_trulia()