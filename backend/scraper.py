"""
Weather Data Scraper for Saitama (GitHub Actions Version)
"""
import os
import re
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# Japan Standard Time (UTC+9)
JST = timezone(timedelta(hours=9))
WEATHER_URL = "https://weathernews.jp/onebox/tenki/saitama/11100/"

def get_supabase_client() -> Client:
    """Create client and FORCE DISABLE proxy settings to avoid errors"""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    
    # 【最重要】GitHub Actionsの環境変数をリセットして自爆を防ぐ
    for var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        if var in os.environ:
            del os.environ[var]
            
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    
    # 最小限の引数で接続
    return create_client(url, key)

def scrape_weather_data() -> dict:
    """Scrape real-time weather data"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    response = requests.get(WEATHER_URL, headers=headers)
    response.raise_for_status()
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    temperature, wind, precipitation = "N/A", "N/A", "0"
    observation_time = None
    today = datetime.now(JST)

    obs_section = soup.find(class_='observedValue')
    if obs_section:
        obs_text = obs_section.get_text().replace('\u2212', '-').replace('\u2013', '-').replace('\uff0d', '-')
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*時点', obs_text)
        if time_match:
            obs_hour, obs_min = int(time_match.group(1)), int(time_match.group(2))
            observation_time = today.replace(hour=obs_hour, minute=obs_min, second=0, microsecond=0)
            if obs_hour > today.hour + 12 or observation_time > today + timedelta(minutes=30):
                observation_time -= timedelta(days=1)
        temp_match = re.search(r'気温[^\d-]*(-?\d+\.?\d*)', obs_text)
        if temp_match: temperature = temp_match.group(1)
        wind_match = re.search(r'(\d+\.?\d*)\s*m/s', obs_text)
        if wind_match: wind = wind_match.group(1)

    precip_matches = re.compile(r'(\d+\.?\d*)\s*ミリ').findall(response.text)
    if precip_matches: precipitation = precip_matches[0]

    return {
        "temperature": temperature,
        "wind": wind,
        "precipitation": precipitation,
        "created_at": observation_time.isoformat() if observation_time else datetime.now(JST).isoformat()
    }

def main():
    print(f"Starting at {datetime.now(JST)}")
    try:
        data = scrape_weather_data()
        print(f"Data: {data}")

        # 接続と保存を一気に実行
        client = get_supabase_client()
        
        # 重複チェック
        exists = client.table("weather_saitama").select("id").eq("created_at", data["created_at"]).execute()
        
        if len(exists.data) > 0:
            print("Duplicate data found. Skipping.")
        else:
            client.table("weather_saitama").insert(data).execute()
            print("Success: Saved to Supabase.")
            
    except Exception as e:
        print(f"Error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
