import time
import random
import csv
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =============================
# CONFIG
# =============================

CITIES = [
    "Stamford",
    "Norwalk",
    "Darien",
    "Wilton",
    "New_Canaan"
]

BASE_URL = "https://www.trulia.com/for_rent/{},CT/3000p_price/"

MAX_PAGES = 10

OUTPUT_FILE = "trulia_rent_links.csv"


# =============================
# DRIVER
# =============================

def start_driver():

    print("Starting undetected Chrome driver...")

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = uc.Chrome(
        options=options,
        version_main=145
    )

    return driver


# =============================
# CAPTCHA
# =============================

def wait_for_captcha():

    print("\nIf a CAPTCHA appears solve it.")
    input("Press ENTER when ready...")


# =============================
# WAIT FOR LISTINGS
# =============================

def wait_for_listings(driver):

    try:

        WebDriverWait(driver, 25).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//a[contains(@href,'/home/')]")
            )
        )

        time.sleep(random.uniform(4,6))

    except:

        print("Listings did not fully load")


# =============================
# COLLECT LINKS
# =============================

def collect_links(driver):

    elements = driver.find_elements(
        By.XPATH,
        "//a[contains(@href,'/home/')]"
    )

    links = set()

    for el in elements:

        link = el.get_attribute("href")

        if link:

            clean = link.split("?")[0]

            if "/home/" in clean:

                links.add(clean)

    return list(links)


# =============================
# NEXT PAGE
# =============================

def go_next_page(driver, page):

    try:

        button = driver.find_element(
            By.XPATH,
            f"//span[@aria-label='Page {page+1}']"
        )

        driver.execute_script(
            "arguments[0].click();",
            button
        )

        print(f"Moving to Page {page+1}")

        time.sleep(random.uniform(7,10))

        return True

    except:

        print("No more pages")

        return False


# =============================
# MAIN SCRAPER
# =============================

def scrape():

    driver = start_driver()

    all_links = set()

    for city in CITIES:

        print("\n==============================")
        print("CITY:", city + ",CT")
        print("==============================")

        url = BASE_URL.format(city)

        driver.get(url)

        wait_for_captcha()

        page = 1

        while page <= MAX_PAGES:

            print("\nOpening page:", page)

            wait_for_listings(driver)

            links = collect_links(driver)

            print("Links detected:", len(links))

            new_links = 0

            for link in links:

                if link not in all_links:

                    all_links.add(link)

                    new_links += 1

                    print("Collected:", link)

            print("New links:", new_links)

            moved = go_next_page(driver, page)

            if not moved:
                break

            page += 1

    print("\n==============================")
    print("SCRAPING FINISHED")
    print("Total links:", len(all_links))
    print("==============================")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow(["URL"])

        for link in all_links:

            writer.writerow([link])

    print("CSV saved:", OUTPUT_FILE)

    try:
        driver.quit()
    except:
        pass


# =============================
# RUN
# =============================

if __name__ == "__main__":

    print("\n==============================")
    print("TRULIA RENT SCRAPER STARTED")
    print("==============================")

    scrape()