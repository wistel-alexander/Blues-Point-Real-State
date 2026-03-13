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
# AUTO SCROLL (LOAD ALL CARDS)
# =====================================

def auto_scroll(driver):

    last_height = driver.execute_script(
        "return document.body.scrollHeight"
    )

    while True:

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

        time.sleep(2)

        new_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

        if new_height == last_height:
            break

        last_height = new_height


# =====================================
# CHECK NEARBY TEXT
# =====================================

def reached_nearby_section(driver, city):

    city_name = city.split(",")[0]

    page_text = driver.page_source.lower()

    check_text = f"apartments for rent near {city_name.lower()}"

    return check_text in page_text


# =====================================
# COLLECT LINKS
# =====================================

def collect_links(driver, city):

    links = []

    cards = driver.find_elements(
        By.XPATH,
        "//a[contains(@href,'/home/')]"
    )

    city_name = city.split(",")[0].lower()

    for card in cards:

        try:

            link = card.get_attribute("href")

            if not link:
                continue

            link = link.split("?")[0]

            # filter city
            if city_name.replace("_","-") not in link.lower():
                continue

            links.append(link)

        except:
            pass

    return list(set(links))


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
# MAIN SCRAPER
# =====================================

def scrape_trulia():

    print("\nTRULIA RENT SCRAPER STARTED\n")

    driver = start_driver()

    wait = WebDriverWait(driver,30)

    all_data = []

    visited_links = set()

    property_counter = 0


    for city in cities:

        print("\n=======================")
        print("CITY:",city)
        print("=======================\n")

        url = BASE_URL.format(city)

        driver.get(url)

        time.sleep(6)

        if captcha_detected(driver):

            input("Solve CAPTCHA then press ENTER")


        page = 1

        property_links = []


        while True:

            print("\nReading page:",page)

            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH,"//a[contains(@href,'/home/')]")
                )
            )

            print("Auto scrolling to load all listings...")

            auto_scroll(driver)

            print("Manual scroll if needed...")

            input("Press ENTER when listings finished loading")


            # stop if nearby listings appear
            if reached_nearby_section(driver, city):

                print("Nearby listings detected -> stopping city scraping")

                break


            links = collect_links(driver, city)

            print("Links found:",len(links))


            for link in links:

                if link not in visited_links:

                    visited_links.add(link)

                    property_links.append(link)

                    print("Collected:",link)


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

                print("\nMoving to page",page)

                time.sleep(6)

            except:

                print("No more pages")

                break


        print("\nTotal property links:",len(property_links))


        # =====================================
        # VISIT PROPERTIES
        # =====================================

        for link in property_links:

            property_counter += 1

            print("\nPROPERTY:",property_counter)
            print(link)

            try:

                driver.get(link)

                time.sleep(random.uniform(5,8))

                if captcha_detected(driver):

                    input("Solve CAPTCHA then press ENTER")


                try:

                    owner = driver.find_element(
                        By.CSS_SELECTOR,
                        "[data-testid='provider-title']"
                    ).text

                    if "Property Owner" not in owner:

                        print("Skipped (agent listing)")
                        continue

                except:

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


                row = {

                    "Address":address,
                    "City":city.split(",")[0],
                    "URL Link":link,
                    "Phone Number":phone,
                    "Email":"",
                    "Name of Person":"",
                    "Source":"Trulia",
                    "Date Posted":"",
                    "Rental / Buy":"Rent",
                    "Price Point":price

                }

                all_data.append(row)

                print("Saved")


            except Exception as e:

                print("Error:",e)

            time.sleep(random.uniform(3,5))


    driver.quit()

    df = pd.DataFrame(all_data)

    df.to_csv(OUTPUT_FILE,index=False)

    print("\nCSV saved:",OUTPUT_FILE)



# =====================================
# RUN
# =====================================

if __name__ == "__main__":

    scrape_trulia()