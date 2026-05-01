"""Open-Meteo weather client — no API key required.

Two-step call:
1. Geocoding API  →  city name + country code  →  lat/lon
2. Forecast API   →  lat/lon  →  current conditions + 7-day daily summary

Both calls are async (httpx).  The WeatherResult is a plain dataclass so
the agent tool can serialise it however it likes.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather Interpretation Codes → human-readable description
_WMO: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "icy fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    71: "light snow", 73: "moderate snow", 75: "heavy snow",
    80: "slight showers", 81: "moderate showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "heavy thunderstorm",
}


@dataclass(slots=True, frozen=True)
class DayForecast:
    date: str
    temp_max_c: float
    temp_min_c: float
    precip_mm: float
    condition: str


@dataclass(slots=True, frozen=True)
class WeatherResult:
    city: str
    country_code: str
    latitude: float
    longitude: float
    current_temp_c: float
    current_condition: str
    current_wind_kmh: float
    forecast: tuple[DayForecast, ...]

    def summary(self) -> str:
        lines = [
            f"Current weather in {self.city} ({self.country_code}): "
            f"{self.current_temp_c:.1f}°C, {self.current_condition}, "
            f"wind {self.current_wind_kmh:.0f} km/h.",
            "7-day forecast:",
        ]
        for d in self.forecast:
            lines.append(
                f"  {d.date}: {d.temp_min_c:.0f}–{d.temp_max_c:.0f}°C, "
                f"{d.precip_mm:.0f} mm precip, {d.condition}"
            )
        return "\n".join(lines)


async def get_weather(city: str, country_code: str) -> WeatherResult:
    """Fetch current conditions and 7-day forecast for *city*.

    Raises ``ValueError`` if the city cannot be geocoded.
    Raises ``httpx.HTTPStatusError`` on unexpected API errors.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # --- step 1: geocode ---
        geo = await client.get(
            _GEO_URL,
            params={
                "name": city,
                "count": 5,
                "language": "en",
                "format": "json",
                "countryCode": country_code.upper(),
            },
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            # retry without country filter — some codes are rejected
            geo2 = await client.get(
                _GEO_URL,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
            )
            geo2.raise_for_status()
            results = geo2.json().get("results") or []
        if not results:
            raise ValueError(f"City not found: {city!r} ({country_code})")

        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]

        # --- step 2: weather ---
        wx = await client.get(
            _WEATHER_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weathercode,windspeed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                "forecast_days": 7,
                "timezone": "auto",
            },
        )
        wx.raise_for_status()
        data = wx.json()

    cur = data["current"]
    daily = data["daily"]

    forecast = tuple(
        DayForecast(
            date=daily["time"][i],
            temp_max_c=daily["temperature_2m_max"][i],
            temp_min_c=daily["temperature_2m_min"][i],
            precip_mm=daily["precipitation_sum"][i] or 0.0,
            condition=_WMO.get(daily["weathercode"][i], "unknown"),
        )
        for i in range(len(daily["time"]))
    )

    return WeatherResult(
        city=loc.get("name", city),
        country_code=country_code.upper(),
        latitude=lat,
        longitude=lon,
        current_temp_c=cur["temperature_2m"],
        current_condition=_WMO.get(cur["weathercode"], "unknown"),
        current_wind_kmh=cur["windspeed_10m"],
        forecast=forecast,
    )
