import os
import json
import logging
import datetime
import homeassistant.util.dt as dt_util
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_point_in_time

_LOGGER = logging.getLogger(__name__)

DOMAIN = "porcentaje_panadero"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Levanta los desplegables nativos bajo la arquitectura moderna."""
    config_app = hass.data[DOMAIN][entry.entry_id]
    usar_sensor_fisico = config_app.get("usar_sensor_fisico", False)

    opciones_origen = ["Manual (Slider)", "Sensor Físico"] if usar_sensor_fisico else ["Manual (Slider)"]

    desplegables = [
        PanSelectMenu(hass, "formula_de_receta", ["---"], "mdi:notebook-edit"),
        PanSelectMenu(hass, "tipo_de_prefermento", ["poolish", "biga", "masa madre"], "mdi:chart-bubble"),
        PanSelectMenu(hass, "harina_para_prefermento", ["harina 1", "harina 2", "harina 3"], "mdi:barley"),
        PanSelectMenu(hass, "origen_temperatura_levado", opciones_origen, "mdi:thermometer-alert"),
        
        PanSelectMenu(hass, "selector_harina_1", [], "mdi:barley"),
        PanSelectMenu(hass, "selector_harina_2", [], "mdi:barley"),
        PanSelectMenu(hass, "selector_harina_3", [], "mdi:barley"),
        PanSelectMenu(hass, "retirar_harina_del_inventario", [], "mdi:delete")
    ]
    async_add_entities(desplegables, True)

class PanSelectMenu(SelectEntity):
    """Representación nativa de un menú desplegable panadero."""

    def __init__(self, hass: HomeAssistant, clave: str, opciones: list, icono: str):
        self._hass = hass
        self._clave = clave
        self._options = opciones
        self._icon = icono

        if clave in ["formula_de_receta", "retirar_harina_del_inventario"]:
            self._current_option = "---"
        elif clave == "tipo_de_prefermento":
            self._current_option = "poolish"
        elif clave == "harina_para_prefermento":
            self._current_option = "harina 1"
        elif clave == "origen_temperatura_levado":
            self._current_option = "Manual (Slider)"
        elif clave == "selector_harina_1":
            self._current_option = "HARINA 1"
        elif clave == "selector_harina_2":
            self._current_option = "HARINA 2"
        elif clave == "selector_harina_3":
            self._current_option = "HARINA 3"
        else:
            self._current_option = "---"

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return self._clave

    @property
    def unique_id(self) -> str:
        return f"pan_select_{self._clave}"

    @property
    def icon(self) -> str: return self._icon

    @property
    def current_option(self) -> str | None:
        """Devuelve la opción activa forzando el estado neutro si el Core devuelve un valor corrupto."""
        if not self._current_option or str(self._current_option) in ["unknown", "unavailable", "None", "none", "", "---"]:
            if self._clave in ["formula_de_receta", "retirar_harina_del_inventario"]:
                return "---"
            elif self._clave == "tipo_de_prefermento":
                return "poolish"
            elif self._clave == "harina_para_prefermento":
                return "harina 1"
            elif self._clave == "origen_temperatura_levado":
                return "Manual (Slider)"
            elif self._clave == "selector_harina_1":
                return "HARINA 1"
            elif self._clave == "selector_harina_2":
                return "HARINA 2"
            elif self._clave == "selector_harina_3":
                return "HARINA 3"
            else:
                return "---"
        return self._current_option

    def _leer_inventario_harinas_sync(self):
        """Lectura síncrona interna delegada de forma segura en un hilo executor."""
        ruta_harinas = self._hass.config.path("custom_components/porcentaje_panadero/harinas.json")
        if os.path.exists(ruta_harinas):
            try:
                with open(ruta_harinas, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as ex:
                _LOGGER.error("Error leyendo inventario de harinas: %s", ex)
        return ["Harina de Media Fuerza", "Harina de Fuerza", "Harina de Gran Fuerza", "Harina de Centeno", "Harina de Espelta"]

    @property
    def options(self) -> list:
        """Devuelve las opciones desde memoria RAM aislando los comodines comerciales."""
        if self._clave in ["selector_harina_1", "selector_harina_2", "selector_harina_3", "retirar_harina_del_inventario"]:
            if not self._options:
                base_init = ["Harina de Media Fuerza", "Harina de Fuerza", "Harina de Gran Fuerza", "Harina de Centeno", "Harina de Espelta"]
                
                if self._clave in ["selector_harina_1", "selector_harina_2", "selector_harina_3"]:
                    for texto_base in ["HARINA 1", "HARINA 2", "HARINA 3"]:
                        if texto_base not in base_init:
                            base_init.append(texto_base)
                    return base_init
                
                if self._clave == "retirar_harina_del_inventario":
                    return ["---"] + base_init
            
            return self._options

        if self._clave == "harina_para_prefermento":
            try:
                def get_f(eid):
                    st = self._hass.states.get(eid)
                    return float(st.state) if st and st.state not in ["unavailable", "unknown", ""] else 0.0

                h1 = get_f("number.harina_1")
                h2 = get_f("number.harina_2")
                h3 = get_f("number.harina_3")
                peso_h_total = get_f("sensor.harina_total")
                peso_pref = get_f("sensor.prefermento_total")

                st_tipo = self._hass.states.get("select.tipo_de_prefermento")
                tipo_pref = st_tipo.state.lower() if st_tipo else "poolish"
                hyd_mm = get_f("number.hidratacion_masa_madre")

                g_req = 0.0
                if peso_pref > 0:
                    if tipo_pref == "biga": g_req = peso_pref * 0.6667
                    elif tipo_pref == "poolish": g_req = peso_pref * 0.5
                    elif tipo_pref == "masa madre": g_req = peso_pref / (1 + (hyd_mm / 100))

                nuevas = []
                if h1 > 0 and (peso_h_total * (h1 / 100)) >= g_req: nuevas.append("harina 1")
                if h2 > 0 and (peso_h_total * (h2 / 100)) >= g_req: nuevas.append("harina 2")
                if h3 > 0 and (peso_h_total * (h3 / 100)) >= g_req: nuevas.append("harina 3")

                lista_final = nuevas if nuevas else ["harina 1"]

                if self._current_option not in lista_final:
                    self._current_option = "harina 1"

                return lista_final
            except Exception:
                return ["harina 1"]

        return self._options


    def _leer_formulas_sync(self):
        ruta_json = self._hass.config.path("custom_components/porcentaje_panadero/formulas.json")
        if os.path.exists(ruta_json):
            try:
                with open(ruta_json, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as ex:
                _LOGGER.error("Error leyendo archivo de recetas: %s", ex)
                return None

    async def async_recargar_recetas(self):
        """Lee las fórmulas y actualiza las opciones del menú desplegable."""
        data = await self._hass.async_add_executor_job(self._leer_formulas_sync)
        if data:
            self._options = ["---"] + list(data.keys())
        else:
            self._options = ["---"]
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Se ejecuta al arrancar de forma asíncrona descargando el disco de hilos."""
        await super().async_added_to_hass()

        if self._clave == "formula_de_receta":
            await self.async_recargar_recetas()

        if self._clave in ["selector_harina_1", "selector_harina_2", "selector_harina_3", "retirar_harina_del_inventario"]:
            lista_json = await self._hass.async_add_executor_job(self._leer_inventario_harinas_sync)
            
            if self._clave in ["selector_harina_1", "selector_harina_2", "selector_harina_3"]:
                for texto_base in ["HARINA 1", "HARINA 2", "HARINA 3"]:
                    if texto_base not in lista_json:
                        lista_json.append(texto_base)
            
            if self._clave == "retirar_harina_del_inventario":
                if "---" not in lista_json:
                    lista_json = ["---"] + lista_json
            self._options = lista_json
            
            if self._options and self._current_option not in self._options:
                if self._clave == "selector_harina_1": self._current_option = "HARINA 1"
                elif self._clave == "selector_harina_2": self._current_option = "HARINA 2"
                elif self._clave == "selector_harina_3": self._current_option = "HARINA 3"
                else: self._current_option = "---"
            self.async_write_ha_state()

        if self._clave in ["harina_para_prefermento", "tipo_de_prefermento", "formula_de_receta"]:
            if not hasattr(self, "_debounce_timer"):
                self._debounce_timer = None

            @callback
            def _on_bascula_change(event):
                if self._debounce_timer is not None:
                    self._debounce_timer()
                    self._debounce_timer = None

                @callback
                def _ejecutar_actualizacion_inmediata(now):
                    self._debounce_timer = None
                    if self._clave == "formula_de_receta":
                        if self._current_option != "---":
                            self._current_option = "---"
                            self.async_write_ha_state()
                        return

                    if self._current_option == "unknown" or self._current_option not in self.options:
                        if self._clave == "harina_para_prefermento":
                            self._current_option = "harina 1"
                        elif self._clave == "tipo_de_prefermento":
                            self._current_option = "poolish"
                    else:
                        self._current_option = "---"
                    self.async_write_ha_state()

                import homeassistant.util.dt as dt_util
                from homeassistant.helpers.event import async_track_point_in_time
                
                momento_ejecucion = dt_util.utcnow() + datetime.timedelta(seconds=0.05)
                self._debounce_timer = async_track_point_in_time(
                    self.hass, _ejecutar_actualizacion_inmediata, momento_ejecucion
                )

            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    ["number.harina_1", "number.harina_2", "number.harina_3", "number.prefermento"],
                    _on_bascula_change
                )
            )

            if self._clave == "formula_de_receta":
                @callback
                async def _on_recetas_actualizadas(event):
                    await self.async_recargar_recetas()

                self.async_on_remove(
                    self.hass.bus.async_listen("porcentaje_panadero_recetas_actualizadas", _on_recetas_actualizadas)
                )

    async def async_select_option(self, option: str) -> None:
        """Se ejecuta al pulsar una opción en el menú desplegable."""
        if self._clave == "formula_de_receta":
            await self.async_recargar_recetas()

        if option not in self._options:
            self._options.append(option)

        if self._clave == "formula_de_receta" and option != "---":
            from . import const
            const.RECETA_ACTIVA_MEMORIA = option.replace("_", " ").title()
            self._hass.states.async_set("sensor.formula_activa", const.RECETA_ACTIVA_MEMORIA, {
                "friendly_name": "Receta en el Obrador", "icon": "mdi:notebook-check"
            })

        self._current_option = option
        self.async_write_ha_state()

        if option == "---":
            return

        tipo_limpio = str(option).lower().strip()
        if self._clave == "tipo_de_prefermento":
            if tipo_limpio == "poolish" and self.hass.states.get("number.levadura_prefermento") is not None:
                await self.hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": 0.20})
            elif tipo_limpio == "biga" and self.hass.states.get("number.levadura_prefermento") is not None:
                await self.hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": 0.33})
            elif tipo_limpio == "masa madre" and self.hass.states.get("number.levadura_prefermento") is not None:
                await self.hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": 0.0})

        if self._clave == "formula_de_receta":
            await self.hass.services.async_call(DOMAIN, "cargar_formula_en_sliders", {"nombre": option})
            self._current_option = "---"
            self.async_write_ha_state()

        if self._clave == "retirar_harina_del_inventario":
            return

        from . import const
        if const.CARGANDO_RECETA_BLOQUEO:
            return

        await self.hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": 1})
