"""
Weather Data Scraper for Saitama
Scrapes current weather observation from weathernews.jp and stores it in Supabase
"""

import os
import re
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime

# Weather data URL
WEATHER_URL = "https://weathernews.jp/onebox/tenki/saitama/11100/"


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

    # Get current date for constructing timestamp
    today = datetime.now()
    print(f"Current date: {today.strftime('%Y-%m-%d')}")

    # Find the current observation section using class names
    # The observation section uses classes: observedValue, obs_block, obs_content

    # Method 1: Find the main observation section
    obs_section = soup.find(class_='observedValue')

    if obs_section:
        obs_text = obs_section.get_text()
        print(f"Found observation section")

        # Extract observation time - look for pattern like "22:40時点"
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*時点', obs_text)
        if time_match:
            obs_hour = int(time_match.group(1))
            obs_minute = int(time_match.group(2))
            # Construct datetime with observation time
            observation_time = today.replace(hour=obs_hour, minute=obs_minute, second=0, microsecond=0)
            print(f"Found observation time: {obs_hour}:{obs_minute:02d}")

        # Extract temperature - look for number after "気温"
        # The structure is: 気温 1.6 ℃
        temp_match = re.search(r'気温[^\d]*(-?\d+\.?\d*)', obs_text)
        if temp_match:
            temperature = temp_match.group(1)
            print(f"Found temperature: {temperature}")
        else:
            # Fallback: find first decimal number in observation section
            temp_match = re.search(r'(-?\d+\.\d+)', obs_text)
            if temp_match:
                temperature = temp_match.group(1)
                print(f"Found temperature (fallback): {temperature}")

        # Extract wind speed - look for number before "m/s"
        # The structure is: 風 0.6 m/s
        wind_match = re.search(r'(\d+\.?\d*)\s*m/s', obs_text)
        if wind_match:
            wind = wind_match.group(1)
            print(f"Found wind: {wind}")

    # Method 2: Try individual obs_block elements if Method 1 didn't work
    if temperature == "N/A":
        obs_blocks = soup.find_all(class_='obs_block')
        for block in obs_blocks:
            block_text = block.get_text()

            # Check if this is the temperature block
            if '気温' in block_text:
                temp_match = re.search(r'(-?\d+\.?\d*)', block_text)
                if temp_match:
                    temperature = temp_match.group(1)
                    print(f"Found temperature from obs_block: {temperature}")

            # Check if this is the wind block
            if '風' in block_text or 'm/s' in block_text:
                wind_match = re.search(r'(\d+\.?\d*)\s*m', block_text)
                if wind_match:
                    wind = wind_match.group(1)
                    print(f"Found wind from obs_block: {wind}")

    # Find precipitation from hourly data for current hour
    # The observation section typically doesn't show precipitation directly
    # Look for precipitation in the hourly forecast for current hour
    precip_pattern = re.compile(r'(\d+\.?\d*)\s*ミリ')
    precip_matches = precip_pattern.findall(html_content)
    if precip_matches:
        precipitation = precip_matches[0]
        print(f"Found precipitation: {precipitation}")

    # Use observation time if found, otherwise use current time
    if observation_time:
        timestamp = observation_time.isoformat()
    else:
        timestamp = datetime.now().isoformat()

    print(f"Final values - Temp: {temperature}, Wind: {wind}, Precip: {precipitation}")
    print(f"Observation timestamp: {timestamp}")

    return {
        "temperature": temperature,
        "wind": wind,
        "precipitation": precipitation,
        "created_at": timestamp
    }


def insert_weather_data(data: dict) -> dict:
    """
    Insert weather data into Supabase table 'weather_saitama'
    """
    supabase = get_supabase_client()

    # Insert data into the weather_saitama table
    result = supabase.table("weather_saitama").insert({
        "temperature": data["temperature"],
        "wind": data["wind"],
        "precipitation": data["precipitation"],
        "created_at": data["created_at"]
    }).execute()

    return result.data


def main():
    """Main function to scrape and store weather data"""
    print("Starting weather data scrape...")
    print(f"Fetching data from: {WEATHER_URL}")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Scrape weather data
    weather_data = scrape_weather_data()
    print(f"Scraped data: {weather_data}")

    # Check if Supabase credentials are available
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    if not supabase_url or not supabase_key:
        print("\nWarning: Supabase credentials not set. Skipping database insert.")
        print("Set SUPABASE_URL and SUPABASE_KEY environment variables to enable database storage.")
        return weather_data

    # Insert into Supabase
    try:
        result = insert_weather_data(weather_data)
        print(f"Data inserted successfully: {result}")
    except Exception as e:
        print(f"Error inserting data: {e}")

    return weather_data


if __name__ == "__main__":
    main()
