import logging
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Levanta la plataforma de entrada de texto unificada con dos entidades."""
    async_add_entities([
        PanTextEntity("nombre_nueva_formula", "porcentaje_panadero_nombre_formula_unique"),
        PanTextEntity("nombre_nueva_harina", "porcentaje_panadero_nombre_harina_unique")
    ], True)

class PanTextEntity(TextEntity):
    """Entidad de texto nativa para escribir nombres en el obrador."""

    def __init__(self, clave: str, unique_id_str: str):
        self._clave = clave
        self.entity_id = f"text.{clave}"
        self._unique_id = unique_id_str
        self._state = ""

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return self._clave

    @property
    def unique_id(self) -> str: return self._unique_id

    @property
    def native_value(self) -> str: return self._state

    @property
    def icon(self) -> str: return "mdi:border-color"

    async def async_set_value(self, value: str) -> None:
        self._state = str(value)
        self.async_write_ha_state()
