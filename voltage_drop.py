from enum import Enum
import math


class TemperatureUnit(Enum):
    CELSIUS = "c"
    FAHRENHEIT = "f"
    KELVIN = "k"


class Temperature:
    def __init__(
        self,
        temperature: float,
        unit: TemperatureUnit = TemperatureUnit.CELSIUS,
    ) -> None:
        """
        Args:
            temperature (float): Temperature in degrees Celsius
            unit (TemperatureUnit, optional): Temperature unit. Defaults to TemperatureUnit.CELSIUS.
        """
        unit_modifier = {
            TemperatureUnit.CELSIUS: 1,
            TemperatureUnit.FAHRENHEIT: 0.5556,
            TemperatureUnit.KELVIN: 1.8,
        }
        self.temperature = temperature * unit_modifier[unit]

    def __float__(self) -> float:
        return self.temperature


class LengthUnit(Enum):
    METERS = "m"
    FEET = "ft"
    INCHES = "in"


class Length:
    def __init__(self, length: float, unit: LengthUnit):
        self.meters = self._convert_to_meters(length, unit)

    def _convert_to_meters(self, length: float, unit: LengthUnit) -> float:
        thing = {
            LengthUnit.METERS: 1,
            LengthUnit.FEET: 0.3048,
            LengthUnit.INCHES: 0.0254,
        }
        test = thing.get(unit)
        if test:
            return length * test
        raise ValueError(f"Unsupported unit: {unit}")

    def __float__(self):
        return self.meters

    def feet(self) -> float:
        return self.meters * 3.2808


class MaterialType(Enum):
    COPPER = "copper"
    ALUMINUM = "aluminum"
    CCA = "cca"
    SILVER = "silver"
    GOLD = "gold"


def get_material_resistivity(
    material: MaterialType,
    temperature: Temperature = Temperature(20.0),
) -> float:
    material_info = {
        MaterialType.COPPER: (1.724e-8, 0.00393),
        MaterialType.ALUMINUM: (2.908e-8, 0.00403),
        MaterialType.CCA: (2.577e-8, 0.00397),
        MaterialType.SILVER: (1.632e-8, 0.00380),
        MaterialType.GOLD: (2.503e-8, 0.00340),
    }

    base_resistivity, temp_coefficient = material_info[material]
    return base_resistivity * (1 + temp_coefficient * float(temperature))


def calculate_awg_diameter_mm(gauge: int) -> float:
    """
    Calculate wire diameter in millimeters for a given AWG gauge.
    Formula: diameter = 0.127 * 92^((36-gauge)/39)
    Where:
    - 0.127mm is the diameter of AWG 36
    - 92 is the ratio of diameters between AWG 0000 and AWG 36
    - 39 is the number of steps between AWG 0000 and AWG 36
    """
    return round(0.127 * 92 ** ((36 - gauge) / 39), 3)


def calculate_wire_area_m2(gauge: int) -> float:
    """Calculate the area of a wire in square meters.

    Args:
        gauge (int): The AWG (American Wire Gauge) number of the wire

    Returns:
        float: The area of the wire in square meters
    """
    return math.pi * (calculate_awg_diameter_mm(gauge) / 2000) ** 2


def calculate_resistance_per_meter(gauge: int) -> float:
    """Calculate the resistance per meter of a wire.

    Args:
        gauge (int): The AWG (American Wire Gauge) number of the wire

    Returns:
        float: The resistance per meter of the wire
    """
    return get_material_resistivity(MaterialType.COPPER) / calculate_wire_area_m2(gauge)


def voltage_drop(
    gauge: int,
    material: MaterialType,
    length: Length,
    current_a: float,
) -> float:
    resistivity = get_material_resistivity(material)
    resistance_per_meter = resistivity / calculate_wire_area_m2(gauge)
    total_resistance = resistance_per_meter * float(length) * 2  # round-trip
    return total_resistance * current_a


print(
    voltage_drop(
        gauge=10,
        material=MaterialType.CCA,
        length=Length(length=20, unit=LengthUnit.FEET),
        current_a=20,
    )
)


def max_wire_length(
    gauge: int,
    material: MaterialType,
    current_amps: float,
    voltage_drop: float = 0.3,
    temperature: Temperature = Temperature(100.0, unit=TemperatureUnit.FAHRENHEIT),
) -> Length:
    """Calculate the maximum allowable wire length based on voltage drop criteria.

    Args:
        gauge (int): The AWG (American Wire Gauge) number of the wire
        material (MaterialType): The type of conductor material (e.g., copper, aluminum)
        current_amps (float): The current flowing through the wire in amperes
        voltage_drop (float, optional): Maximum allowable voltage drop as a decimal (default 0.1 or 10%)

    Returns:
        float: Maximum wire length in meters that maintains the specified voltage drop
    """
    resistivity = get_material_resistivity(material, temperature)
    resistance_per_meter = resistivity / calculate_wire_area_m2(gauge)
    # V = IR, solve for length where V is the allowed voltage drop
    return Length(
        voltage_drop / (current_amps * resistance_per_meter),
        LengthUnit.METERS,
    )


print(max_wire_length(gauge=10, material=MaterialType.CCA, current_amps=20).feet())
print(max_wire_length(gauge=10, material=MaterialType.CCA, current_amps=10).feet())
print(max_wire_length(gauge=10, material=MaterialType.CCA, current_amps=5).feet())
