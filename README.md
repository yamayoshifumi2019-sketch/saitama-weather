 1. Backend - Python Weather Scraper

  File: backend/scraper.py

  Technologies:
  - Python 3
  - requests - HTTP requests
  - BeautifulSoup4 - HTML parsing
  - supabase-py - Supabase client

  Scraping Approach:
  - Target URL: https://weathernews.jp/onebox/tenki/saitama/11100/
  - Key discovery: The page has two temperature sections:
    - Hourly forecast (whole numbers like 13℃) - NOT what we want
    - Real-time observation in observedValue class (decimals like 1.6℃) - THIS is correct
  - The scraper finds the observedValue HTML element which contains:
    - 気温 (temperature): extracted with regex 気温[^\d]*(-?\d+\.?\d*)
    - 風 (wind): extracted with regex (\d+\.?\d*)\s*m/s
    - Precipitation: from hourly data

  Output: Clean numeric values only (no units like ℃ or m/s)

  ---
  2. Database - Supabase

  Table: weather_saitama

  Schema (in supabase_table.sql):
  CREATE TABLE weather_saitama (
    id SERIAL PRIMARY KEY,
    temperature TEXT NOT NULL,
    wind TEXT NOT NULL,
    precipitation TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  Credentials used:
  - URL: https://kbomlessjusnwiewewau.supabase.co
  - API Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (the JWT you provided)

  ---
  3. Frontend - Next.js Dashboard

  Files:
  - frontend/pages/index.tsx - Main dashboard component
  - frontend/lib/supabase.ts - Supabase client
  - frontend/styles/globals.css - Tailwind imports

  Technologies:
  - Next.js 14
  - React 18
  - Tailwind CSS
  - @supabase/supabase-js

  Features:
  - Fetches data from weather_saitama table
  - Displays in table format (Date/Time, Temp, Wind, Rain)
  - Client-side search/filter bar
  - Responsive design
