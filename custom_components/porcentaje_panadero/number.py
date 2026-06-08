import logging
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    config_app = hass.data[DOMAIN][entry.entry_id]

    config_numbers = [
        ("masa_final_objetivo", 1000.0, 100.0, 10000.0, 50.0, "g", "mdi:scale-balance"),
        ("harina_1", 100.0, 0.0, 100.0, 1.0, "%", "mdi:grain"),
        ("harina_2", 0.0, 0.0, 100.0, 1.0, "%", "mdi:grain"),
        ("harina_3", 0.0, 0.0, 100.0, 1.0, "%", "mdi:grain"),
        ("agua_hidratacion", 60.0, 10.0, 100.0, 0.5, "%", "mdi:water"),
        ("sal", 2.0, 0.0, 5.0, 0.1, "%", "mdi:shaker-outline"),
        ("levadura", 0.7, 0.0, 9.0, 0.01, "%", "mdi:yeast"),
        ("prefermento", 0.0, 0.0, 100.0, 1.0, "%", "mdi:chart-bubble"),
        ("hidratacion_masa_madre", 100.0, 50.0, 150.0, 1.0, "%", "mdi:flask-round-bottom"),
        ("inoculo_masa_madre", 33.3, 0.0, 100.0, 0.1, "%", "mdi:flask-plus"),
        ("levadura_prefermento", 0.2, 0.0, 3.0, 0.01, "%", "mdi:yeast"),
        ("malta", 0.0, 0.0, 3.0, 0.1, "%", "mdi:grain"),
        ("azucar", 0.0, 0.0, 30.0, 0.1, "%", "mdi:spoon-sugar"),
        ("aove", 0.0, 0.0, 30.0, 0.1, "%", "mdi:oil"),
        ("mantequilla", 0.0, 0.0, 50.0, 0.1, "%", "mdi:cow"),
        ("leche_en_polvo", 0.0, 0.0, 20.0, 0.1, "%", "mdi:blur"),
        ("leche_liquida", 0.0, 0.0, 100.0, 0.1, "%", "mdi:water-opacity"),
        ("huevo", 0.0, 0.0, 50.0, 0.1, "%", "mdi:egg"),
        ("temperatura_objetivo_masa", 24.0, 0.0, 32.0, 0.5, "°C", "mdi:thermometer"),
        ("temperatura_harina", 20.0, 0.0, 35.0, 0.5, "°C", "mdi:thermometer"),
        ("temperatura_prefermento", 0.0, 0.0, 35.0, 0.5, "°C", "mdi:thermometer"),
        ("temperatura_friccion_amasadora", 0.0, 0.0, 15.0, 0.5, "°C", "mdi:thermometer"),
        ("temperatura_ambiente", 24.0, 4.0, 32.0, 0.5, "°C", "mdi:thermometer"),
        ("tang_zhong", 0.0, 0.0, 20.0, 1.0, "%", "mdi:pot-steam"),
    ]

    sliders = [PanNumberSlider(c, d, mi, ma, p, u, i) for c, d, mi, ma, p, u, i in config_numbers]
    async_add_entities(sliders, True)

class PanNumberSlider(NumberEntity):
    def __init__(self, clave: str, defecto: float, minimo: float, maximo: float, paso: float, unidad: str, icono: str):
        self._clave = clave
        self.entity_id = f"number.{clave}"
        self._state = defecto
        self._min_value = minimo
        self._max_value = maximo
        self._step = paso
        self._unit = unidad
        self._icon = icono

    @property
    def has_entity_name(self) -> bool: return True
    @property
    def translation_key(self) -> str: return self._clave
    @property
    def unique_id(self) -> str: return f"porcentaje_panadero_{self._clave}_unique"
    @property
    def native_value(self) -> float: return self._state
    @property
    def native_min_value(self) -> float: return self._min_value
    @property
    def native_max_value(self) -> float: return self._max_value
    @property
    def native_step(self) -> float: return self._step
    @property
    def native_unit_of_measurement(self) -> str: return self._unit
    @property
    def icon(self) -> str: return self._icon
    @property
    def mode(self) -> NumberMode: return NumberMode.SLIDER

    async def async_set_native_value(self, value: float) -> None:
        if self._state == round(value, 2):
            return
        self._state = round(value, 2)
        self.async_write_ha_state()

        if self._clave in ["harina_1", "harina_2", "harina_3"]:
            h_orig = 1 if self._clave == "harina_1" else (2 if self._clave == "harina_2" else 3)
            await self.hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": h_orig})
