"""Van weather service - fetches weather with masked GPS for privacy."""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

import requests
import typer
from apscheduler.schedulers.blocking import BlockingScheduler

from python.common import configure_logger
from python.van_weather.models import Config, DailyForecast, HourlyForecast, Weather

# Map Pirate Weather icons to Home Assistant conditions
CONDITION_MAP = {
    "clear-day": "sunny",
    "clear-night": "clear-night",
    "rain": "rainy",
    "snow": "snowy",
    "sleet": "snowy-rainy",
    "wind": "windy",
    "fog": "fog",
    "cloudy": "cloudy",
    "partly-cloudy-day": "partlycloudy",
    "partly-cloudy-night": "partlycloudy",
}

logger = logging.getLogger(__name__)


def get_ha_state(url: str, token: str, entity_id: str) -> float:
    """Get numeric state from Home Assistant entity."""
    response = requests.get(
        f"{url}/api/states/{entity_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return float(response.json()["state"])


def parse_daily_forecast(data: dict[str, dict[str, Any]]) -> list[DailyForecast]:
    """Parse daily forecast from Pirate Weather API."""
    daily = data.get("daily", {}).get("data", [])
    daily_forecasts = []
    for day in daily[:8]:  # Up to 8 days
        time_stamp = day.get("time")
        if time_stamp:
            date_time = datetime.fromtimestamp(time_stamp, tz=UTC).isoformat()
            daily_forecasts.append(
                DailyForecast(
                    date_time=date_time,
                    condition=CONDITION_MAP.get(day.get("icon", ""), "cloudy"),
                    temperature=day.get("temperatureHigh"),
                    templow=day.get("temperatureLow"),
                    precipitation_probability=day.get("precipProbability"),
                )
            )

    return daily_forecasts


def parse_hourly_forecast(data: dict[str, dict[str, Any]]) -> list[HourlyForecast]:
    """Parse hourly forecast from Pirate Weather API."""
    hourly = data.get("hourly", {}).get("data", [])
    hourly_forecasts = []
    for hour in hourly[:48]:  # Up to 48 hours
        time_stamp = hour.get("time")
        if time_stamp:
            date_time = datetime.fromtimestamp(time_stamp, tz=UTC).isoformat()
            hourly_forecasts.append(
                HourlyForecast(
                    date_time=date_time,
                    condition=CONDITION_MAP.get(hour.get("icon", ""), "cloudy"),
                    temperature=hour.get("temperature"),
                    precipitation_probability=hour.get("precipProbability"),
                )
            )
    return hourly_forecasts


def fetch_weather(api_key: str, lat: float, lon: float) -> Weather:
    """Fetch weather from Pirate Weather API."""
    url = f"https://api.pirateweather.net/forecast/{api_key}/{lat},{lon}"
    response = requests.get(url, params={"units": "us"}, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily_forecasts = parse_daily_forecast(data)
    hourly_forecasts = parse_hourly_forecast(data)

    current = data.get("currently", {})
    icon = current.get("icon", "")
    return Weather(
        temperature=current.get("temperature"),
        feels_like=current.get("apparentTemperature"),
        humidity=current.get("humidity"),
        wind_speed=current.get("windSpeed"),
        wind_bearing=current.get("windBearing"),
        condition=CONDITION_MAP.get(icon, "cloudy"),
        summary=current.get("summary"),
        pressure=current.get("pressure"),
        visibility=current.get("visibility"),
        daily_forecasts=daily_forecasts,
        hourly_forecasts=hourly_forecasts,
    )


def post_to_ha(url: str, token: str, weather: Weather) -> None:
    """Post weather data to Home Assistant as sensor entities."""
    headers = {"Authorization": f"Bearer {token}"}

    # Post current weather as individual sensors
    sensors = {
        "sensor.van_weather_condition": {
            "state": weather.condition or "unknown",
            "attributes": {"friendly_name": "Van Weather Condition"},
        },
        "sensor.van_weather_temperature": {
            "state": weather.temperature,
            "attributes": {"unit_of_measurement": "°F", "device_class": "temperature"},
        },
        "sensor.van_weather_apparent_temperature": {
            "state": weather.feels_like,
            "attributes": {"unit_of_measurement": "°F", "device_class": "temperature"},
        },
        "sensor.van_weather_humidity": {
            "state": int((weather.humidity or 0) * 100),
            "attributes": {"unit_of_measurement": "%", "device_class": "humidity"},
        },
        "sensor.van_weather_pressure": {
            "state": weather.pressure,
            "attributes": {"unit_of_measurement": "mbar", "device_class": "pressure"},
        },
        "sensor.van_weather_wind_speed": {
            "state": weather.wind_speed,
            "attributes": {"unit_of_measurement": "mph", "device_class": "wind_speed"},
        },
        "sensor.van_weather_wind_bearing": {
            "state": weather.wind_bearing,
            "attributes": {"unit_of_measurement": "°"},
        },
        "sensor.van_weather_visibility": {
            "state": weather.visibility,
            "attributes": {"unit_of_measurement": "mi"},
        },
    }

    for entity_id, data in sensors.items():
        if data["state"] is not None:
            requests.post(f"{url}/api/states/{entity_id}", headers=headers, json=data, timeout=30)

    # Post daily forecast as JSON attribute sensor
    daily_forecast = [
        {
            "datetime": daily_forecast.date_time,
            "condition": daily_forecast.condition,
            "temperature": daily_forecast.temperature,
            "templow": daily_forecast.templow,
            "precipitation_probability": int((daily_forecast.precipitation_probability or 0) * 100),
        }
        for daily_forecast in weather.daily_forecasts
    ]

    requests.post(
        f"{url}/api/states/sensor.van_weather_forecast_daily",
        headers=headers,
        json={"state": len(daily_forecast), "attributes": {"forecast": daily_forecast}},
        timeout=30,
    )

    # Post hourly forecast as JSON attribute sensor
    hourly_forecast = [
        {
            "datetime": hourly_forecast.date_time,
            "condition": hourly_forecast.condition,
            "temperature": hourly_forecast.temperature,
            "precipitation_probability": int((hourly_forecast.precipitation_probability or 0) * 100),
        }
        for hourly_forecast in weather.hourly_forecasts
    ]

    requests.post(
        f"{url}/api/states/sensor.van_weather_forecast_hourly",
        headers=headers,
        json={"state": len(hourly_forecast), "attributes": {"forecast": hourly_forecast}},
        timeout=30,
    )


def update_weather(config: Config) -> None:
    """Fetch GPS, mask it, get weather, post to HA."""
    lat = get_ha_state(config.ha_url, config.ha_token, config.lat_entity)
    lon = get_ha_state(config.ha_url, config.ha_token, config.lon_entity)

    masked_lat = round(lat, config.mask_decimals)
    masked_lon = round(lon, config.mask_decimals)

    logger.info(f"Masked location: {masked_lat}, {masked_lon}")

    weather = fetch_weather(config.pirate_weather_api_key, masked_lat, masked_lon)
    logger.info(f"Weather: {weather.temperature}°F, {weather.condition}")

    post_to_ha(config.ha_url, config.ha_token, weather)
    logger.info("Posted weather to HA")


def main(
    ha_url: Annotated[str, typer.Option(envvar="HA_URL")],
    ha_token: Annotated[str, typer.Option(envvar="HA_TOKEN")],
    api_key: Annotated[str, typer.Option(envvar="PIRATE_WEATHER_API_KEY")],
    interval: Annotated[int, typer.Option(help="Poll interval in seconds")] = 900,
    log_level: Annotated[str, typer.Option()] = "INFO",
) -> None:
    """Fetch weather for van using masked GPS location."""
    configure_logger(log_level)

    config = Config(ha_url=ha_url, ha_token=ha_token, pirate_weather_api_key=api_key)

    logger.info(f"Starting van weather service, polling every {interval}s")

    scheduler = BlockingScheduler()
    scheduler.add_job(
        update_weather,
        "interval",
        seconds=interval,
        args=[config],
        next_run_time=datetime.now(UTC),
    )
    scheduler.start()


if __name__ == "__main__":
    typer.run(main)
