"""Tests for van_weather/main.py main() function."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from python.van_weather.main import main


def test_van_weather_main() -> None:
    """Test main sets up scheduler."""
    with (
        patch("python.van_weather.main.BlockingScheduler") as mock_sched_cls,
        patch("python.van_weather.main.configure_logger"),
    ):
        mock_sched = MagicMock()
        mock_sched_cls.return_value = mock_sched

        main(
            ha_url="http://ha.local",
            ha_token="token",
            api_key="key",
            interval=60,
            log_level="INFO",
        )

        mock_sched.add_job.assert_called_once()
        mock_sched.start.assert_called_once()
