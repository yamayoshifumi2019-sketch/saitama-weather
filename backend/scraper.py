"""
Weather Data Scraper for Saitama - Ultimate Stable Version
"""

import os
import sys

# ===== 最重要：supabase を import する前に proxy を消す =====
proxy_vars = ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]
# ========================================================

import re
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# 日本標準時 (JST)
JST = timezone(timedelta(hours=9))
WEATHER_URL = "https://weathernews.jp/onebox/tenki/saitama/11100/"

def get_supabase_client() -> Client:
    """Supabaseに接続する"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY is missing in GitHub Secrets.")
        sys.exit(1)

    return create_client(url, key)

def scrape_weather_data() -> dict:
    """さいたま市の最新天気をスクレイピングする"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(WEATHER_URL, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
    except Exception as e:
        print(f"Failed to fetch weather data: {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")

    temperature, wind, precipitation = "N/A", "N/A", "0"
    observation_time = None
    today = datetime.now(JST)

    obs_section = soup.find(class_="observedValue")
    if obs_section:
        obs_text = (
            obs_section.get_text()
            .replace("\u2212", "-")
            .replace("\u2013", "-")
            .replace("\uff0d", "-")
        )

        time_match = re.search(r"(\d{1,2}):(\d{2})\s*時点", obs_text)
        if time_match:
            h, m = int(time_match.group(1)), int(time_match.group(2))
            observation_time = today.replace(hour=h, minute=m, second=0, microsecond=0)
            if h > today.hour + 12:
                observation_time -= timedelta(days=1)

        temp_match = re.search(r"気温[^\d-]*(-?\d+\.?\d*)", obs_text)
        if temp_match:
            temperature = temp_match.group(1)

        wind_match = re.search(r"(\d+\.?\d*)\s*m/s", obs_text)
        if wind_match:
            wind = wind_match.group(1)

    precip_matches = re.findall(r"(\d+\.?\d*)\s*ミリ", response.text)
    if precip_matches:
        precipitation = precip_matches[0]

    ts = observation_time.isoformat() if observation_time else today.isoformat()

    return {
        "temperature": temperature,
        "wind": wind,
        "precipitation": precipitation,
        "created_at": ts,
    }

def main():
    print(f"--- Process started at {datetime.now(JST)} ---")

    weather_data = scrape_weather_data()
    print(f"Fetched Data: {weather_data}")

    try:
        client = get_supabase_client()

        query = (
            client.table("weather_saitama")
            .select("id")
            .eq("created_at", weather_data["created_at"])
            .execute()
        )

        if query.data:
            print("Result: Data already exists. Skip insert.")
        else:
            res = client.table("weather_saitama").insert(weather_data).execute()
            print(f"Result: Saved. ID={res.data[0]['id']}")

    except Exception as e:
        print(f"Database Error: {e}")
        sys.exit(1)

    print("--- Process finished successfully ---")

if __name__ == "__main__":
    main()
