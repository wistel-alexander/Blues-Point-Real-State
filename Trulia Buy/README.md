# Trulia Buy Scraper

A web scraper for collecting real estate listing data from Trulia.com for properties **for sale** in Connecticut cities.

## Overview

This project scrapes residential property listings from Trulia.com, specifically targeting cities in Connecticut including:
- Stamford, CT
- Norwalk, CT
- Darien, CT
- Wilton, CT
- New Canaan, CT

The scraper extracts property details and saves them to a CSV file for analysis and market research.

## Features

- 🔄 **Automated Scraping**: Uses Selenium with undetected-chromedriver to bypass anti-bot detection
- 🛡️ **Anti-Detection**: Implements CAPTCHA detection and handling
- 📊 **Data Export**: Saves collected listings to CSV format
- 🔗 **Link Tracking**: Maintains a log of visited links to avoid duplicates
- ⏱️ **Rate Limiting**: Includes random delays to respect server resources

## Requirements

- Python 3.7+
- undetected-chromedriver
- selenium
- pandas

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the scraper:
```bash
python trulia_scraper_buy.py
```

The script will:
1. Initialize a Chrome driver with anti-detection settings
2. Scrape listings from specified cities
3. Save data to `trulia_buy_data.csv`
4. Track visited links in `visited_links_buy.csv`

## Output Files

- **trulia_buy_data.csv**: Contains all scraped property listings with details
- **visited_links_buy.csv**: Tracks URLs that have been scraped to prevent duplicates

## Configuration

Edit the following variables in the script to customize behavior:

```python
cities = ["Stamford,CT", "Norwalk,CT", ...]  # Target cities
MAX_PAGES = 20  # Maximum pages to scrape per city
BASE_URL = "https://www.trulia.com/for_sale/{}/"  # Trulia URL format
```

## Notes

- ⚠️ Respect Trulia's Terms of Service and robots.txt
- 🔍 Use responsibly with appropriate delays between requests
- 🚨 This tool is designed for educational and research purposes

## License

This project is provided as-is for educational purposes.

## Disclaimer

Web scraping may violate the terms of service of the target website. Use this tool responsibly and ensure compliance with applicable laws and website policies.
