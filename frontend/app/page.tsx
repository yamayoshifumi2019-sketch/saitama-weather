'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
const supabase = createClient(supabaseUrl, supabaseAnonKey)

interface WeatherData {
  id?: number
  temperature: string
  wind: string
  precipitation: string
  created_at: string
}

export default function Home() {
  const [weatherData, setWeatherData] = useState<WeatherData[]>([])
  const [filteredData, setFilteredData] = useState<WeatherData[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch weather data from Supabase
  useEffect(() => {
    async function fetchWeatherData() {
      try {
        setLoading(true)
        const { data, error } = await supabase
          .from('weather_saitama')
          .select('*')
          .order('created_at', { ascending: false })

        if (error) {
          throw error
        }

        setWeatherData(data || [])
        setFilteredData(data || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }

    fetchWeatherData()
  }, [])

  // Filter data based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredData(weatherData)
      return
    }

    const lowercaseSearch = searchTerm.toLowerCase()
    const filtered = weatherData.filter((item) => {
      const dateStr = formatDateTime(item.created_at).toLowerCase()
      return (
        dateStr.includes(lowercaseSearch) ||
        item.temperature.toLowerCase().includes(lowercaseSearch) ||
        item.wind.toLowerCase().includes(lowercaseSearch) ||
        item.precipitation.toLowerCase().includes(lowercaseSearch)
      )
    })

    setFilteredData(filtered)
  }, [searchTerm, weatherData])

  // Format datetime for display (without timezone conversion)
  function formatDateTime(isoString: string): string {
    // Parse the ISO string directly without timezone conversion
    // Input format: "2026-01-12T22:40:00+00:00" or "2026-01-12 22:40:00+00"
    const match = isoString.match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/)
    if (match) {
      const [, year, month, day, hour, minute] = match
      return `${year}/${month}/${day} ${hour}:${minute}`
    }
    // Fallback if pattern doesn't match
    return isoString
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-blue-600 text-white py-6 shadow-lg">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold">Saitama Weather Dashboard</h1>
          <p className="text-blue-100 mt-1">Real-time weather data from Saitama, Japan</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Search/Filter Bar */}
        <div className="mb-6">
          <div className="relative">
            <input
              type="text"
              placeholder="Search by date, temperature, wind, or precipitation..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full md:w-96 px-4 py-3 pl-10 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <svg
              className="absolute left-3 top-3.5 h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          {searchTerm && (
            <p className="text-sm text-gray-600 mt-2">
              Showing {filteredData.length} of {weatherData.length} records
            </p>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            <p className="font-medium">Error loading data</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Data Table */}
        {!loading && !error && (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Date/Time
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Temp
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Wind
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Rain
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredData.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
                        {searchTerm ? 'No matching records found' : 'No weather data available'}
                      </td>
                    </tr>
                  ) : (
                    filteredData.map((item, index) => (
                      <tr
                        key={item.id || index}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDateTime(item.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-orange-100 text-orange-800">
                            {item.temperature}°C
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                            {item.wind} m/s
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            {item.precipitation} mm
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Stats Summary */}
        {!loading && !error && weatherData.length > 0 && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">Total Records</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{weatherData.length}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">Latest Update</h3>
              <p className="text-lg font-semibold text-gray-900 mt-2">
                {weatherData[0] ? formatDateTime(weatherData[0].created_at) : 'N/A'}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">Data Source</h3>
              <p className="text-lg font-semibold text-gray-900 mt-2">Weather News JP</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 py-4 mt-8">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>Saitama Weather Dashboard - University Assignment</p>
        </div>
      </footer>
    </div>
  )
}
