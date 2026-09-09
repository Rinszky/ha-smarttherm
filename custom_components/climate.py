"""Climate platform for SmartTherm integration."""
import logging
import aiohttp
import async_timeout
from urllib.parse import quote
import asyncio

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SmartTherm climate platform from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    if coordinator.data:
        for idx, device in enumerate(coordinator.data):
            entities.append(SmartThermClimate(coordinator, idx, device))

    async_add_entities(entities)


class SmartThermClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a SmartTherm Climate Device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, index, device_data):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._index = index
        self._device_id = device_data.get("device_id")
        self._attr_name = None 
        self._attr_unique_id = f"smarttherm_{self._device_id}"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_target_temperature_step = 0.5
        self._attr_min_temp = 15.0
        self._attr_max_temp = 30.0
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )
        self._attr_preset_modes = ["Scheduled", "Manual", "Off", "Hold"]
        self._last_request_url = None

    @property
    def name(self):
        """Return the name of the entity."""
        device = self._get_device()
        return device.get("device_name") if device else f"SmartTherm {self._index}"

    @property
    def device_info(self):
        """Return device information."""
        device = self._get_device()
        name = device.get("device_name") if device else f"SmartTherm {self._index}"
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": name,
            "manufacturer": "SmartTherm",
            "model": "OCStat Thermostat",
        }

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes for debugging."""
        device = self._get_device()
        attrs = {}
        if device:
            attrs.update({
                "raw_api_data": device,
                "th_work": device.get("th_work"),
                "work_mode": device.get("work_mode"),
            })
        if self._last_request_url:
            attrs["last_api_request_url"] = self._last_request_url
        return attrs

    @property
    def current_temperature(self):
        """Return the current room temperature."""
        device = self._get_device()
        if device and "inside_temparature" in device:
            try:
                return float(device["inside_temparature"]) / 10.0
            except (ValueError, TypeError):
                return None
        return None

    @property
    def target_temperature(self):
        """Return target set temperature."""
        device = self._get_device()
        if device:
            val = device.get("current_temprature") or device.get("autoTemp")
            if val is not None:
                try:
                    return float(val) / 10.0
                except (ValueError, TypeError):
                    return None
        return None

    @property
    def hvac_mode(self):
        """Return HVAC mode: OFF if work_mode == 4 OR th_work == 0, else HEAT."""
        device = self._get_device()
        if device:
            work_mode = str(device.get("work_mode"))
            th_work = str(device.get("th_work"))
            if work_mode == "4" or th_work == "0":
                return HVACMode.OFF
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_action(self):
        """Return current action based strictly on th_work."""
        device = self._get_device()
        if device:
            th_work = str(device.get("th_work"))
            if th_work == "1":
                return HVACAction.HEATING
            work_mode = str(device.get("work_mode"))
            if work_mode == "4" or th_work == "0":
                return HVACAction.OFF
            return HVACAction.IDLE
        return None

    @property
    def preset_mode(self):
        """Return current preset mode based on work_mode."""
        device = self._get_device()
        if device:
            work_mode = str(device.get("work_mode"))
            mode_map = {"0": "Scheduled", "1": "Manual", "4": "Off", "5": "Hold"}
            return mode_map.get(work_mode, "Scheduled")
        return "Scheduled"

    def _get_device(self):
        """Get current device data from coordinator."""
        if self.coordinator.data and len(self.coordinator.data) > self._index:
            return self.coordinator.data[self._index]
        return None

    async def async_set_temperature(self, **kwargs):
        """Set target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        temp_int = int(round(temperature * 10))
        device = self._get_device()
        current_work_mode = str(device.get("work_mode", "1")) if device else "1"
        work_mode = "1" if current_work_mode not in ["0", "5"] else current_work_mode

        await self._send_command(temp_int, work_mode)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        work_mode = "4" if hvac_mode == HVACMode.OFF else "1"
        device = self._get_device()
        temp_int = int(device.get("current_temprature") or device.get("autoTemp", 185)) if device else 185

        await self._send_command(temp_int, work_mode)

    async def async_set_preset_mode(self, preset_mode):
        """Set preset mode."""
        mode_map = {"Scheduled": "0", "Manual": "1", "Off": "4", "Hold": "5"}
        work_mode = mode_map.get(preset_mode, "0")
        
        device = self._get_device()
        temp_int = int(device.get("current_temprature") or device.get("autoTemp", 185)) if device else 185

        await self._send_command(temp_int, work_mode)

    async def _send_command(self, temp_int, work_mode):
        """Send command using GET because the server prefers it."""
        safe_device_id = quote(self._device_id)
        
        url = f"http://www.ocstat-thermostat.com/ocstat/setThermostatWorkModeNew?current_temprature={temp_int}&device_id={safe_device_id}&messageId=8535&token={self.coordinator.token}&user_id={self.coordinator.user_id}&work_mode={work_mode}"
        
        self._last_request_url = url
        
        headers = {
            "User-Agent": "OCS100/6.2.0 (iPhone; iOS 27.0; Scale/3.00)",
        }

        async with async_timeout.timeout(10):
            try:
                async with aiohttp.ClientSession() as session:
                    # Changing to session.get to match browser behavior
                    async with session.get(url, headers=headers) as response:
                        await response.text()
                        # Wait a bit for server to process before refreshing
                        await asyncio.sleep(2)
                        await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Failed to send command to SmartTherm: %s", err)
