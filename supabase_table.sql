-- SQL to create the weather_saitama table in Supabase
-- Run this in the Supabase SQL Editor

CREATE TABLE weather_saitama (
  id SERIAL PRIMARY KEY,
  temperature TEXT NOT NULL,
  wind TEXT NOT NULL,
  precipitation TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (optional, but recommended)
ALTER TABLE weather_saitama ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations (for development)
CREATE POLICY "Allow all operations" ON weather_saitama
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Create an index on created_at for faster queries
CREATE INDEX idx_weather_saitama_created_at ON weather_saitama(created_at DESC);
