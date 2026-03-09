"""Tests for python/stuff modules."""

from __future__ import annotations

from python.stuff.capasitor import (
    calculate_capacitor_capacity,
    calculate_pack_capacity,
    calculate_pack_capacity2,
)
from python.stuff.voltage_drop import (
    Length,
    LengthUnit,
    MaterialType,
    Temperature,
    TemperatureUnit,
    calculate_awg_diameter_mm,
    calculate_resistance_per_meter,
    calculate_wire_area_m2,
    get_material_resistivity,
    max_wire_length,
    voltage_drop,
)


# --- capasitor tests ---


def test_calculate_capacitor_capacity() -> None:
    """Test capacitor capacity calculation."""
    result = calculate_capacitor_capacity(voltage=2.7, farads=500)
    assert isinstance(result, float)


def test_calculate_pack_capacity() -> None:
    """Test pack capacity calculation."""
    result = calculate_pack_capacity(cells=10, cell_voltage=2.7, farads=500)
    assert isinstance(result, float)


def test_calculate_pack_capacity2() -> None:
    """Test pack capacity2 calculation returns capacity and cost."""
    capacity, cost = calculate_pack_capacity2(cells=10, cell_voltage=2.7, farads=3000, cell_cost=11.60)
    assert isinstance(capacity, float)
    assert cost == 11.60 * 10


# --- voltage_drop tests ---


def test_temperature_celsius() -> None:
    """Test Temperature with celsius."""
    t = Temperature(20.0, TemperatureUnit.CELSIUS)
    assert float(t) == 20.0


def test_temperature_fahrenheit() -> None:
    """Test Temperature with fahrenheit."""
    t = Temperature(100.0, TemperatureUnit.FAHRENHEIT)
    assert isinstance(float(t), float)


def test_temperature_kelvin() -> None:
    """Test Temperature with kelvin."""
    t = Temperature(300.0, TemperatureUnit.KELVIN)
    assert isinstance(float(t), float)


def test_temperature_default_unit() -> None:
    """Test Temperature defaults to celsius."""
    t = Temperature(25.0)
    assert float(t) == 25.0


def test_length_meters() -> None:
    """Test Length in meters."""
    length = Length(10.0, LengthUnit.METERS)
    assert float(length) == 10.0


def test_length_feet() -> None:
    """Test Length in feet."""
    length = Length(10.0, LengthUnit.FEET)
    assert abs(float(length) - 3.048) < 0.001


def test_length_inches() -> None:
    """Test Length in inches."""
    length = Length(100.0, LengthUnit.INCHES)
    assert abs(float(length) - 2.54) < 0.001


def test_length_feet_method() -> None:
    """Test Length.feet() conversion."""
    length = Length(1.0, LengthUnit.METERS)
    assert abs(length.feet() - 3.2808) < 0.001


def test_get_material_resistivity_default_temp() -> None:
    """Test material resistivity with default temperature."""
    r = get_material_resistivity(MaterialType.COPPER)
    assert r > 0


def test_get_material_resistivity_with_temp() -> None:
    """Test material resistivity with explicit temperature."""
    r = get_material_resistivity(MaterialType.ALUMINUM, Temperature(50.0))
    assert r > 0


def test_get_material_resistivity_all_materials() -> None:
    """Test resistivity for all materials."""
    for material in MaterialType:
        r = get_material_resistivity(material)
        assert r > 0


def test_calculate_awg_diameter_mm() -> None:
    """Test AWG diameter calculation."""
    d = calculate_awg_diameter_mm(10)
    assert d > 0


def test_calculate_wire_area_m2() -> None:
    """Test wire area calculation."""
    area = calculate_wire_area_m2(10)
    assert area > 0


def test_calculate_resistance_per_meter() -> None:
    """Test resistance per meter calculation."""
    r = calculate_resistance_per_meter(10)
    assert r > 0


def test_voltage_drop_calculation() -> None:
    """Test voltage drop calculation."""
    vd = voltage_drop(
        gauge=10,
        material=MaterialType.CCA,
        length=Length(20, LengthUnit.FEET),
        current_a=20,
    )
    assert vd > 0


def test_max_wire_length_default_temp() -> None:
    """Test max wire length with default temperature."""
    result = max_wire_length(gauge=10, material=MaterialType.CCA, current_amps=20)
    assert float(result) > 0
    assert result.feet() > 0


def test_max_wire_length_with_temp() -> None:
    """Test max wire length with explicit temperature."""
    result = max_wire_length(
        gauge=10,
        material=MaterialType.COPPER,
        current_amps=10,
        voltage_drop=0.5,
        temperature=Temperature(30.0),
    )
    assert float(result) > 0
