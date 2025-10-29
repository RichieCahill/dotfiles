"""test_executors."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

import pytest

from python.parallelize import _parallelize_base, parallelize_process, parallelize_thread

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_mock import MockerFixture


class MockFuture(Future):
    """MockFuture."""

    def __init__(self, result: Any) -> None:  # noqa: ANN401
        """Init."""
        super().__init__()
        self._result = result
        self._exception: BaseException | None = None
        self.set_result(result)

    def exception(self, timeout: float | None = None) -> BaseException | None:
        """Exception."""
        logging.debug(f"{timeout}=")
        return self._exception

    def result(self, timeout: float | None = None) -> Any:  # noqa: ANN401
        """Result."""
        logging.debug(f"{timeout}=")
        return self._result


class MockPoolExecutor(ThreadPoolExecutor):
    """MockPoolExecutor."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initializes a new ThreadPoolExecutor instance."""
        super().__init__(*args, **kwargs)

    def submit(self, fn: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Future:  # noqa: ANN401
        """Submits a callable to be executed with the given arguments.

        Args:
            fn: The callable to execute.
            *args: The positional arguments to pass to the callable.
            **kwargs: The keyword arguments to pass to the callable.

        Returns:
            A Future instance representing the execution of the callable.
        """
        result = fn(*args, **kwargs)
        return MockFuture(result)


def add(a: int, b: int) -> int:
    """Add."""
    return a + b


def test_parallelize_thread() -> None:
    """test_parallelize_thread."""
    kwargs_list = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    results = parallelize_thread(func=add, kwargs_list=kwargs_list, progress_tracker=1)
    assert results.results == [3, 7]
    assert not results.exceptions


def test_parallelize_thread_exception() -> None:
    """test_parallelize_thread."""
    kwargs_list: list[dict[str, int | None]] = [{"a": 1, "b": 2}, {"a": 3, "b": None}]
    results = parallelize_thread(func=add, kwargs_list=kwargs_list)
    assert results.results == [3]
    output = """[TypeError("unsupported operand type(s) for +: 'int' and 'NoneType'")]"""
    assert str(results.exceptions) == output


def test_parallelize_process() -> None:
    """test_parallelize_process."""
    kwargs_list = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    results = parallelize_process(func=add, kwargs_list=kwargs_list)
    assert results.results == [3, 7]
    assert not results.exceptions


def test_parallelize_process_to_many_max_workers(mocker: MockerFixture) -> None:
    """test_parallelize_process."""
    mocker.patch(target="python"
    ".parallelize.cpu_count", return_value=1)

    with pytest.raises(RuntimeError, match="max_workers must be less than or equal to 1"):
        parallelize_process(func=add, kwargs_list=[{"a": 1, "b": 2}], max_workers=8)


def test_executor_results_repr() -> None:
    """test_ExecutorResults_repr."""
    results = parallelize_thread(func=add, kwargs_list=[{"a": 1, "b": 2}])
    assert repr(results) == "results=[3] exceptions=[]"


def test_early_error() -> None:
    """test_early_error."""
    kwargs_list: list[dict[str, int | None]] = [{"a": 1, "b": 2}, {"a": 3, "b": None}]
    with pytest.raises(TypeError, match=r"unsupported operand type\(s\) for \+\: 'int' and 'NoneType'"):
        parallelize_thread(func=add, kwargs_list=kwargs_list, mode="early_error")


def test_mock_pool_executor() -> None:
    """test_mock_pool_executor."""
    results = _parallelize_base(
        executor_type=MockPoolExecutor,
        func=add,
        kwargs_list=[{"a": 1, "b": 2}, {"a": 3, "b": 4}],
        max_workers=None,
        progress_tracker=None,
        mode="normal",
    )
    assert repr(results) == "results=[3, 7] exceptions=[]"
