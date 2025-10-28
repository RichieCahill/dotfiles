def caculat_batry_specs(cell_amp_hour, cell_voltage, cells_per_pack, packs):
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

battry_capacity, pack_voltage = caculat_batry_specs(300, 3.2, 8, 4)
print(f"{battry_capacity=} {pack_voltage=}")
cost = 3300
print(f"$/kWh {cost / battry_capacity}")


3300/32

battry_capacity, pack_voltage = caculat_batry_specs(600, 12.8, 2, 1)
print(f"{battry_capacity=} {pack_voltage=}")
cost = (740 * 2)
print({f"{cost=}"})
print(f"$/kWh {cost / battry_capacity}")

battry_capacity, pack_voltage = caculat_batry_specs(300, 12.8, 2, 2)
print(f"{battry_capacity=} {pack_voltage=}")
cost = 330 * 4
print({f"{cost=}"})
print(f"$/kWh {cost / battry_capacity}")
print("a")

battry_capacity, pack_voltage = caculat_batry_specs(280, 3.2, 8, 1)
print(f"{battry_capacity=} {pack_voltage=}")
cost = 130 * 8
print({f"{cost=}"})
print(f"$/kWh {cost / battry_capacity}")

battry_capacity, pack_voltage = caculat_batry_specs(200, 48, 1, 1)
print(f"{battry_capacity=} {pack_voltage=}")
cost = 2060
print({f"{cost=}"})
print(f"$/kWh {cost / battry_capacity}")

battry_capacity, pack_voltage = caculat_batry_specs(600, 12, 2, 1)
print(f"{battry_capacity=} {pack_voltage=}")
cost = 740 * 2
print({f"{cost=}"})
print(f"$/kWh {cost / battry_capacity}")

battry_capacity, pack_voltage = caculat_batry_specs(400, 12, 2, 1)
print(f"{battry_capacity=} {pack_voltage=}")
cost = 590 * 2
print({f"{cost=}"})
print(f"$/kWh {cost / battry_capacity}")

battry_capacity, pack_voltage = caculat_batry_specs(100, 3.2, 8, 4)
print(f"{battry_capacity=} {pack_voltage=}")
cost = 880 * 2
print({f"{cost=}"})
print(f"$/kWh {cost / battry_capacity}")

