import logging
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "porcentaje_panadero"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Levanta los sliders de forma condicional leyendo la configuracion de la UI."""
    config_app = hass.data[DOMAIN][entry.entry_id]
    usar_sensor_fisico = config_app.get("usar_sensor_fisico", False)

    config_numbers = [
        ("pan_masa_final", 1000.0, 100.0, 10000.0, 50.0, "g", "mdi:scale-balance"),
        ("pan_pct_harina_1", 100.0, 0.0, 100.0, 1.0, "%", "mdi:grain"),
        ("pan_pct_harina_2", 0.0, 0.0, 100.0, 1.0, "%", "mdi:grain"),
        ("pan_pct_harina_3", 0.0, 0.0, 100.0, 1.0, "%", "mdi:grain"),
        ("pan_pct_agua", 60.0, 10.0, 100.0, 0.5, "%", "mdi:water"),
        ("pan_pct_sal", 2.0, 0.0, 5.0, 0.1, "%", "mdi:shaker-outline"),
        ("pan_pct_levadura", 0.7, 0.0, 5.0, 0.01, "%", "mdi:yeast"),
        ("pan_pct_prefermento", 0.0, 0.0, 100.0, 1.0, "%", "mdi:chart-bubble"),
        ("pan_hidratacion_masa_madre", 100.0, 50.0, 150.0, 1.0, "%", "mdi:flask-round-bottom"),
        ("pan_porcentaje_inoculo_masa_madre", 33.3, 0.0, 100.0, 0.1, "%", "mdi:flask-plus"),
        ("pan_pct_levadura_prefermento", 0.0, 0.0, 1.5, 0.01, "%", "mdi:yeast"),
        ("pan_pct_malta", 0.0, 0.0, 3.0, 0.1, "%", "mdi:grain"),
        ("pan_pct_azucar", 0.0, 0.0, 30.0, 0.1, "%", "mdi:spoon-sugar"),
        ("pan_pct_aove", 0.0, 0.0, 30.0, 0.1, "%", "mdi:oil"),
        ("pan_pct_mantequilla", 0.0, 0.0, 50.0, 0.1, "%", "mdi:cow"),
        ("pan_pct_leche_en_polvo", 0.0, 0.0, 20.0, 0.1, "%", "mdi:blur"),
        ("pan_pct_leche", 0.0, 0.0, 100.0, 0.1, "%", "mdi:water-opacity"),
        ("pan_pct_huevo", 0.0, 0.0, 50.0, 0.1, "%", "mdi:egg"),
        ("pan_t_objetivo_masa", 24.0, 0.0, 32.0, 0.5, "°C", "mdi:thermometer-check"),
        ("pan_t_harina", 20.0, 0.0, 35.0, 0.5, "°C", "mdi:thermometer"),
        ("pan_t_prefermento", 20.0, 0.0, 35.0, 0.5, "°C", "mdi:thermometer"),
        ("pan_t_friccion_amasadora", 0.0, 0.0, 15.0, 0.5, "°C", "mdi:engine-outline"),
    ]

    if not usar_sensor_fisico:
        config_numbers.append(("pan_t_ambiente", 20.0, 0.0, 40.0, 0.5, "°C", "mdi:thermometer"))

    sliders = [PanNumberSlider(c, d, mi, ma, p, u, i) for c, d, mi, ma, p, u, i in config_numbers]
    async_add_entities(sliders, True)

class PanNumberSlider(NumberEntity):
    """Representacion nativa de un control deslizante panadero bilingue."""

    def __init__(self, clave: str, defecto: float, minimo: float, maximo: float, paso: float, unidad: str, icono: str):
        self._clave = clave
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
        """Actualiza el valor en memoria y fuerza la inyeccion en el bus central de HA."""
        self._state = round(value, 2)
        self.async_write_ha_state()
        self.hass.states.async_set(
            self.entity_id, 
            str(self._state), 
            {"unit_of_measurement": self._unit, "friendly_name": self.name}
        )

        harina_origen = 1
        if self._clave == "pan_pct_harina_2":
            harina_origen = 2
        elif self._clave == "pan_pct_harina_3":
            harina_origen = 3

        await self.hass.services.async_call(
            DOMAIN,
            "balancear_harinas",
            {"harina_origen": harina_origen}
        )
