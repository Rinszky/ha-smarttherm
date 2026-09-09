"""Config flow for SmartTherm integration with email/password login."""
import voluptuous as vol
import aiohttp
import async_timeout
import json

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from . import DOMAIN

class SmartThermConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartTherm."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            email = user_input["email"]
            password = user_input["password"]

            # Perform login request
            url = "http://www.ocstat-thermostat.com/ocstat/login"
            payload = f"email={email}&password={password}&type=1"
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "OCS100/6.2.0 (iPhone; iOS 27.0; Scale/3.00)"
            }

            try:
                async with async_timeout.timeout(10):
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, data=payload, headers=headers) as response:
                            text = await response.text()
                            try:
                                res_data = json.loads(text)
                            except json.JSONDecodeError:
                                errors["base"] = "cannot_connect"
                                res_data = {}

                            if res_data.get("statu"):
                                user_info = res_data.get("user", {})
                                token = user_info.get("token")
                                user_id = str(user_info.get("id"))

                                if token and user_id:
                                    # Save token and user_id in entry data
                                    data = {
                                        "email": email,
                                        "token": token,
                                        "user_id": user_id,
                                    }
                                    return self.async_create_entry(title=f"SmartTherm ({email})", data=data)
                                else:
                                    errors["base"] = "invalid_auth"
                            else:
                                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required("email"): cv.string,
                vol.Required("password"): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
