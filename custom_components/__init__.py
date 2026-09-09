"""SmartTherm Custom Integration for Home Assistant."""
from datetime import timedelta
import logging
import json

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "smarttherm"
PLATFORMS = [Platform.CLIMATE]
UPDATE_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SmartTherm from a config entry."""
    token = entry.data["token"]
    user_id = entry.data["user_id"]
    # We use a default messageId like '8535' since it's not strictly checked by API or we can use a static one
    message_id = "8535"

    coordinator = SmartThermCoordinator(hass, token, user_id, message_id)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return True


class SmartThermCoordinator(DataUpdateCoordinator):
    """Data update coordinator for SmartTherm."""

    def __init__(self, hass, token, user_id, message_id):
        """Initialize coordinator."""
        self.token = token
        self.user_id = user_id
        self.message_id = message_id
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from API for all devices."""
        url = f"http://www.ocstat-thermostat.com/ocstat/getDeviceListNew?device_id=%26vbje5555j01&messageId={self.message_id}&token={self.token}&user_id={self.user_id}"
        async with async_timeout.timeout(10):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url) as response:
                        text = await response.text()
                        try:
                            data = json.loads(text)
                        except json.JSONDecodeError as err:
                            raise Exception(f"Invalid JSON response: {text}") from err

                        if not data.get("statu"):
                            raise Exception("Failed to fetch devices from SmartTherm API")
                        
                        # Returns the full list of devices (e.g. Ground and Rooftop)
                        return data.get("devices", [])
            except Exception as err:
                raise Exception(f"Error communicating with SmartTherm API: {err}")
