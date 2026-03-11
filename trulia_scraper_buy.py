import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random
import re


# =====================================
# CONFIGURATION
# =====================================

cities = [
    "Stamford,CT",
    "Norwalk,CT",
    "Darien,CT",
    "Wilton,CT",
    "New_Canaan,CT"
]

BASE_URL = "https://www.trulia.com/for_sale/{}/fsbo_lt/"

OUTPUT_FILE = "trulia_fsbo_data.csv"

MAX_PAGES = 1


# =====================================
# START DRIVER
# =====================================

def start_driver():

    print("\nStarting undetected Chrome driver...\n")

    options = uc.ChromeOptions()

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(
        options=options,
        version_main=145
    )

    driver.set_window_size(1400,900)

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


# =====================================
# CAPTCHA DETECTION
# =====================================

def captcha_detected(driver):

    page = driver.page_source.lower()

    words = [
        "captcha",
        "verify you are human",
        "security check",
        "robot"
    ]

    for w in words:
        if w in page:
            return True

    return False


# =====================================
# SAFE FIND MULTIPLE SELECTORS
# =====================================

def safe_find_multiple(driver, selectors):

    for selector in selectors:

        try:

            element = driver.find_element(By.CSS_SELECTOR, selector)

            text = element.text.strip()

            if text:
                return text

        except:
            continue

    return ""


# =====================================
# SCRAPER
# =====================================

def scrape_trulia():

    print("\n==============================")
    print("TRULIA SCRAPER STARTED")
    print("==============================")

    driver = start_driver()

    wait = WebDriverWait(driver,20)

    all_data = []

    visited_links = set()

    property_counter = 0


    for city in cities:

        print("\n==============================")
        print("CITY:", city)
        print("==============================")


        for page in range(1, MAX_PAGES+1):

            if page == 1:
                url = BASE_URL.format(city)
            else:
                url = BASE_URL.format(city) + f"{page}_p/"

            print("\nOpening page:", page)
            print(url)

            driver.get(url)

            time.sleep(random.uniform(4,7))


            # CAPTCHA CHECK

            if captcha_detected(driver):

                print("\n⚠ CAPTCHA DETECTED")
                print("Solve it manually in the browser.")
                print("Press ENTER here when finished.\n")

                input()


            try:

                wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,"[data-testid='home-card-sale']")
                    )
                )

                print("Listings loaded")

            except:

                print("No listings detected")
                continue


            listings = driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='home-card-sale']"
            )

            print("Listings found:", len(listings))

            property_links = []


            for i,listing in enumerate(listings):

                try:

                    link = listing.find_element(
                        By.CSS_SELECTOR,
                        "a[data-testid='property-card-link']"
                    ).get_attribute("href")


                    if link not in visited_links:

                        visited_links.add(link)

                        property_links.append(link)

                        print("Collected NEW link:", link)

                    else:

                        print("Duplicate skipped")

                except:

                    print("Link extraction failed")


            print("Total NEW links:", len(property_links))


            # =====================================
            # VISIT PROPERTY
            # =====================================

            for link in property_links:

                property_counter += 1

                print("\n--------------------------------")
                print("PROPERTY:", property_counter)
                print(link)
                print("--------------------------------")


                try:

                    driver.get(link)

                    time.sleep(random.uniform(5,8))


                    if captcha_detected(driver):

                        print("\n⚠ CAPTCHA detected on property page")
                        print("Solve it manually then press ENTER")

                        input()


                    # ADDRESS
                    address = safe_find_multiple(driver,[

                        "[data-testid='home-details-summary-headline']",
                        "[data-testid='property-address']",
                        "h1"

                    ])

                    print("Address:", address)


                    # PRICE
                    price = safe_find_multiple(driver,[

                        "[data-testid='home-details-summary-price']",
                        "[data-testid='property-price']"

                    ])

                    print("Price:", price)


                    # PHONE
                    phone = safe_find_multiple(driver,[

                        "[data-testid='owner-phone']"

                    ])

                    phone = phone.replace("Owner Phone:","").strip()

                    print("Phone:", phone)


                    # DESCRIPTION
                    description = safe_find_multiple(driver,[

                        "[data-testid='seo-description-paragraph']"

                    ])


                    date_posted = ""

                    match = re.search(r"listed on (.*)", description)

                    if match:
                        date_posted = match.group(1)

                    print("Date Posted:", date_posted)


                    row = {

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

                    all_data.append(row)

                    print("Data saved")


                except Exception as e:

                    print("Error scraping property:", e)


                time.sleep(random.uniform(3,5))


    driver.quit()


    print("\n==============================")
    print("SCRAPING FINISHED")
    print("Total properties:", len(all_data))
    print("==============================")


    df = pd.DataFrame(all_data)

    df.to_csv(OUTPUT_FILE,index=False)

    print("CSV saved:", OUTPUT_FILE)


# =====================================
# RUN SCRIPT
# =====================================

if __name__ == "__main__":

    scrape_trulia()