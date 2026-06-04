import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)

DOMAIN = "porcentaje_panadero"

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Da de alta los sensores de forma pasiva aislando los hilos del arranque."""
    config_app = hass.data[DOMAIN][entry.entry_id]
    usar_sensor_fisico = config_app.get("usar_sensor_fisico", False)
    entidad_termometro = config_app.get("entidad_termometro", "manual")

    claves_sensores = [
        "harina_total", "agua_total", "harina_1_neta", "harina_2_neta", 
        "harina_3_neta", "agua_neta", "sal_neta", "levadura_neta", 
        "prefermento_total", "inoculo_masa_madre", "harina_prefermento", 
        "agua_prefermento", "levadura_prefermento", "temperatura_agua_ideal", 
        "malta", "azucar", "aove", "mantequilla", "leche_polvo", "leche", "huevo"
    ]

    sensores = []
    for clave in claves_sensores:
        unidad = "°C" if clave == "temperatura_agua_ideal" else "g"
        if "agua" in clave or clave == "leche": icono = "mdi:water"
        elif "harina" in clave or clave == "malta": icono = "mdi:grain"
        elif "levadura" in clave: icono = "mdi:yeast"
        elif clave == "sal_neta": icono = "mdi:shaker-outline"
        elif clave == "azucar": icono = "mdi:spoon-sugar"
        elif clave == "aove": icono = "mdi:oil"
        elif clave == "mantequilla": icono = "mdi:cow"
        elif clave == "huevo": icono = "mdi:egg"
        else: icono = "mdi:scale-balance"
        
        sensores.append(PanSensor(hass, clave, unidad, icono, usar_sensor_fisico, entidad_termometro))
    
    async_add_entities(sensores, False)

class PanSensor(SensorEntity):
    """Entidad de sensor panadero asincrono puro de alto rendimiento."""

    def __init__(self, hass: HomeAssistant, tipo_sensor: str, unidad: str, icono: str, usar_fisico: bool, entidad_termometro: str):
        self._hass = hass
        self.tipo_sensor = tipo_sensor
        self._unidad = unidad
        self._icono = icono
        self.usar_fisico = usar_fisico
        self.entidad_termometro = entidad_termometro
        self._state = 0.0

    @property
    def has_entity_name(self) -> bool: return True

    @property
    def translation_key(self) -> str: return self.tipo_sensor

    @property
    def unique_id(self): return f"porcentaje_panadero_{self.tipo_sensor}_unique"

    @property
    def native_value(self): return self._state

    @property
    def native_unit_of_measurement(self): return self._unidad

    @property
    def icon(self): return self._icono

    async def async_added_to_hass(self):
        """Activa la escucha pasiva enlazando estrictamente tus 26 mandos cortos de Lovelace."""
        await super().async_added_to_hass()
        
        entidades_escucha = [
            "number.masa_final_objetivo",
            "number.harina_1",
            "number.harina_2",
            "number.harina_3",
            "number.agua_hidratacion",
            "number.sal",
            "number.levadura",
            "number.prefermento",
            "select.tipo_de_prefermento",
            "number.hidratacion_masa_madre",
            "number.inoculo_masa_madre",
            "select.harina_para_prefermento",
            "number.levadura_prefermento",
            "switch.habilitar_ingredientes_extras",
            "number.malta",
            "number.azucar",
            "number.aove",
            "number.mantequilla",
            "number.leche_en_polvo",
            "number.leche_liquida",
            "number.huevo",
            "number.temperatura_objetivo_masa",
            "number.temperatura_harina",
            "number.temperatura_prefermento",
            "number.temperatura_friccion_amasadora",
            "select.formula_de_receta"
        ]

        if self.usar_fisico and self.entidad_termometro != "manual":
            entidades_escucha.append(self.entidad_termometro)
        else:
            entidades_escucha.append("number.temperatura_ambiente")

        @callback
        def _on_state_change(event):
            self.calcular_matematicas_panaderas()
            self.async_write_ha_state()
            
        self.async_on_remove(
            async_track_state_change_event(self.hass, entidades_escucha, _on_state_change)
        )
        
        self._state = 0.0

    def calcular_matematicas_panaderas(self):
        """Procesa las ecuaciones panaderas leyendo tus ID reales de Lovelace."""
        try:
            def get_float(entity_id, default_val=0.0):
                state = self._hass.states.get(entity_id)
                if not state or state.state in ["unavailable", "unknown", ""]:
                    return default_val
                try:
                    return float(state.state)
                except (ValueError, TypeError):
                    return default_val

            def get_str(entity_id, default_val=""):
                state = self._hass.states.get(entity_id)
                if not state or state.state in ["unavailable", "unknown", ""]:
                    return default_val
                return state.state

            masa_final = get_float("number.masa_final_objetivo", 1000.0)
            pct_h1 = get_float("number.harina_1", 100.0)
            pct_h2 = get_float("number.harina_2", 0.0)
            pct_h3 = get_float("number.harina_3", 0.0)
            pct_agua = get_float("number.agua_hidratacion", 60.0)
            pct_sal = get_float("number.sal", 2.0)
            pct_leva = get_float("number.levadura", 0.7)
            pct_pref = get_float("number.prefermento", 0.0)
            
            tipo_pref = get_str("select.tipo_de_prefermento", "poolish").lower()
            hyd_mm = get_float("number.hidratacion_masa_madre", 100.0)
            h_para_pref = get_str("select.harina_para_prefermento", "harina 1").lower()
            pct_leva_pref = get_float("number.levadura_prefermento", 0.0)
            
            extras_on = get_str("switch.habilitar_ingredientes_extras") == "on"

            r_malta = (get_float("number.malta", 0.0) / 100) if extras_on else 0
            r_azucar = (get_float("number.azucar", 0.0) / 100) if extras_on else 0
            r_aove = (get_float("number.aove", 0.0) / 100) if extras_on else 0
            r_mantequilla = (get_float("number.mantequilla", 0.0) / 100) if extras_on else 0
            r_leche_polvo = (get_float("number.leche_en_polvo", 0.0) / 100) if extras_on else 0
            r_leche = (get_float("number.leche_liquida", 0.0) / 100) if extras_on else 0
            r_huevo = (get_float("number.huevo", 0.0) / 100) if extras_on else 0

            r_leva_pref_neta = 0.0
            if pct_pref > 0 and tipo_pref in ["poolish", "biga"] and pct_leva_pref > 0:
                f_harina = 0.5 if tipo_pref == "poolish" else 0.6667
                r_leva_pref_neta = (pct_pref / 100) * f_harina * (pct_leva_pref / 100)

            divisor = 1 + (pct_agua/100) + (pct_sal/100) + (pct_leva/100) + r_malta + r_azucar + r_aove + r_mantequilla + r_leche_polvo + r_leche + r_huevo + r_leva_pref_neta
            if divisor == 0: divisor = 1.627

            h_total = masa_final / divisor
            agua_total = h_total * (pct_agua / 100)

            sal_state = round(h_total * (pct_sal / 100), 1)
            leva_state = round(h_total * (pct_leva / 100), 1)
            malta_state = round(h_total * r_malta, 1)
            azucar_state = round(h_total * r_azucar, 1)
            aove_state = round(h_total * r_aove, 1)
            mantequilla_state = round(h_total * r_mantequilla, 1)
            leche_polvo_state = round(h_total * r_leche_polvo, 1)
            leche_state = round(h_total * r_leche, 1)
            huevo_state = round(h_total * r_huevo, 1)

            h_desc = 0.0
            pref_total_raw = h_total * (pct_pref / 100) if pct_pref > 0 else 0.0
            g_inoculo_state = 0.0
            h_pref_raw = 0.0
            a_pref_raw = 0.0
            l_pref_state = 0.0

            if pct_pref > 0:
                if tipo_pref == "biga":
                    h_pref_raw = pref_total_raw * 0.6667
                    a_pref_raw = pref_total_raw * 0.3333
                    l_pref_state = round((h_pref_raw * pct_leva_pref) / 100, 1)
                    h_desc = h_pref_raw
                elif tipo_pref == "poolish":
                    h_pref_raw = pref_total_raw * 0.5
                    a_pref_raw = pref_total_raw * 0.5
                    l_pref_state = round((h_pref_raw * pct_leva_pref) / 100, 1)
                    h_desc = h_pref_raw
                elif tipo_pref == "masa madre":
                    pct_inoculo = get_float("number.inoculo_masa_madre", 33.3)
                    
                    factor_hyd = 1 + (hyd_mm / 100)
                    h_total_prefermento = pref_total_raw / factor_hyd if factor_hyd != 0 else pref_total_raw / 2
                    
                    g_inoculo_state = round(h_total_prefermento * (pct_inoculo / 100) * factor_hyd, 1)
                    
                    h_en_inoculo = g_inoculo_state / factor_hyd if factor_hyd != 0 else g_inoculo_state / 2
                    a_en_inoculo = g_inoculo_state - h_en_inoculo
                    
                    h_pref_raw = h_total_prefermento - h_en_inoculo
                    a_pref_raw = (pref_total_raw - h_total_prefermento) - a_en_inoculo


            h_pref_state = round(h_pref_raw, 1)
            a_pref_state = round(a_pref_raw, 1)
            pref_total_state = round(g_inoculo_state + h_pref_state + a_pref_state, 1) if tipo_pref == "masa madre" else round(h_pref_state + a_pref_state + l_pref_state, 1)
            if pct_pref == 0: pref_total_state = 0.0

            h1_bruta = h_total * (pct_h1 / 100)
            h2_bruta = h_total * (pct_h2 / 100)
            h3_bruta = h_total * (pct_h3 / 100)

            h1_final_state = h1_bruta
            h2_final_state = h2_bruta
            h3_final_state = h3_bruta

            if "harina 1" in h_para_pref: h1_final_state = h1_bruta - h_desc
            elif "harina 2" in h_para_pref:
                if pct_h2 > 0 and (h2_bruta - h_desc) >= 0: h2_final_state = h2_bruta - h_desc
                else: h1_final_state = h1_bruta - h_desc
            elif "harina 3" in h_para_pref:
                if pct_h3 > 0 and (h3_bruta - h_desc) >= 0: h3_final_state = h3_bruta - h_desc
                else: h1_final_state = h1_bruta - h_desc

            h1_final_state = round(h1_final_state, 1)
            h2_final_state = round(h2_final_state, 1)
            h3_final_state = round(h3_final_state, 1)

            suma_otros = h1_final_state + h2_final_state + h3_final_state + sal_state + leva_state + malta_state + azucar_state + aove_state + mantequilla_state + leche_polvo_state + leche_state + huevo_state + pref_total_state
            agua_neta_state = round(masa_final - suma_otros, 1)

            if self.usar_fisico and self.entidad_termometro != "manual":
                state_termometro = self._hass.states.get(self.entidad_termometro)
                t_ambiente = float(state_termometro.state) if state_termometro and state_termometro.state not in ["unavailable", "unknown", ""] else 22.0
            else:
                t_ambiente = get_float("number.temperatura_ambiente", 22.0)

            t_objetivo = get_float("number.temperatura_objetivo_masa", 24.0)
            t_harina = get_float("number.temperatura_harina", 20.0)
            t_friccion = get_float("number.temperatura_friccion_amasadora", 0.0)
            
            if pct_pref > 0:
                t_agua_calc = round((t_objetivo * 4) - (t_ambiente + t_harina + get_float("number.temperatura_prefermento", 20.0) + t_friccion), 1)
            else:
                t_agua_calc = round((t_objetivo * 3) - (t_ambiente + t_harina + t_friccion), 1)

            if self.tipo_sensor == "harina_total": self._state = round(h_total, 1)
            elif self.tipo_sensor == "agua_total": self._state = round(agua_total, 1)
            elif self.tipo_sensor == "sal_neta": self._state = sal_state
            elif self.tipo_sensor == "levadura_neta": self._state = leva_state
            elif self.tipo_sensor == "malta": self._state = malta_state
            elif self.tipo_sensor == "azucar": self._state = azucar_state
            elif self.tipo_sensor == "aove": self._state = aove_state
            elif self.tipo_sensor == "mantequilla": self._state = mantequilla_state
            elif self.tipo_sensor == "leche_polvo": self._state = leche_polvo_state
            elif self.tipo_sensor == "leche": self._state = leche_state
            elif self.tipo_sensor == "huevo": self._state = huevo_state
            elif self.tipo_sensor == "prefermento_total": self._state = pref_total_state
            elif self.tipo_sensor == "inoculo_masa_madre": self._state = g_inoculo_state
            elif self.tipo_sensor == "harina_prefermento": self._state = h_pref_state
            elif self.tipo_sensor == "agua_prefermento": self._state = a_pref_state
            elif self.tipo_sensor == "levadura_prefermento": self._state = l_pref_state
            elif self.tipo_sensor == "harina_1_neta": self._state = h1_final_state
            elif self.tipo_sensor == "harina_2_neta": self._state = h2_final_state
            elif self.tipo_sensor == "harina_3_neta": self._state = h3_final_state
            elif self.tipo_sensor == "agua_neta": self._state = agua_neta_state
            elif self.tipo_sensor == "temperatura_agua_ideal": self._state = t_agua_calc

        except Exception as ex:
            _LOGGER.error("Error en calculo: %s", ex)
