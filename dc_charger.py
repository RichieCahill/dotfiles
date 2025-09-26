def dc_charger_on(
    battery_max_kwh: float,
    battery_current_kwh: float,
    solar_max_kwh: float,
    daily_power_kwh: float,
    night: bool,
) -> bool:
    battery_free_kwh = battery_max_kwh - battery_current_kwh

    if daily_power_kwh <= battery_current_kwh or night:
        return True

    if battery_current_kwh >= battery_max_kwh:
        return False

    if solar_max_kwh >= battery_free_kwh:
        return False

    return True
