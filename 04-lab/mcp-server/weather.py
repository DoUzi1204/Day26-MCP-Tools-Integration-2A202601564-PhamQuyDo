from typing import Any
import asyncio
import httpx
import os
from fastmcp import FastMCP

from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))
mcp = FastMCP("weather")

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    # Check if API key is set
    if not API_KEY:
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    # Add API key to parameters
    params["key"] = API_KEY
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
    """
    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    if not data:
        if not API_KEY:
            # Fallback mock weather for instant testing
            return f"""Current Weather for {city.title()}, Vietnam (Live Demo):

Temperature: 29.0°C (84.2°F)
Feels like: 32.0°C (89.6°F)
Condition: Partly Cloudy ⛅
Humidity: 78%
Wind: 12.0 km/h (7.5 mph) SE
Pressure: 1010 mb
UV Index: 6.0
Visibility: 10.0 km

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        return f"Unable to fetch current weather data for {city}. Please check the city name and API key configuration."

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    # Limit days to 3 for free tier
    days = min(days, 3)
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data:
        if not API_KEY:
            # Fallback mock forecast for testing
            today = datetime.now()
            forecasts = [f"Weather Forecast for {city.title()} (3-Day Demo):"]
            demo_days = [
                ("Partly Cloudy ⛅", 31, 24, 20, 12, 6),
                ("Scattered Showers 🌧️", 29, 23, 65, 16, 4),
                ("Sunny & Pleasant ☀️", 32, 25, 10, 10, 8),
            ]
            for i in range(days):
                date_str = (today + timedelta(days=i)).strftime('%Y-%m-%d')
                cond, high, low, rain, wind, uv = demo_days[i % len(demo_days)]
                forecast = f"""{date_str}:
High: {high}°C ({high * 9/5 + 32:.1f}°F)
Low: {low}°C ({low * 9/5 + 32:.1f}°F)
Condition: {cond}
Chance of Rain: {rain}%
Max Wind: {wind} km/h
UV Index: {uv}"""
                forecasts.append(forecast)
            return "\n---\n".join(forecasts)
        return f"Unable to fetch forecast data for {city}. Please check the city name and API key configuration."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide."

print("✅ MCP server initialized with Streamable HTTP transport")
print("🔧 Available tools: get_current_weather, get_forecast, health_check")

if __name__ == "__main__":
    import sys
    
    is_cloud_run = bool(os.getenv("PORT"))
    is_standalone = len(sys.argv) == 1 and sys.stdin.isatty()
    
    if is_cloud_run or is_standalone:
        print(f"🚀 Starting MCP server on http://0.0.0.0:{port}/mcp")
        try:
            mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
        except TypeError:
            mcp.run(transport="streamable-http")
    else:
        print("Starting FastMCP server in stdio mode for local client", file=sys.stderr)
        mcp.run()