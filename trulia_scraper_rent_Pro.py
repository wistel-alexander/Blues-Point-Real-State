import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random
import os


cities = [
    "Stamford,CT",
    "Norwalk,CT",
    "Darien,CT",
    "Wilton,CT",
    "New_Canaan,CT"
]

BASE_URL = "https://www.trulia.com/for_rent/{}/3000p_price/"

OUTPUT_FILE = "trulia_rent_data.csv"
VISITED_FILE = "visited_links.csv"


def start_driver():

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=options, version_main=145)

    driver.maximize_window()

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


def wait_for_listings(driver):

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "a[data-testid='property-card-link']")
        )
    )


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


def next_page_exists(driver):

    try:

        driver.find_element(
            By.CSS_SELECTOR,
            "button[aria-label='Next page']"
        )

        return True

    except:

        return False


def scrape_property(driver, link, city):

    try:

        driver.get(link)

        time.sleep(random.uniform(4,7))

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
            price = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='on-market-price-details']"
            ).text
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

        data = {

            "Address": address,
            "City": city.split(",")[0],
            "URL Link": link,
            "Phone Number": phone,
            "Email": "",
            "Name of Person": owner_name,
            "Source": "Trulia",
            "Date Posted": "",
            "Rental / Buy": "Rent",
            "Price Point": price

        }

        return data

    except:

        return None


def scrape_trulia():

    driver = start_driver()

    visited_links = load_visited_links()

    for city in cities:

        print("\nCITY:", city)

        page = 1

        while True:

            if page == 1:

                url = BASE_URL.format(city)

            else:

                url = f"https://www.trulia.com/for_rent/{city}/3000p_price/{page}_p/"

            print("Opening:", url)

            driver.get(url)

            wait_for_listings(driver)

            if captcha_detected(driver):

                input("Solve CAPTCHA then press ENTER")

            links = collect_links(driver, city)

            print("Listings:", len(links))

            for link in links:

                if link in visited_links:
                    continue

                print("Property:", link)

                data = scrape_property(driver, link, city)

                visited_links.add(link)

                save_visited_link(link)

                if data:

                    save_property(data)

                    print("Saved")

                time.sleep(random.uniform(3,6))

            if not next_page_exists(driver):

                print("Last page reached")

                break

            page += 1

            time.sleep(random.uniform(5,8))

    driver.quit()


if __name__ == "__main__":

    scrape_trulia()