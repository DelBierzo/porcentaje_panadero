import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
DOMAIN = "porcentaje_panadero"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Levanta los interruptores nativos bajo el flujo de configuración con persistencia."""
    async_add_entities([
        PanExtrasSwitch("habilitar_ingredientes_extras", "mdi:basket-plus"),
        PanExtrasSwitch("calcular_hidratacion_real", "mdi:water-percent")
    ], True)

class PanExtrasSwitch(SwitchEntity, RestoreEntity):
    """Representación nativa de los interruptores del obrador."""

    def __init__(self, clave: str, icono: str):
        """Inicializa el interruptor."""
        self._clave = clave
        self._icono = icono
        self.entity_id = f"switch.{clave}"
        self._is_on = False

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return self._clave

    @property
    def unique_id(self) -> str: return f"porcentaje_panadero_{self._clave}_unique"

    @property
    def is_on(self) -> bool: return self._is_on

    @property
    def icon(self) -> str: return self._icono

    async def async_added_to_hass(self):
        """Se ejecuta al arrancar el servidor. Gestiona la persistencia selectiva."""
        await super().async_added_to_hass()

        if self._clave == "habilitar_ingredientes_extras":
            self._is_on = False
            _LOGGER.info("Interruptor '%s' inicializado en APAGADO por política de seguridad.", self._clave)
        else:
            old_state = await self.async_get_last_state()
            if old_state:
                self._is_on = old_state.state == "on"
            _LOGGER.info("Interruptor '%s' restaurado del disco en estado: %s", self._clave, old_state.state if old_state else "off")

    async def async_turn_on(self, **kwargs) -> None:
        self._is_on = True
        self.async_write_ha_state()
        await self.hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": 1})

    async def async_turn_off(self, **kwargs) -> None:
        self._is_on = False
        self.async_write_ha_state()
        await self.hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": 1})
