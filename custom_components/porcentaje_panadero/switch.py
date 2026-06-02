import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "porcentaje_panadero"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Levanta el interruptor bilingüe nativo bajo el flujo de configuración."""
    async_add_entities([PanExtrasSwitch()], True)

class PanExtrasSwitch(SwitchEntity):
    """Representación nativa del interruptor de extras vinculable a las traducciones."""

    def __init__(self):
        """Inicializa el interruptor apagado por defecto."""
        self._is_on = False

    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def translation_key(self) -> str:
        return "pan_extras"

    @property
    def unique_id(self) -> str:
        return "porcentaje_panadero_pan_extras_unique"

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def icon(self) -> str:
        return "mdi:basket-plus"

    async def async_turn_on(self, **kwargs) -> None:
        self._is_on = True
        self.async_write_ha_state()
        await self.hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": 1})

    async def async_turn_off(self, **kwargs) -> None:
        self._is_on = False
        self.async_write_ha_state()
        await self.hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": 1})
