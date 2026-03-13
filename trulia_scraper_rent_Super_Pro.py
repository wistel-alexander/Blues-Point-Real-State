import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import pandas as pd
import time
import random
import re
import os


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
LINKS_FILE = "trulia_rent_links_master.csv"


# =====================================
# DRIVER
# =====================================

def start_driver():

    options = uc.ChromeOptions()

    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=options, version_main=145)

    driver.execute_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )

    return driver


# =====================================
# CAPTCHA
# =====================================

def captcha_detected(driver):

    page = driver.page_source.lower()

    triggers = [
        "captcha",
        "verify you are human",
        "security check",
        "robot"
    ]

    return any(t in page for t in triggers)


# =====================================
# SAFE FIND
# =====================================

def safe_find_multiple(driver, selectors):

    for selector in selectors:

        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            txt = el.text.strip()

            if txt:
                return txt

        except:
            pass

    return ""


# =====================================
# DETECT NEARBY
# =====================================

def nearby_section_detected(driver):

    try:

        driver.find_element(
            By.XPATH,
            "//p[contains(text(),'Apartments For Rent Near')]"
        )

        return True

    except:

        return False


# =====================================
# EXTRACT LINKS FROM CARDS ONLY
# =====================================

def collect_card_links(driver, city):

    cards = driver.find_elements(
        By.XPATH,
        "//article//a[contains(@href,'/home/')]"
    )

    links = []

    city_slug = city.lower().replace(",","-").replace("_","-")

    for card in cards:

        try:

            link = card.get_attribute("href")

            if link:

                link = link.split("?")[0]

                if city_slug in link.lower():

                    links.append(link)

        except:
            pass

    return list(set(links))


# =====================================
# LOAD EXISTING LINKS
# =====================================

def load_existing_links():

    if not os.path.exists(LINKS_FILE):

        return set()

    df = pd.read_csv(LINKS_FILE)

    return set(df["URL"].tolist())


# =====================================
# SAVE MASTER LINKS
# =====================================

def save_links_master(links):

    df = pd.DataFrame(list(links), columns=["URL"])

    df.to_csv(LINKS_FILE,index=False)


# =====================================
# SCRAPER
# =====================================

def scrape():

    print("\nTRULIA RENT SCRAPER PRO\n")

    driver = start_driver()

    visited_links = load_existing_links()

    print("Existing links loaded:",len(visited_links))

    all_data = []

    new_links_global = set()


    for city in cities:

        print("\n====================")
        print("CITY:",city)
        print("====================")

        driver.get(BASE_URL.format(city))

        time.sleep(6)

        if captcha_detected(driver):

            input("Solve CAPTCHA then press ENTER")


        page = 1

        while True:

            print("\nReading page:",page)

            print("\nSCROLL MANUALLY until all cards load.")
            input("Then press ENTER to extract card links...")

            if nearby_section_detected(driver):

                print("Nearby listings detected → stopping page")
                break


            links = collect_card_links(driver, city)

            print("Cards detected:",len(links))


            for link in links:

                if link not in visited_links:

                    visited_links.add(link)
                    new_links_global.add(link)

                    print("NEW:",link)


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

                time.sleep(random.uniform(5,8))

            except:

                print("No more pages")
                break


    save_links_master(visited_links)

    print("\nNew links collected:",len(new_links_global))


    # =====================================
    # OPEN PROPERTY PAGES
    # =====================================

    for link in new_links_global:

        print("\nOpening:",link)

        try:

            driver.get(link)

            time.sleep(random.uniform(5,7))

            if captcha_detected(driver):

                input("Solve CAPTCHA then press ENTER")


            try:

                provider = driver.find_element(
                    By.CSS_SELECTOR,
                    "[data-testid='provider-title']"
                ).text

                if "Property Owner" not in provider:

                    print("Skipped (agent)")
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


            description = safe_find_multiple(driver,[
                "[data-testid='seo-description-paragraph']"
            ])


            date_posted = ""

            match = re.search(r"listed on (.*)",description)

            if match:
                date_posted = match.group(1)


            row = {

                "Address":address,
                "City":city,
                "URL Link":link,
                "Phone Number":phone,
                "Email":"",
                "Name of Person":"",
                "Source":"Trulia",
                "Date Posted":date_posted,
                "Rental / Buy":"Rent",
                "Price Point":price

            }

            all_data.append(row)

            print("Saved")


        except Exception as e:

            print("Error:",e)


    try:
        driver.quit()
    except:
        pass


    df = pd.DataFrame(all_data)

    df.to_csv(OUTPUT_FILE,index=False)

    print("\nData saved:",OUTPUT_FILE)



# =====================================
# RUN
# =====================================

if __name__ == "__main__":

    scrape()