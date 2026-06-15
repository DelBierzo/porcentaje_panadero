import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "porcentaje_panadero"

_TIPO_LEVADURA_MEMORIA = "seca"
_BASE_TANG_ZHONG_MEMORIA = "agua"

ID_BOTON_LEVADURA = "button.alternar_fresca_seca"
ID_BOTON_TANG_ZHONG = "button.alternar_tang_zhong_agua_leche"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Levanta la plataforma de botones nativos bajo la arquitectura moderna."""
    boton_toggle_yeast = PanToggleYeastButton(hass)
    boton_toggle_tz = PanToggleTangZhongButton(hass)
    boton_reset = PanResetButton(hass, boton_toggle_yeast, boton_toggle_tz)
    boton_save = PanSaveButton(hass)
    boton_delete = PanDeleteButton(hass)

    async_add_entities([
        boton_reset,
        boton_save,
        boton_delete,
        boton_toggle_yeast,
        boton_toggle_tz
    ], True)

class PanResetButton(ButtonEntity):
    """Botón nativo para restablecer los sliders y harinas a los valores de fábrica."""

    def __init__(self, hass: HomeAssistant, boton_levadura, boton_tz):
        self._hass = hass
        self._boton_levadura = boton_levadura
        self._boton_tz = boton_tz

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return "pan_restablecer_valores"

    @property
    def unique_id(self) -> str: 
        return "porcentaje_panadero_pan_restablecer_valores_unique"

    @property
    def icon(self) -> str: return "mdi:lock-reset"

    async def async_press(self) -> None:
        """Se ejecuta al pulsar el botón de restablecer. Envía comandos directos limpios."""
        _LOGGER.info("Restableciendo parámetros de Porcentaje Panadero a valores de fábrica.")
        
        from . import const
        const.RECETA_ACTIVA_MEMORIA = "---"
        
        global _TIPO_LEVADURA_MEMORIA, _BASE_TANG_ZHONG_MEMORIA
        _TIPO_LEVADURA_MEMORIA = "seca"
        _BASE_TANG_ZHONG_MEMORIA = "agua"
        
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
            "number.inoculo_masa_madre": 33.3,
            "number.levadura_prefermento": 0.2,
            "number.tang_zhong": 0.0,
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
            "number.temperatura_friccion_amasadora": 0.0,
            "number.temperatura_ambiente": 24.0
        }

        if self._hass.states.get("select.formula_de_receta") is not None:
            await self._hass.services.async_call("select", "select_option", {"entity_id": "select.formula_de_receta", "option": "---"})
        if self._hass.states.get("switch.habilitar_ingredientes_extras") is not None:
            await self._hass.services.async_call("switch", "turn_off", {"entity_id": "switch.habilitar_ingredientes_extras"})
        if self._hass.states.get("text.nombre_nueva_formula") is not None:
            await self._hass.services.async_call("text", "set_value", {"entity_id": "text.nombre_nueva_formula", "value": ""})
        if self._hass.states.get("text.nombre_nueva_harina") is not None:
            await self._hass.services.async_call("text", "set_value", {"entity_id": "text.nombre_nueva_harina", "value": ""})
        if self._hass.states.get("select.origen_temperatura_levado") is not None:
            await self._hass.services.async_call("select", "select_option", {"entity_id": "select.origen_temperatura_levado", "option": "Manual (Slider)"})
        if self._hass.states.get("select.harina_principal_1") is not None:
            await self._hass.services.async_call("select", "select_option", {"entity_id": "select.harina_principal_1", "option": "HARINA 1"})
        if self._hass.states.get("select.harina_secundaria_2") is not None:
            await self._hass.services.async_call("select", "select_option", {"entity_id": "select.harina_secundaria_2", "option": "HARINA 2"})
        if self._hass.states.get("select.harina_secundaria_3") is not None:
            await self._hass.services.async_call("select", "select_option", {"entity_id": "select.harina_secundaria_3", "option": "HARINA 3"})
        if self._hass.states.get("select.retirar_harina_del_inventario") is not None:
            await self._hass.services.async_call("select", "select_option", {"entity_id": "select.retirar_harina_del_inventario", "option": "---"})
        if self._hass.states.get("select.eliminar_harina") is not None:
            await self._hass.services.async_call("select", "select_option", {"entity_id": "select.eliminar_harina", "option": "---"})

        try:
            componente_select = self._hass.data.get("select")
            if componente_select and hasattr(componente_select, "entities"):
                for entidad in componente_select.entities:
                    if hasattr(entidad, "unique_id"):
                        if entidad.unique_id == "porcentaje_panadero_select_selector_harina_1_unique":
                            entidad._current_option = "HARINA 1"
                            entidad.async_write_ha_state()
                        elif entidad.unique_id == "porcentaje_panadero_select_selector_harina_2_unique":
                            entidad._current_option = "HARINA 2"
                            entidad.async_write_ha_state()
                        elif entidad.unique_id == "porcentaje_panadero_select_selector_harina_3_unique":
                            entidad._current_option = "HARINA 3"
                            entidad.async_write_ha_state()
                        elif entidad.unique_id in ["porcentaje_panadero_select_eliminar_harina_unique", "porcentaje_panadero_select_retirar_harina_del_inventario_unique"]:
                            entidad._current_option = "---"
                            entidad.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Error forzando reinicio de estados en RAM del componente: %s", ex)

        for entidad_id, valor in valores_fabrica.items():

            if self._hass.states.get(entidad_id) is not None:
                try:
                    await self._hass.services.async_call("number", "set_value", {"entity_id": entidad_id, "value": valor})
                except Exception:
                    pass

        if self._boton_levadura:
            self._boton_levadura.async_write_ha_state()
        
        if self._boton_tz:
            self._boton_tz.async_write_ha_state()
            self._hass.states.async_set(
                ID_BOTON_TANG_ZHONG,
                "agua",
                {
                    "base_liquida": "agua",
                    "options": ["agua", "leche"],
                    "friendly_name": "Base Líquida Tang-Zhong"
                }
            )

class PanSaveButton(ButtonEntity):
    """Botón nativo para guardar la receta activa."""

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
    """Botón nativo para eliminar la receta activa."""

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
    """Botón con estado persistente de texto inyectado para el tipo de levadura."""

    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self.entity_id = ID_BOTON_LEVADURA

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return "pan_alternar_tipo_levadura"

    @property
    def unique_id(self) -> str: 
        return "porcentaje_panadero_pan_alternar_tipo_levadura_unique"

    @property
    def icon(self) -> str: return "mdi:swap-horizontal"

    @property
    def state(self) -> str:
        global _TIPO_LEVADURA_MEMORIA
        return _TIPO_LEVADURA_MEMORIA

    @property
    def extra_state_attributes(self) -> dict:
        global _TIPO_LEVADURA_MEMORIA
        return {
            "tipo_levadura": _TIPO_LEVADURA_MEMORIA,
            "options": ["fresca", "seca"]
        }

    async def async_press(self) -> None:
        """Se ejecuta al pulsar físicamente el botón en la pantalla. Aplica el factor de conversión."""
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


class PanToggleTangZhongButton(ButtonEntity):
    """Botón nativo con estado de texto para alternar el líquido base del Tang-Zhong."""

    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self.entity_id = ID_BOTON_TANG_ZHONG

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return "pan_alternar_tang_zhong_base"

    @property
    def unique_id(self) -> str: return "porcentaje_panadero_pan_alternar_tz_base_unique"

    @property
    def icon(self) -> str: return "mdi:water-percent-alert"

    @property
    def state(self) -> str:
        global _BASE_TANG_ZHONG_MEMORIA
        return _BASE_TANG_ZHONG_MEMORIA

    @property
    def extra_state_attributes(self) -> dict:
        global _BASE_TANG_ZHONG_MEMORIA
        return {
            "base_liquida": _BASE_TANG_ZHONG_MEMORIA,
            "options": ["agua", "leche"]
        }

    async def async_press(self) -> None:
        """Conmuta la base líquida y dispara el balanceo reactivo de harinas para recalcular líquidos."""
        global _BASE_TANG_ZHONG_MEMORIA
        _BASE_TANG_ZHONG_MEMORIA = "leche" if _BASE_TANG_ZHONG_MEMORIA == "agua" else "agua"
        self.async_write_ha_state()
        await self._hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": 1})

    async def async_added_to_hass(self) -> None:
        self.async_write_ha_state()


def obtener_tipo_levadura_actual() -> str:
    global _TIPO_LEVADURA_MEMORIA
    return _TIPO_LEVADURA_MEMORIA

def establecer_tipo_levadura_actual(tipo: str) -> None:
    global _TIPO_LEVADURA_MEMORIA
    if tipo in ["fresca", "seca"]:
        _TIPO_LEVADURA_MEMORIA = tipo

def obtener_base_tz_actual() -> str:
    global _BASE_TANG_ZHONG_MEMORIA
    return _BASE_TANG_ZHONG_MEMORIA

def establecer_base_tz_actual(base: str) -> None:
    global _BASE_TANG_ZHONG_MEMORIA
    if base in ["agua", "leche"]:
        _BASE_TANG_ZHONG_MEMORIA = base
