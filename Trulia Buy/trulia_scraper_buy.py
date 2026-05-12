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


def start_driver():

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")

    driver = uc.Chrome(options=options, version_main=148)

    return driver


# ---------------- CAPTCHA DETECTION ---------------- #

def captcha_present(driver):

    page = driver.page_source.lower()

    triggers = [
        "px-captcha",
        "press & hold",
        "verify you are human",
        "confirme que es humano",
        "amzn-captcha"
    ]

    return any(t in page for t in triggers)


def wait_for_captcha(driver):

    if captcha_present(driver):

        print("\nCAPTCHA DETECTED - solve manually")

        while captcha_present(driver):

            print("Waiting for captcha to be solved...")
            time.sleep(5)

        print("Captcha solved\n")


# --------------------------------------------------- #


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


def save_property(data):

    df = pd.DataFrame([data])

    if not os.path.exists(OUTPUT_FILE):

        df.to_csv(OUTPUT_FILE, index=False)

    else:

        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)


def collect_links(driver, city):

    city_slug = city.lower().replace(" ", "-").replace(",", "-")

    cards = driver.find_elements(
        By.CSS_SELECTOR,
        "[data-testid='home-card-sale']"
    )

    urls = []

    for card in cards:

        try:
            # -------------------------------
            # 🔴 DETECTAR "COMING SOON"
            # -------------------------------
            tags = card.find_elements(
                By.CSS_SELECTOR,
                "[data-testid^='property-tag']"
            )

            is_coming_soon = False

            for tag in tags:
                if "coming soon" in tag.text.lower():
                    is_coming_soon = True
                    break

            if is_coming_soon:
                print("Skipping COMING SOON property")
                continue

            # -------------------------------
            # 🔗 EXTRAER LINK
            # -------------------------------
            link_element = card.find_element(
                By.CSS_SELECTOR,
                "a[data-testid='property-card-link']"
            )

            href = link_element.get_attribute("href")

            if href:

                href = href.split("?")[0].lower()

                if city_slug.split("-")[0] in href:
                    urls.append(href)

        except Exception as e:
            print("Error processing card:", e)
            continue

    return list(dict.fromkeys(urls))


def has_next_page(driver):

    try:

        driver.find_element(
            By.CSS_SELECTOR,
            "[data-testid='pagination-next-page']"
        )

        return True

    except:

        return False


def extract_price(text):

    match = re.search(r"\$\d[\d,]*", text)

    if match:
        return match.group()

    return ""


def extract_date(text):

    match = re.search(r'on (\w+ \d{1,2}, \d{4})', text)

    if match:

        raw_date = match.group(1)

        date_obj = datetime.strptime(raw_date, "%b %d, %Y")

        return date_obj.strftime("%m/%d/%Y")

    return ""


def scrape_property(driver, link, city):

    try:

        driver.get(link)

        time.sleep(random.uniform(5,8))

        wait_for_captcha(driver)

        try:

            phone = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='owner-phone']"
            ).text

            phone = phone.replace("Owner Phone:", "").strip()

        except:

            return None


        address1 = ""
        address2 = ""

        try:

            address1 = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='home-details-summary-headline']"
            ).text

        except:
            pass


        try:

            address2 = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='home-details-summary-city-state']"
            ).text

        except:
            pass


        address = f"{address1}, {address2}"


        price = ""

        try:

            price_text = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='on-market-price-details']"
            ).text

            price = extract_price(price_text)

        except:
            pass


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

        print("Error:", e)

        return None


def build_city_url(city, page):

    if city in SPECIAL_CITY_URLS:

        base = SPECIAL_CITY_URLS[city]

        if page == 1:
            return base
        else:
            return base + f"{page}_p/"

    else:

        if page == 1:
            return BASE_URL.format(city)
        else:
            return f"https://www.trulia.com/for_sale/{city}/{page}_p/"


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

            url = build_city_url(city, page)

            print("\nOpening:", url)

            driver.get(url)

            time.sleep(random.uniform(5,8))

            wait_for_captcha(driver)


            input(
                "\nScroll manually until listings load\n"
                "Press ENTER when ready..."
            )


            links = collect_links(driver, city)

            print("Listings found:", len(links))


            if len(links) == 0:

                print("No listings found — stopping city.")
                break


            next_page = has_next_page(driver)


            for link in links:

                if link in visited_links:
                    continue

                print("Scraping:", link)

                data = scrape_property(driver, link, city)

                visited_links.add(link)

                save_visited_link(link)

                if data:

                    save_property(data)

                    print("Saved")

                time.sleep(random.uniform(4,7))


            if not next_page:

                print("LAST PAGE OF CITY")
                break


            page += 1


    driver.quit()

    print("\nSCRAPING FINISHED")


if __name__ == "__main__":

    scrape_trulia()