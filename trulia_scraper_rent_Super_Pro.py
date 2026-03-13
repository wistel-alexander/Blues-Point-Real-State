import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import time
import random
import re


# =====================================
# CONFIG
# =====================================

cities = [
    "Stamford,CT",
    "Norwalk,CT",
    "Darien,CT",
    "Wilton,CT",
    "New_Canaan,CT"
]

BASE_URL = "https://www.trulia.com/for_rent/{}/3000p_price/"

OUTPUT_FILE = "trulia_rent_data.csv"


# =====================================
# DRIVER
# =====================================

def start_driver():

    print("\nStarting undetected Chrome driver...\n")

    options = uc.ChromeOptions()

    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=options, version_main=145)

    driver.maximize_window()

    return driver


# =====================================
# CAPTCHA DETECTION
# =====================================

def captcha_detected(driver):

    page = driver.page_source.lower()

    words = ["captcha","verify you are human","security check"]

    return any(w in page for w in words)


# =====================================
# SAFE FIND
# =====================================

def safe_find_multiple(driver, selectors):

    for selector in selectors:

        try:

            element = driver.find_element(By.CSS_SELECTOR, selector)

            text = element.text.strip()

            if text:
                return text

        except:
            pass

    return ""


# =====================================
# COLLECT PROPERTY LINKS
# =====================================

def collect_links(driver):

    links = []

    cards = driver.find_elements(
        By.XPATH,
        "//a[contains(@href,'/home/')]"
    )

    for card in cards:

        try:

            link = card.get_attribute("href")

            if link and "/home/" in link:

                link = link.split("?")[0]

                links.append(link)

        except:
            pass

    return list(set(links))


# =====================================
# MAIN SCRAPER
# =====================================

def scrape_trulia():

    print("\n==============================")
    print("TRULIA RENT SCRAPER STARTED")
    print("==============================")

    driver = start_driver()

    wait = WebDriverWait(driver,30)

    all_data = []

    visited_links = set()

    property_counter = 0


    for city in cities:

        print("\n==============================")
        print("CITY:", city)
        print("==============================")

        url = BASE_URL.format(city)

        driver.get(url)

        time.sleep(6)

        if captcha_detected(driver):

            print("\n⚠ CAPTCHA DETECTED")
            input("Solve captcha then press ENTER")


        page = 1

        property_links = []


        while True:

            print("\nReading page:", page)

            # WAIT UNTIL ANY PROPERTY LINK EXISTS
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH,"//a[contains(@href,'/home/')]")
                )
            )

            print("\n👇 SCROLL MANUALLY to load all cards")
            input("When finished scrolling press ENTER...")


            links = collect_links(driver)

            print("Links extracted:", len(links))


            for link in links:

                if link not in visited_links:

                    visited_links.add(link)

                    property_links.append(link)

                    print("Collected:", link)


            try:

                page += 1

                next_button = driver.find_element(
                    By.XPATH,
                    f"//span[@aria-label='Page {page}']"
                )

                driver.execute_script(
                    "arguments[0].click();",
                    next_button
                )

                print("\n➡ Moving to page", page)

                time.sleep(7)

            except:

                print("No more pages")

                break


        print("Total links collected:", len(property_links))


        # =================================
        # VISIT EACH PROPERTY
        # =================================

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

                    print("⚠ CAPTCHA detected")
                    input("Solve captcha then press ENTER")


                try:

                    owner = driver.find_element(
                        By.CSS_SELECTOR,
                        "[data-testid='provider-title']"
                    ).text

                    if "Property Owner" not in owner:

                        print("Skipped (not property owner)")
                        continue

                except:

                    print("Provider not found")
                    continue


                address = safe_find_multiple(driver,[

                    "[data-testid='home-details-summary-headline']",
                    "h1"

                ])


                price = safe_find_multiple(driver,[

                    "[data-testid='home-details-summary-price']"

                ])


                phone = safe_find_multiple(driver,[

                    "[data-testid='owner-phone']"

                ])

                phone = phone.replace("Owner Phone:","").strip()


                description = safe_find_multiple(driver,[

                    "[data-testid='seo-description-paragraph']"

                ])


                date_posted = ""

                match = re.search(r"listed on (.*)", description)

                if match:
                    date_posted = match.group(1)


                row = {

                    "Address": address,
                    "City": city.split(",")[0],
                    "URL Link": link,
                    "Phone Number": phone,
                    "Email": "",
                    "Name of Person": "",
                    "Source": "Trulia",
                    "Date Posted": date_posted,
                    "Rental / Buy": "Rent",
                    "Price Point": price

                }

                all_data.append(row)

                print("Saved")


            except Exception as e:

                print("Error:", e)

            time.sleep(random.uniform(3,5))


    driver.quit()

    df = pd.DataFrame(all_data)

    df.to_csv(OUTPUT_FILE,index=False)

    print("\nCSV saved:", OUTPUT_FILE)


# =====================================
# RUN
# =====================================

if __name__ == "__main__":

    scrape_trulia()