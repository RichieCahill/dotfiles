"""thing."""


def caculat_batry_specs(
    cell_amp_hour: int,
    cell_voltage: float,
    cells_per_pack: int,
    packs: int,
) -> tuple[float, float]:
    """Caculat battry specs."""
    pack_voltage = cell_voltage * cells_per_pack

    pack_watt_hours = pack_voltage * cell_amp_hour

    battry_capacity = pack_watt_hours * packs
    return (
        battry_capacity,
        pack_voltage,
    )


battry_capacity, pack_voltage = caculat_batry_specs(300, 3.2, 8, 2)
print(f"{battry_capacity=} {pack_voltage=}")
cost = 1700
print(f"$/kWh {cost / battry_capacity}")
