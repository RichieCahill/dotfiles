"""test_components."""

from pytest_mock import MockerFixture

from python.system_tests.components import systemd_tests, zpool_tests
from python.zfs import Zpool

temp = "Every feature flags pool has all supported and requested features enabled.\n"

SYSTEM_TESTS_COMPONENTS = "python.system_tests.components"


def test_zpool_tests(mocker: MockerFixture) -> None:
    """test_zpool_tests."""
    mock_zpool = mocker.MagicMock(spec=Zpool)
    mock_zpool.health = "ONLINE"
    mock_zpool.capacity = 70
    mock_zpool.name = "Main"
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.Zpool", return_value=mock_zpool)
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.bash_wrapper", return_value=(temp, ""))
    errors = zpool_tests(("Main",))
    assert errors == []


def test_zpool_tests_out_of_date(mocker: MockerFixture) -> None:
    """test_zpool_tests_out_of_date."""
    mock_zpool = mocker.MagicMock(spec=Zpool)
    mock_zpool.health = "ONLINE"
    mock_zpool.capacity = 70
    mock_zpool.name = "Main"
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.Zpool", return_value=mock_zpool)
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.bash_wrapper", return_value=("", ""))
    errors = zpool_tests(("Main",))
    assert errors == ["ZPool out of date run `sudo zpool upgrade -a`"]


def test_zpool_tests_out_of_space(mocker: MockerFixture) -> None:
    """test_zpool_tests_out_of_space."""
    mock_zpool = mocker.MagicMock(spec=Zpool)
    mock_zpool.health = "ONLINE"
    mock_zpool.capacity = 100
    mock_zpool.name = "Main"
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.Zpool", return_value=mock_zpool)
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.bash_wrapper", return_value=(temp, ""))
    errors = zpool_tests(("Main",))
    assert errors == ["Main is low on space"]


def test_zpool_tests_offline(mocker: MockerFixture) -> None:
    """test_zpool_tests_offline."""
    mock_zpool = mocker.MagicMock(spec=Zpool)
    mock_zpool.health = "OFFLINE"
    mock_zpool.capacity = 70
    mock_zpool.name = "Main"
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.Zpool", return_value=mock_zpool)
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.bash_wrapper", return_value=(temp, ""))
    errors = zpool_tests(("Main",))
    assert errors == ["Main is OFFLINE"]


def test_systemd_tests(mocker: MockerFixture) -> None:
    """test_systemd_tests."""
    mocker.patch(
        f"{SYSTEM_TESTS_COMPONENTS}.bash_wrapper",
        side_effect=[
            ("inactive\n", ""),
            ("active\n", ""),
        ],
    )
    errors = systemd_tests(("docker",))
    assert errors == []
    """test_systemd_tests."""


def test_systemd_tests_multiple_negative_retries(mocker: MockerFixture) -> None:
    """test_systemd_tests_fail."""
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.bash_wrapper", return_value=("active\n", ""))
    errors = systemd_tests(("docker",), max_retries=-1, retry_delay_secs=-1)
    assert errors == []


def test_systemd_tests_multiple_pass(mocker: MockerFixture) -> None:
    """test_systemd_tests_fail."""
    mocker.patch(
        f"{SYSTEM_TESTS_COMPONENTS}.bash_wrapper",
        side_effect=[
            ("inactive\n", ""),
            ("activating\n", ""),
            ("active\n", ""),
        ],
    )
    errors = systemd_tests(
        ("docker",),
        retryable_statuses=("inactive\n", "activating\n"),
        valid_statuses=("active\n",),
    )
    assert errors == []


def test_systemd_tests_fail(mocker: MockerFixture) -> None:
    """test_systemd_tests_fail."""
    mocker.patch(f"{SYSTEM_TESTS_COMPONENTS}.bash_wrapper", return_value=("inactive\n", ""))
    errors = systemd_tests(("docker",), max_retries=5)
    assert errors == ["docker is inactive"]
