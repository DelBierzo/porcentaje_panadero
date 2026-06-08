import logging
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    async_add_entities([PanTextEntity()], True)

class PanTextEntity(TextEntity):
    def __init__(self):
        self.entity_id = "text.nombre_nueva_formula"
        self._state = ""

    @property
    def has_entity_name(self) -> bool: return True
    @property
    def translation_key(self) -> str: return "nombre_nueva_formula"
    @property
    def unique_id(self) -> str: return "porcentaje_panadero_nombre_formula_unique"
    @property
    def native_value(self) -> str: return self._state
    @property
    def icon(self) -> str: return "mdi:border-color"

    async def async_set_value(self, value: str) -> None:
        self._state = str(value)
        self.async_write_ha_state()
