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
    "New_Canaan,CT"
]

BASE_URL = "https://www.trulia.com/for_sale/{}/fsbo_lt/"

OUTPUT_FILE = "trulia_buy_data.csv"
VISITED_FILE = "visited_links_buy.csv"

MAX_PAGES = 20


def start_driver():

    options = uc.ChromeOptions()

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")

    driver = uc.Chrome(options=options, version_main=145)

    return driver


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


def captcha_detected(driver):

    page = driver.page_source.lower()

    words = ["captcha", "verify you are human", "security check"]

    return any(w in page for w in words)


def collect_links(driver, city):

    city_slug = city.lower().replace(",", "-").replace("_", "-")

    links = driver.find_elements(
        By.CSS_SELECTOR,
        "a[data-testid='property-card-link']"
    )

    urls = []

    for link in links:

        href = link.get_attribute("href")

        if href:

            href = href.split("?")[0].lower()

            if city_slug in href:

                urls.append(href)

    return list(set(urls))


def extract_price(price_text):

    match = re.search(r"\$\d[\d,]*", price_text)

    if match:
        return match.group()

    return ""


def extract_date(seo_text):

    match = re.search(r'on (\w+ \d{1,2}, \d{4})', seo_text)

    if match:

        raw_date = match.group(1)

        date_obj = datetime.strptime(raw_date, "%b %d, %Y")

        return date_obj.strftime("%m/%d/%Y")

    return ""


def scrape_property(driver, link, city):

    try:

        driver.get(link)

        time.sleep(random.uniform(6,10))

        if captcha_detected(driver):

            input("Solve CAPTCHA then press ENTER")

        try:

            owner_type = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='provider-title']"
            ).text

            if "Property Owner" not in owner_type:
                return None

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
                "[data-testid='home-details-summary-price']"
            ).text

            price = extract_price(price_text)

        except:
            pass


        owner_name = ""

        try:

            owner_name = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='owner-name']"
            ).text

        except:
            pass


        phone = ""

        try:

            phone = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='owner-phone']"
            ).text

            phone = phone.replace("Owner Phone:", "").strip()

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
            "Name of Person": owner_name,
            "Source": "Trulia",
            "Date Posted": date_posted,
            "Rental / Buy": "Buy",
            "Price Point": price

        }

        return data

    except Exception as e:

        print("Error:", e)

        return None


def scrape_trulia():

    print("TRULIA BUY SCRAPER STARTED")

    driver = start_driver()

    visited_links = load_visited_links()

    print("Visited links loaded:", len(visited_links))


    for city in cities:

        print("===================================")
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


            links = collect_links(driver, city)

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

                    print("Saved")


                time.sleep(random.uniform(5,9))


            page += 1


    driver.quit()

    print("SCRAPING FINISHED")


if __name__ == "__main__":

    scrape_trulia()