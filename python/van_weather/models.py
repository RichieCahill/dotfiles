"""Models for van weather service."""

from datetime import datetime

from pydantic import BaseModel, field_serializer


class Config(BaseModel):
    """Service configuration."""

    ha_url: str
    ha_token: str
    pirate_weather_api_key: str
    lat_entity: str = "sensor.gps_latitude"
    lon_entity: str = "sensor.gps_longitude"
    mask_decimals: int = 1  # ~11km accuracy


class DailyForecast(BaseModel):
    """Daily forecast entry."""

    date_time: datetime
    condition: str | None = None
    temperature: float | None = None  # High
    templow: float | None = None  # Low
    precipitation_probability: float | None = None

    @field_serializer("date_time")
    def serialize_date_time(self, date_time: datetime) -> str:
        """Serialize datetime to ISO format."""
        return date_time.isoformat()


class HourlyForecast(BaseModel):
    """Hourly forecast entry."""

    date_time: datetime
    condition: str | None = None
    temperature: float | None = None
    precipitation_probability: float | None = None

    @field_serializer("date_time")
    def serialize_date_time(self, date_time: datetime) -> str:
        """Serialize datetime to ISO format."""
        return date_time.isoformat()


class Weather(BaseModel):
    """Weather data from Pirate Weather."""

    temperature: float | None = None
    feels_like: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    wind_bearing: float | None = None
    condition: str | None = None
    summary: str | None = None
    pressure: float | None = None
    visibility: float | None = None
    daily_forecasts: list[DailyForecast] = []
    hourly_forecasts: list[HourlyForecast] = []
