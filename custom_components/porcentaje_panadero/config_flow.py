import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PorcentajePanaderoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Maneja el flujo de configuración nativo de la integración."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Primer paso cuando el usuario añade la integración desde la interfaz."""
        errores = {}

        if user_input is not None:
            if user_input.get("usar_sensor_fisico") and user_input.get("entidad_termometro") == "manual":
                errores["base"] = "sensor_no_seleccionado"
            else:
                return self.async_create_entry(
                    title="Porcentaje Panadero",
                    data=user_input
                )

        registro_entidades = er.async_get(self.hass)
        sensores_temperatura = ["manual"]

        for entidad in registro_entidades.entities.values():
            if entidad.domain == "sensor":
                if entidad.device_class == "temperature" or "temperature" in entidad.entity_id:
                    sensores_temperatura.append(entidad.entity_id)

        esquema_datos = vol.Schema({
            vol.Required("usar_sensor_fisico", default=False): bool,
            vol.Required("entidad_termometro", default="manual"): vol.In(sensores_temperatura)
        })

        return self.async_show_form(
            step_id="user",
            data_schema=esquema_datos,
            errors=errores
        )
