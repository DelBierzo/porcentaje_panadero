import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PorcentajePanaderoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        registro_entidades = er.async_get(self.hass)
        lista_termometros = ["Ninguno / Manual (Slider)"]

        for entrada in registro_entidades.entities.values():
            if entrada.domain == SENSOR_DOMAIN and entrada.capabilities:
                device_class = entrada.device_class or ""
                if "temperature" in device_class or "temperature" in entrada.entity_id:
                    lista_termometros.append(entrada.entity_id)

        lista_termometros.sort()

        if user_input is not None:
            usar_fisico = user_input.get("usar_sensor_fisico", False)
            termometro_elegido = user_input.get("entidad_termometro", "Ninguno / Manual (Slider)")

            if usar_fisico and termometro_elegido == "Ninguno / Manual (Slider)":
                errors["base"] = "sensor_no_seleccionado"
            else:
                return self.async_create_entry(
                    title="Porcentaje Panadero", 
                    data={
                        "usar_sensor_fisico": usar_fisico,
                        "entidad_termometro": termometro_elegido if usar_fisico else "manual"
                    }
                )

        schema_dict = {
            vol.Optional("usar_sensor_fisico", default=False): bool,
            vol.Optional("entidad_termometro", default="Ninguno / Manual (Slider)"): vol.In(lista_termometros)
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_dict),
            errors=errors
        )
