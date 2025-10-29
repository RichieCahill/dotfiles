"""test_common."""

from __future__ import annotations

from os import environ
from typing import TYPE_CHECKING

from apprise import Apprise

from python.common import bash_wrapper, signal_alert, utcnow

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_utcnow() -> None:
    """test_utcnow."""
    utcnow()


def test_signal_alert(mocker: MockerFixture) -> None:
    """test_signal_alert."""
    environ["SIGNAL_ALERT_FROM_PHONE"] = "1234567890"
    environ["SIGNAL_ALERT_TO_PHONE"] = "0987654321"

    mock_logger = mocker.patch("python.common.logger")
    mock_apprise_client = mocker.MagicMock(spec=Apprise)
    mocker.patch("python.common.Apprise", return_value=mock_apprise_client)

    signal_alert("test")

    mock_logger.info.assert_not_called()
    mock_apprise_client.add.assert_called_once_with("signal://localhost:8989/1234567890/0987654321")
    mock_apprise_client.notify.assert_called_once_with(title="", body="test")


def test_signal_alert_no_phones(mocker: MockerFixture) -> None:
    """test_signal_alert_no_phones."""
    if "SIGNAL_ALERT_FROM_PHONE" in environ:
        del environ["SIGNAL_ALERT_FROM_PHONE"]
    if "SIGNAL_ALERT_TO_PHONE" in environ:
        del environ["SIGNAL_ALERT_TO_PHONE"]
    mock_logger = mocker.patch("python.common.logger")
    signal_alert("test")

    mock_logger.info.assert_called_once_with("SIGNAL_ALERT_FROM_PHONE or SIGNAL_ALERT_TO_PHONE not set")


def test_test_bash_wrapper() -> None:
    """test_test_bash_wrapper."""
    stdout, returncode = bash_wrapper("echo test")
    assert stdout == "test\n"
    assert returncode == 0


def test_test_bash_wrapper_error() -> None:
    """test_test_bash_wrapper_error."""
    expected_error = 2
    stdout, returncode = bash_wrapper("ls /this/path/does/not/exist")
    assert stdout == "ls: cannot access '/this/path/does/not/exist': No such file or directory\n"
    assert returncode == expected_error
