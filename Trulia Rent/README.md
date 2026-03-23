# Trulia Rent Scraper

A web scraper for collecting real estate rental listing data from Trulia.com for properties **for rent** in Connecticut cities.

## Overview

This project scrapes residential rental property listings from Trulia.com, specifically targeting cities in Connecticut including:
- Stamford, CT
- Norwalk, CT
- Darien, CT
- Wilton, CT
- New Canaan, CT

The scraper extracts rental property details and saves them to a CSV file for market analysis and research purposes.

## Features

- 🔄 **Automated Scraping**: Uses Selenium with undetected-chromedriver to bypass anti-bot detection
- 🛡️ **Anti-Detection**: Implements CAPTCHA detection and handling
- 💰 **Price Filtering**: Focuses on rentals with $3000+ price range
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
python trulia_scraper_rent.py
```

The script will:
1. Initialize a Chrome driver with anti-detection settings
2. Scrape rental listings from specified cities
3. Save data to `trulia_rent_data.csv`
4. Track visited links in `visited_links.csv`

## Output Files

- **trulia_rent_data.csv**: Contains all scraped rental property listings with details
- **visited_links.csv**: Tracks URLs that have been scraped to prevent duplicates

## Configuration

Edit the following variables in the script to customize behavior:

```python
cities = ["Stamford,CT", "Norwalk,CT", ...]  # Target cities
MAX_PAGES = 20  # Maximum pages to scrape per city
BASE_URL = "https://www.trulia.com/for_rent/{}/3000p_price/"  # Trulia URL format (3000+ price)
```

## Notes

- ⚠️ Respect Trulia's Terms of Service and robots.txt
- 🔍 Use responsibly with appropriate delays between requests
- 💵 Currently filtered for rentals $3000 per month and above
- 🚨 This tool is designed for educational and research purposes

## License

This project is provided as-is for educational purposes.

## Disclaimer

Web scraping may violate the terms of service of the target website. Use this tool responsibly and ensure compliance with applicable laws and website policies.
