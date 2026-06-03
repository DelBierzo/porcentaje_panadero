import logging
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "porcentaje_panadero"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Levanta la plataforma de cuadro de texto bajo el flujo moderno."""
    cajas_texto = [
        PanTextEntity(hass, "nombre_nueva_formula", "", "mdi:border-color")
    ]
    async_add_entities(cajas_texto, True)

class PanTextEntity(TextEntity):
    """Representacion nativa de un cuadro de texto panadero bilingue."""

    def __init__(self, hass: HomeAssistant, clave: str, defecto: str, icono: str):
        self._hass = hass
        self._clave = clave
        self._state = defecto
        self._icon = icono

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return self._clave

    @property
    def unique_id(self) -> str: return self._clave

    @property
    def native_value(self) -> str: return self._state

    @property
    def icon(self) -> str: return self._icon

    async def async_set_value(self, value: str) -> None:
        """Actualiza el valor en memoria y fuerza la inyeccion en el bus central."""
        self._state = str(value)
        self.async_write_ha_state()
