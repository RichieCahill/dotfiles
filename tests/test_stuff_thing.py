"""Tests for python/stuff/thing.py."""

from __future__ import annotations

from python.stuff.thing import caculat_batry_specs


def test_caculat_batry_specs() -> None:
    """Test battery specs calculation."""
    capacity, voltage = caculat_batry_specs(
        cell_amp_hour=300,
        cell_voltage=3.2,
        cells_per_pack=8,
        packs=2,
    )
    assert voltage == 3.2 * 8
    assert capacity == voltage * 300 * 2
