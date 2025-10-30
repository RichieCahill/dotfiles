"""capasitor."""


def calculate_capacitor_capacity(voltage: float, farads: float) -> float:
    """Calculate capacitor capacity."""
    joules = (farads * voltage**2) // 2
    return joules // 3600


def calculate_pack_capacity(cells: int, cell_voltage: float, farads: float) -> float:
    """Calculate pack capacity."""
    return calculate_capacitor_capacity(cells * cell_voltage, farads / cells)


def calculate_pack_capacity2(cells: int, cell_voltage: float, farads: float, cell_cost: float) -> tuple[float, float]:
    """Calculate pack capacity."""
    capacitor_capacity = calculate_capacitor_capacity(cells * cell_voltage, farads / cells)
    return capacitor_capacity, cell_cost * cells


def main() -> None:
    """Main."""
    watt_hours = calculate_pack_capacity(cells=10, cell_voltage=2.7, farads=500)
    print(f"{watt_hours=}")
    print(f"{watt_hours*16=}")
    watt_hours = calculate_pack_capacity(cells=1, cell_voltage=2.7, farads=5000)
    print(f"{watt_hours=}")

    watt_hours, cost = calculate_pack_capacity2(
        cells=10,
        cell_voltage=2.7,
        farads=3000,
        cell_cost=11.60,
    )
    print(f"{watt_hours=}")
    print(f"{cost=}")


if __name__ == "__main__":
    main()
