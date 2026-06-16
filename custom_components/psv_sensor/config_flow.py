"""Config flow per PSV Sensor."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import CONF_SCAN_HOUR, DEFAULT_SCAN_HOUR, DOMAIN

class PsvSensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        errors = {}
        if user_input is not None:
            if 0 <= user_input[CONF_SCAN_HOUR] <= 23:
                return self.async_create_entry(title="Prezzi PSV del mese", data=user_input)
            errors[CONF_SCAN_HOUR] = "invalid_hour"
        schema = vol.Schema({
            vol.Required(CONF_SCAN_HOUR, default=DEFAULT_SCAN_HOUR): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PsvSensorOptionsFlow(config_entry)

class PsvSensorOptionsFlow(config_entries.OptionsFlow):
    """Gestisce le opzioni modificabili dopo l'installazione.

    NOTA: non definiamo __init__ con self.config_entry = config_entry.
    Nelle versioni recenti di Home Assistant, OptionsFlow espone già
    `config_entry` come property popolata automaticamente dal framework;
    sovrascriverla qui causa AttributeError perché la property non ha setter.
    """

    async def async_step_init(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            if 0 <= user_input[CONF_SCAN_HOUR] <= 23:
                return self.async_create_entry(title="", data=user_input)
            errors[CONF_SCAN_HOUR] = "invalid_hour"
        current = self.config_entry.options.get(CONF_SCAN_HOUR, self.config_entry.data.get(CONF_SCAN_HOUR, DEFAULT_SCAN_HOUR))
        schema = vol.Schema({
            vol.Required(CONF_SCAN_HOUR, default=current): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
        })
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
