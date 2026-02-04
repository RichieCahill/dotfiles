"""TinyTuya device controller for heater."""

import logging

import tinytuya

from python.heater.models import ActionResult, DeviceConfig, HeaterStatus

logger = logging.getLogger(__name__)

# DPS mapping for heater
DPS_POWER = "1"  # bool: on/off
DPS_SETPOINT = "101"  # int: target temp (read-only)
DPS_STATE = "102"  # str: "Stop", "Heat", etc.
DPS_UNKNOWN = "104"  # int: unknown
DPS_ERROR = "108"  # int: last error code


class HeaterController:
    """Controls a Tuya heater device via local network."""

    def __init__(self, config: DeviceConfig) -> None:
        self.device = tinytuya.Device(config.device_id, config.ip, config.local_key)
        self.device.set_version(config.version)
        self.device.set_socketTimeout(0.5)
        self.device.set_socketRetryLimit(1)

    def status(self) -> HeaterStatus:
        """Get current heater status."""
        data = self.device.status()

        if "Error" in data:
            logger.error("Device error: %s", data)
            return HeaterStatus(power=False, raw_dps={"error": data["Error"]})

        dps = data.get("dps", {})
        return HeaterStatus(
            power=bool(dps.get(DPS_POWER, False)),
            setpoint=dps.get(DPS_SETPOINT),
            state=dps.get(DPS_STATE),
            error_code=dps.get(DPS_ERROR),
            raw_dps=dps,
        )

    def turn_on(self) -> ActionResult:
        """Turn heater on."""
        try:
            self.device.set_value(DPS_POWER, True)
            return ActionResult(success=True, action="on", power=True)
        except Exception as error:
            logger.exception("Failed to turn on")
            return ActionResult(success=False, action="on", error=str(error))

    def turn_off(self) -> ActionResult:
        """Turn heater off."""
        try:
            self.device.set_value(DPS_POWER, False)
            return ActionResult(success=True, action="off", power=False)
        except Exception as error:
            logger.exception("Failed to turn off")
            return ActionResult(success=False, action="off", error=str(error))

    def toggle(self) -> ActionResult:
        """Toggle heater power state."""
        status = self.status()
        if status.power:
            return self.turn_off()
        return self.turn_on()
