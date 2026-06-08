import os
import json
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

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
        PanSelectMenu(hass, "origen_temperatura_levado", opciones_origen, "mdi:thermometer-alert")
    ]
    async_add_entities(desplegables, True)


class PanSelectMenu(SelectEntity):
    """Representación nativa de un menú desplegable panadero."""

    def __init__(self, hass: HomeAssistant, clave: str, opciones: list, icono: str):
        self._hass = hass
        self._clave = clave
        self._options = opciones
        self._icon = icono
        
        if clave == "formula_de_receta":
            self._current_option = "---"
        elif clave == "tipo_de_prefermento":
            self._current_option = "poolish"
        elif clave == "harina_para_prefermento":
            self._current_option = "harina 1"
        elif clave == "origen_temperatura_levado":
            self._current_option = "Manual (Slider)"
        else:
            self._current_option = "---"

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return self._clave

    @property
    def unique_id(self) -> str: 
        return f"porcentaje_panadero_select_{self._clave}_unique"

    @property
    def options(self) -> list:
        """Devuelve las opciones válidas de la lista estática (evita I/O síncrono)."""
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

    @property
    def current_option(self) -> str: return self._current_option

    @property
    def icon(self) -> str: return self._icon

    def _leer_formulas_sync(self):
        """Método seguro ejecutado en el pool de hilos para cargar el archivo."""
        ruta_json = self._hass.config.path("custom_components/porcentaje_panadero/formulas.json")
        if os.path.exists(ruta_json):
            try:
                with open(ruta_json, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as ex:
                _LOGGER.error("Error leyendo archivo de recetas: %s", ex)
        return None

    async def async_recargar_recetas(self):
        """Actualiza de forma asíncrona la lista de recetas desde el disco sin bloquear a HA."""
        data = await self._hass.async_add_executor_job(self._leer_formulas_sync)
        if data:
            self._options = ["---"] + list(data.keys())
        else:
            self._options = ["---"]
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Se ejecuta al arrancar. Carga las recetas e inicia los escuchadores."""
        await super().async_added_to_hass()

        if self._clave == "formula_de_receta":
            await self.async_recargar_recetas()

        if self._clave in ["harina_para_prefermento", "tipo_de_prefermento", "formula_de_receta"]:
            @callback
            def _on_bascula_change(event):
                # RESTAURADO: Si tocas una báscula, la receta vuelve a "---" para poder editarla libremente
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

            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, 
                    ["number.harina_1", "number.harina_2", "number.harina_3", "number.prefermento"], 
                    _on_bascula_change
                )
            )

    async def async_select_option(self, option: str) -> None:
        """Cambia la opción seleccionada y ejecuta los servicios correspondientes."""
        if self._clave == "formula_de_receta":
            # Si vas a seleccionar, nos aseguramos primero de refrescar la lista por si guardaste una nueva
            await self.async_recargar_recetas()
            
        if option not in self._options:
            # Forzado dinámico si Lovelace guardó e intentó seleccionar en el mismo milisegundo
            self._options.append(option)

        self._current_option = option
        self.async_write_ha_state()

        if option == "---":
            return

        tipo_limpio = str(option).lower().strip()
        if self._clave == "tipo_de_prefermento":
            if tipo_limpio == "poolish":
                if self.hass.states.get("number.levadura_prefermento") is not None:
                    await self.hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": 0.20})
            elif tipo_limpio == "biga":
                if self.hass.states.get("number.levadura_prefermento") is not None:
                    await self.hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": 0.33})
            elif tipo_limpio == "masa madre":
                if self.hass.states.get("number.levadura_prefermento") is not None:
                    await self.hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": 0.0})

        if self._clave == "formula_de_receta":
            await self.hass.services.async_call(DOMAIN, "cargar_formula_en_sliders", {"nombre": option})
            self._current_option = "---"
            self.async_write_ha_state()

        await self.hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": 1})
