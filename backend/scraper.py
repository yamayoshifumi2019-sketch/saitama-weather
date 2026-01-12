"""
Weather Data Scraper for Saitama
Scrapes current weather observation from weathernews.jp and stores it in Supabase
Runs continuously with 10-minute intervals
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime

# Weather data URL
WEATHER_URL = "https://weathernews.jp/onebox/tenki/saitama/11100/"

# Interval between scrapes (in seconds)
SCRAPE_INTERVAL = 600  # 10 minutes


def get_supabase_client() -> Client:
    """Create and return Supabase client"""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    return create_client(url, key)


def scrape_weather_data() -> dict:
    """
    Scrape CURRENT/REAL-TIME temperature, wind speed, and precipitation
    from weathernews.jp observation section (実況天気).
    Uses class names: observedValue, obs_block, obs_content
    Returns a dictionary with numeric values only.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
    }

    response = requests.get(WEATHER_URL, headers=headers)
    response.raise_for_status()

    # Decode with proper encoding
    response.encoding = 'utf-8'
    html_content = response.text

    soup = BeautifulSoup(html_content, "html.parser")

    # Initialize default values
    temperature = "N/A"
    wind = "N/A"
    precipitation = "0"
    observation_time = None

    # Get current date for constructing timestamp (JST)
    today = datetime.now()

    # Find the current observation section using class names
    # The observation section uses classes: observedValue, obs_block, obs_content
    obs_section = soup.find(class_='observedValue')

    if obs_section:
        obs_text = obs_section.get_text()

        # Normalize minus signs: replace Unicode minus (U+2212), en-dash (U+2013),
        # fullwidth minus (U+FF0D) with regular hyphen-minus (U+002D)
        obs_text = obs_text.replace('\u2212', '-').replace('\u2013', '-').replace('\uff0d', '-')

        # Extract observation time - look for pattern like "22:40時点" (JST)
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*時点', obs_text)
        if time_match:
            obs_hour = int(time_match.group(1))
            obs_minute = int(time_match.group(2))
            # Construct datetime with observation time (JST)
            observation_time = today.replace(hour=obs_hour, minute=obs_minute, second=0, microsecond=0)

        # Extract temperature - look for number after "気温"
        # Use [^\d-]* to not consume the minus sign for negative temperatures
        temp_match = re.search(r'気温[^\d-]*(-?\d+\.?\d*)', obs_text)
        if temp_match:
            temperature = temp_match.group(1)
        else:
            # Fallback: find first decimal number in observation section
            temp_match = re.search(r'(-?\d+\.\d+)', obs_text)
            if temp_match:
                temperature = temp_match.group(1)

        # Extract wind speed - look for number before "m/s"
        wind_match = re.search(r'(\d+\.?\d*)\s*m/s', obs_text)
        if wind_match:
            wind = wind_match.group(1)

    # Method 2: Try individual obs_block elements if Method 1 didn't work
    if temperature == "N/A":
        obs_blocks = soup.find_all(class_='obs_block')
        for block in obs_blocks:
            block_text = block.get_text()
            # Normalize minus signs
            block_text = block_text.replace('\u2212', '-').replace('\u2013', '-').replace('\uff0d', '-')

            if '気温' in block_text:
                temp_match = re.search(r'(-?\d+\.?\d*)', block_text)
                if temp_match:
                    temperature = temp_match.group(1)

            if '風' in block_text or 'm/s' in block_text:
                wind_match = re.search(r'(\d+\.?\d*)\s*m', block_text)
                if wind_match:
                    wind = wind_match.group(1)

    # Find precipitation
    precip_pattern = re.compile(r'(\d+\.?\d*)\s*ミリ')
    precip_matches = precip_pattern.findall(html_content)
    if precip_matches:
        precipitation = precip_matches[0]

    # Use observation time (JST) if found, otherwise use current time
    if observation_time:
        timestamp = observation_time.isoformat()
    else:
        timestamp = datetime.now().isoformat()

    return {
        "temperature": temperature,
        "wind": wind,
        "precipitation": precipitation,
        "created_at": timestamp
    }


def check_duplicate(timestamp: str) -> bool:
    """Check if data with the same observation time already exists"""
    supabase = get_supabase_client()
    result = supabase.table("weather_saitama").select("id").eq("created_at", timestamp).execute()
    return len(result.data) > 0


def insert_weather_data(data: dict) -> dict:
    """Insert weather data into Supabase table 'weather_saitama'"""
    supabase = get_supabase_client()
    result = supabase.table("weather_saitama").insert({
        "temperature": data["temperature"],
        "wind": data["wind"],
        "precipitation": data["precipitation"],
        "created_at": data["created_at"]
    }).execute()
    return result.data


def main():
    """Main function to run scraper continuously with 10-minute intervals"""
    print("=" * 60)
    print("  Saitama Weather Scraper - Continuous Mode")
    print(f"  Scraping interval: {SCRAPE_INTERVAL // 60} minutes")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    while True:
        try:
            # Fetch weather data
            print("\n" + "-" * 60)
            print(f"Fetching weather data...")

            weather_data = scrape_weather_data()

            print(f"  Temperature: {weather_data['temperature']}°C")
            print(f"  Wind: {weather_data['wind']} m/s")
            print(f"  Precipitation: {weather_data['precipitation']} mm")
            print(f"  Observation Time (JST): {weather_data['created_at']}")

            # Check if Supabase credentials are available
            supabase_url = os.environ.get("SUPABASE_URL", "")
            supabase_key = os.environ.get("SUPABASE_KEY", "")

            if not supabase_url or not supabase_key:
                print("\nWarning: Supabase credentials not set. Skipping database insert.")
            else:
                # Check for duplicate before inserting
                if check_duplicate(weather_data["created_at"]):
                    print(f"\nData for {weather_data['created_at']} already exists. Skipping insert.")
                else:
                    # Insert into Supabase
                    result = insert_weather_data(weather_data)
                    jst_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"\nData successfully saved to Supabase at {jst_timestamp} (JST)")

            print(f"\nWaiting for 10 minutes before next update...")
            print("-" * 60)

            # Wait for 10 minutes before next scrape
            time.sleep(SCRAPE_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nScraper stopped by user. Goodbye!")
            break
        except requests.exceptions.RequestException as e:
            print(f"\nNetwork error: {e}")
            print("Retrying in 10 minutes...")
            time.sleep(SCRAPE_INTERVAL)
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            print("Retrying in 10 minutes...")
            time.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    main()
