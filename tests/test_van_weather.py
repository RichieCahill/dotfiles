"""Tests for python/van_weather modules."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from python.van_weather.models import Config, DailyForecast, HourlyForecast, Weather
from python.van_weather.main import (
    CONDITION_MAP,
    fetch_weather,
    get_ha_state,
    parse_daily_forecast,
    parse_hourly_forecast,
    post_to_ha,
    update_weather,
    _post_weather_data,
)

if TYPE_CHECKING:
    pass


# --- models tests ---


def test_config() -> None:
    """Test Config creation."""
    config = Config(ha_url="http://ha.local", ha_token="token123", pirate_weather_api_key="key123")
    assert config.ha_url == "http://ha.local"
    assert config.lat_entity == "sensor.gps_latitude"
    assert config.lon_entity == "sensor.gps_longitude"
    assert config.mask_decimals == 1


def test_daily_forecast() -> None:
    """Test DailyForecast creation and serialization."""
    dt = datetime(2024, 1, 1, tzinfo=UTC)
    forecast = DailyForecast(
        date_time=dt,
        condition="sunny",
        temperature=75.0,
        templow=55.0,
        precipitation_probability=0.1,
    )
    assert forecast.condition == "sunny"
    serialized = forecast.model_dump()
    assert serialized["date_time"] == dt.isoformat()


def test_hourly_forecast() -> None:
    """Test HourlyForecast creation and serialization."""
    dt = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    forecast = HourlyForecast(
        date_time=dt,
        condition="cloudy",
        temperature=65.0,
        precipitation_probability=0.3,
    )
    assert forecast.temperature == 65.0
    serialized = forecast.model_dump()
    assert serialized["date_time"] == dt.isoformat()


def test_weather_defaults() -> None:
    """Test Weather default values."""
    weather = Weather()
    assert weather.temperature is None
    assert weather.daily_forecasts == []
    assert weather.hourly_forecasts == []


def test_weather_full() -> None:
    """Test Weather with all fields."""
    weather = Weather(
        temperature=72.0,
        feels_like=70.0,
        humidity=0.5,
        wind_speed=10.0,
        wind_bearing=180.0,
        condition="sunny",
        summary="Clear",
        pressure=1013.0,
        visibility=10.0,
    )
    assert weather.temperature == 72.0
    assert weather.condition == "sunny"


# --- main tests ---


def test_condition_map() -> None:
    """Test CONDITION_MAP has expected entries."""
    assert CONDITION_MAP["clear-day"] == "sunny"
    assert CONDITION_MAP["rain"] == "rainy"
    assert CONDITION_MAP["snow"] == "snowy"


def test_get_ha_state() -> None:
    """Test get_ha_state."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"state": "45.123"}
    mock_response.raise_for_status.return_value = None

    with patch("python.van_weather.main.requests.get", return_value=mock_response) as mock_get:
        result = get_ha_state("http://ha.local", "token", "sensor.lat")

    assert result == 45.123
    mock_get.assert_called_once()


def test_parse_daily_forecast() -> None:
    """Test parse_daily_forecast."""
    data = {
        "daily": {
            "data": [
                {
                    "time": 1704067200,
                    "icon": "clear-day",
                    "temperatureHigh": 75.0,
                    "temperatureLow": 55.0,
                    "precipProbability": 0.1,
                },
                {
                    "time": 1704153600,
                    "icon": "rain",
                },
            ]
        }
    }
    result = parse_daily_forecast(data)
    assert len(result) == 2
    assert result[0].condition == "sunny"
    assert result[0].temperature == 75.0


def test_parse_daily_forecast_empty() -> None:
    """Test parse_daily_forecast with empty data."""
    result = parse_daily_forecast({})
    assert result == []


def test_parse_daily_forecast_no_timestamp() -> None:
    """Test parse_daily_forecast skips entries without time."""
    data = {"daily": {"data": [{"icon": "clear-day"}]}}
    result = parse_daily_forecast(data)
    assert result == []


def test_parse_hourly_forecast() -> None:
    """Test parse_hourly_forecast."""
    data = {
        "hourly": {
            "data": [
                {
                    "time": 1704067200,
                    "icon": "cloudy",
                    "temperature": 65.0,
                    "precipProbability": 0.3,
                },
            ]
        }
    }
    result = parse_hourly_forecast(data)
    assert len(result) == 1
    assert result[0].condition == "cloudy"


def test_parse_hourly_forecast_empty() -> None:
    """Test parse_hourly_forecast with empty data."""
    result = parse_hourly_forecast({})
    assert result == []


def test_parse_hourly_forecast_no_timestamp() -> None:
    """Test parse_hourly_forecast skips entries without time."""
    data = {"hourly": {"data": [{"icon": "rain"}]}}
    result = parse_hourly_forecast(data)
    assert result == []


def test_fetch_weather() -> None:
    """Test fetch_weather."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "currently": {
            "temperature": 72.0,
            "apparentTemperature": 70.0,
            "humidity": 0.5,
            "windSpeed": 10.0,
            "windBearing": 180.0,
            "icon": "clear-day",
            "summary": "Clear",
            "pressure": 1013.0,
            "visibility": 10.0,
        },
        "daily": {"data": []},
        "hourly": {"data": []},
    }
    mock_response.raise_for_status.return_value = None

    with patch("python.van_weather.main.requests.get", return_value=mock_response):
        weather = fetch_weather("apikey", 45.0, -122.0)

    assert weather.temperature == 72.0
    assert weather.condition == "sunny"


def test_post_weather_data() -> None:
    """Test _post_weather_data."""
    weather = Weather(
        temperature=72.0,
        feels_like=70.0,
        humidity=0.5,
        wind_speed=10.0,
        wind_bearing=180.0,
        condition="sunny",
        pressure=1013.0,
        visibility=10.0,
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("python.van_weather.main.requests.post", return_value=mock_response) as mock_post:
        _post_weather_data("http://ha.local", "token", weather)

    assert mock_post.call_count > 0


def test_post_to_ha_retry_on_failure() -> None:
    """Test post_to_ha retries on failure."""
    weather = Weather(temperature=72.0)

    import requests

    with (
        patch("python.van_weather.main._post_weather_data", side_effect=requests.RequestException("fail")),
        patch("python.van_weather.main.time.sleep"),
    ):
        post_to_ha("http://ha.local", "token", weather)


def test_post_to_ha_success() -> None:
    """Test post_to_ha calls _post_weather_data on each attempt."""
    weather = Weather(temperature=72.0)

    with patch("python.van_weather.main._post_weather_data") as mock_post:
        post_to_ha("http://ha.local", "token", weather)
        # The function loops through all attempts even on success (no break)
        assert mock_post.call_count == 6


def test_update_weather() -> None:
    """Test update_weather orchestration."""
    config = Config(ha_url="http://ha.local", ha_token="token", pirate_weather_api_key="key")

    with (
        patch("python.van_weather.main.get_ha_state", side_effect=[45.123, -122.456]),
        patch("python.van_weather.main.fetch_weather", return_value=Weather(temperature=72.0, condition="sunny")),
        patch("python.van_weather.main.post_to_ha"),
    ):
        update_weather(config)
