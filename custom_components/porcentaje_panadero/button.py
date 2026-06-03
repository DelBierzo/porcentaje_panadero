import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "porcentaje_panadero"

_TIPO_LEVADURA_MEMORIA = "seca"

# ID exacto de la entidad en la base de datos de estados de Home Assistant
ID_BOTON_LEVADURA = "button.alternar_fresca_seca"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Levanta la plataforma de botones nativos bajo la arquitectura moderna."""
    # Instanciamos el botón de levadura primero
    boton_toggle_yeast = PanToggleYeastButton(hass)
    
    # Creamos las instancias del resto de botones pasando la referencia para sincronizarlos
    boton_reset = PanResetButton(hass, boton_toggle_yeast)
    boton_save = PanSaveButton(hass)
    boton_delete = PanDeleteButton(hass)
    
    async_add_entities([
        boton_reset,
        boton_save,
        boton_delete,
        boton_toggle_yeast
    ], True)

class PanResetButton(ButtonEntity):
    """Boton nativo para restablecer los sliders a los valores de fabrica."""

    def __init__(self, hass: HomeAssistant, boton_levadura):
        self._hass = hass
        self._boton_levadura = boton_levadura

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return "pan_restablecer_valores"

    @property
    def unique_id(self) -> str: return "porcentaje_panadero_pan_restablecer_valores_unique"

    @property
    def icon(self) -> str: return "mdi:lock-reset"

    async def async_press(self) -> None:
        """Se ejecuta al pulsar el boton de restablecer. Envia comandos directos a tus IDs limpios."""
        _LOGGER.info("Restableciendo parametros de Porcentaje Panadero a valores de fabrica.")
        global _TIPO_LEVADURA_MEMORIA
        _TIPO_LEVADURA_MEMORIA = "seca"
        
        valores_fabrica = {
            "number.masa_final_objetivo": 1000.0,
            "number.harina_1": 100.0,
            "number.harina_2": 0.0,
            "number.harina_3": 0.0,
            "number.agua_hidratacion": 60.0,
            "number.sal": 2.0,
            "number.levadura": 0.7,
            "number.prefermento": 0.0,
            "number.hidratacion_masa_madre": 100.0,
            "number.levadura_prefermento": 0.0,
            "number.malta": 0.0,
            "number.azucar": 0.0,
            "number.aove": 0.0,
            "number.mantequilla": 0.0,
            "number.leche_en_polvo": 0.0,
            "number.leche_liquida": 0.0,
            "number.huevo": 0.0,
            "number.temperatura_objetivo_masa": 24.0,
            "number.temperatura_harina": 20.0,
            "number.temperatura_prefermento": 20.0,
            "number.temperatura_friccion_amasadora": 0.0
        }

        for vid in ["select.formula_de_receta", "select.formulas", "select.porcentaje_panadero_formula_de_receta_unique"]:
            if self._hass.states.get(vid) is not None:
                await self._hass.services.async_call("select", "select_option", {"entity_id": vid, "option": "---"})

        if self._hass.states.get("switch.habilitar_ingredientes_extras") is not None:
            await self._hass.services.async_call("switch", "turn_off", {"entity_id": "switch.habilitar_ingredientes_extras"})

        if self._hass.states.get("text.porcentaje_panadero_nombre_nueva_formula") is not None:
            await self._hass.services.async_call("text", "set_value", {"entity_id": "text.porcentaje_panadero_nombre_nueva_formula", "value": ""})

        for entidad_id, valor in valores_fabrica.items():
            if self._hass.states.get(entidad_id) is not None:
                try:
                    await self._hass.services.async_call("number", "set_value", {"entity_id": entidad_id, "value": valor})
                except Exception:
                    pass

        # Forzamos al botón de levadura a repintarse en 'seca' inmediatamente
        if self._boton_levadura:
            self._boton_levadura.async_write_ha_state()

class PanSaveButton(ButtonEntity):
    """Boton nativo para guardar la receta activa."""

    def __init__(self, hass: HomeAssistant):
        self._hass = hass

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return "pan_guardar_formula"

    @property
    def unique_id(self) -> str: return "porcentaje_panadero_pan_guardar_formula_unique"

    @property
    def icon(self) -> str: return "mdi:content-save-move"

    async def async_press(self) -> None:
        await self._hass.services.async_call(DOMAIN, "guardar_formula", {})

class PanDeleteButton(ButtonEntity):
    """Boton nativo para eliminar la receta activa."""

    def __init__(self, hass: HomeAssistant):
        self._hass = hass

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return "pan_eliminar_formula"

    @property
    def unique_id(self) -> str: return "porcentaje_panadero_pan_eliminar_formula_unique"

    @property
    def icon(self) -> str: return "mdi:trash-can-outline"

    async def async_press(self) -> None:
        await self._hass.services.async_call(DOMAIN, "eliminar_formula", {})

class PanToggleYeastButton(ButtonEntity):
    """Boton con estado persistente de texto inyectado en el Core."""

    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self.entity_id = ID_BOTON_LEVADURA

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return "pan_alternar_tipo_levadura"

    @property
    def unique_id(self) -> str: return "porcentaje_panadero_pan_alternar_tipo_levadura_unique"

    @property
    def icon(self) -> str: return "mdi:swap-horizontal"

    @property
    def state(self) -> str:
        """Fuerza al estado principal a devolver el texto en lugar de la fecha de pulsacion."""
        global _TIPO_LEVADURA_MEMORIA
        return _TIPO_LEVADURA_MEMORIA

    @property
    def extra_state_attributes(self) -> dict:
        """Devuelve los atributos requeridos por Lovelace."""
        global _TIPO_LEVADURA_MEMORIA
        return {
            "tipo_levadura": _TIPO_LEVADURA_MEMORIA,
            "options": ["fresca", "seca"]
        }

    async def async_press(self) -> None:
        """Se ejecuta al pulsar fisicamente el boton en la pantalla."""
        global _TIPO_LEVADURA_MEMORIA
        tipo_actual = _TIPO_LEVADURA_MEMORIA
        
        def get_f(eid):
            st = self._hass.states.get(eid)
            return float(st.state) if st and st.state not in ["unavailable", "unknown", ""] else 0.0

        pct_leva = get_f("number.levadura")
        pct_leva_pref = get_f("number.levadura_prefermento")

        if tipo_actual == "seca":
            _TIPO_LEVADURA_MEMORIA = "fresca"
            nuevo_pct = round(pct_leva * 3.0, 2)
            nuevo_pct_pref = round(pct_leva_pref * 3.0, 2)
        else:
            _TIPO_LEVADURA_MEMORIA = "seca"
            nuevo_pct = round(pct_leva / 3.0, 2)
            nuevo_pct_pref = round(pct_leva_pref / 3.0, 2)

        if self._hass.states.get("number.levadura") is not None:
            await self._hass.services.async_call("number", "set_value", {"entity_id": "number.levadura", "value": nuevo_pct})
        if pct_leva_pref > 0 and self._hass.states.get("number.levadura_prefermento") is not None:
            await self._hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": nuevo_pct_pref})

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_write_ha_state()

# Funciones puente globales requeridas para __init__.py
def obtener_tipo_levadura_actual() -> str:
    global _TIPO_LEVADURA_MEMORIA
    return _TIPO_LEVADURA_MEMORIA

def establecer_tipo_levadura_actual(tipo: str) -> None:
    global _TIPO_LEVADURA_MEMORIA
    if tipo in ["fresca", "seca"]:
        _TIPO_LEVADURA_MEMORIA = tipo
