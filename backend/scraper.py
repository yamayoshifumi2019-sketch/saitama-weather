"""
Weather Data Scraper for Saitama (GitHub Actions Version)
Scrapes current weather observation and stores it in Supabase.
Runs once and exits (scheduling is handled by GitHub Actions).
"""

import os
import re
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# Japan Standard Time (UTC+9)
JST = timezone(timedelta(hours=9))

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
    """Scrape real-time weather data from weathernews.jp"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    response = requests.get(WEATHER_URL, headers=headers)
    response.raise_for_status()
    response.encoding = 'utf-8'
    
    soup = BeautifulSoup(response.text, "html.parser")

    temperature = "N/A"
    wind = "N/A"
    precipitation = "0"
    observation_time = None
    today = datetime.now(JST)

    obs_section = soup.find(class_='observedValue')
    if obs_section:
        obs_text = obs_section.get_text().replace('\u2212', '-').replace('\u2013', '-').replace('\uff0d', '-')
        
        # 観測時刻の抽出
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*時点', obs_text)
        if time_match:
            obs_hour, obs_min = int(time_match.group(1)), int(time_match.group(2))
            observation_time = today.replace(hour=obs_hour, minute=obs_min, second=0, microsecond=0)
            if obs_hour > today.hour + 12 or observation_time > today + timedelta(minutes=30):
                observation_time -= timedelta(days=1)

        # 気温の抽出
        temp_match = re.search(r'気温[^\d-]*(-?\d+\.?\d*)', obs_text)
        if temp_match: temperature = temp_match.group(1)

        # 風速の抽出
        wind_match = re.search(r'(\d+\.?\d*)\s*m/s', obs_text)
        if wind_match: wind = wind_match.group(1)

    # 降水量の抽出
    precip_matches = re.compile(r'(\d+\.?\d*)\s*ミリ').findall(response.text)
    if precip_matches: precipitation = precip_matches[0]

    timestamp = observation_time.isoformat() if observation_time else datetime.now(JST).isoformat()

    return {
        "temperature": temperature,
        "wind": wind,
        "precipitation": precipitation,
        "created_at": timestamp
    }

def check_duplicate(timestamp: str) -> bool:
    """Check if data already exists"""
    supabase = get_supabase_client()
    result = supabase.table("weather_saitama").select("id").eq("created_at", timestamp).execute()
    return len(result.data) > 0

def insert_weather_data(data: dict):
    """Insert into Supabase"""
    supabase = get_supabase_client()
    supabase.table("weather_saitama").insert({
        "temperature": data["temperature"],
        "wind": data["wind"],
        "precipitation": data["precipitation"],
        "created_at": data["created_at"]
    }).execute()

def main():
    """Execute scraping ONCE and exit"""
    print(f"Starting scrape at {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')} (JST)")
    
    try:
        weather_data = scrape_weather_data()
        print(f"Data found: {weather_data}")

        # Supabaseへの保存
        if check_duplicate(weather_data["created_at"]):
            print(f"Data for {weather_data['created_at']} already exists. Skipping.")
        else:
            insert_weather_data(weather_data)
            print("Successfully saved to Supabase.")
            
    except Exception as e:
        print(f"Error occurred: {e}")
        exit(1) # エラーがあった場合はGitHub Actionsに失敗を通知

if __name__ == "__main__":
    main()
