import logging
from datetime import datetime, timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.restore_state import RestoreEntity
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
        "prefermento_total", "tang_zhong_total", "inoculo_masa_madre",
        "harina_prefermento", "agua_prefermento", "levadura_prefermento", 
        "temperatura_agua_ideal", "malta", "azucar", "aove", "mantequilla", 
        "leche_polvo", "leche", "huevo", "formula_activa", 
        "tiempo_fermentacion_estimado", "hora_fin_fermentacion",
        "porcentaje_harina_sobre_masa", "temperatura_utilizada",
        "sensor_fisico_instalado", "porcentaje_hidratacion_final",
        "porcentaje_hidratacion_prefermento", "porcentaje_harina_prefermento",
        "porcentaje_harina_1_neta", "porcentaje_harina_2_neta", "porcentaje_harina_3_neta",
        "porcentaje_inoculo_puro", "porcentaje_hidratacion_total_real"
    ]

    # COMPROBACIÓN DINÁMICA
    if usar_sensor_fisico and entidad_termometro != "manual":
        claves_sensores.append("temperatura_real")

    sensores = []
    for clave in claves_sensores:
        if clave in [
            "formula_activa", "tiempo_fermentacion_estimado",
            "hora_fin_fermentacion", "porcentaje_harina_sobre_masa",
            "sensor_fisico_instalado", "porcentaje_hidratacion_final",
            "porcentaje_hidratacion_prefermento", "porcentaje_harina_prefermento",
            "porcentaje_harina_1_neta", "porcentaje_harina_2_neta", "porcentaje_harina_3_neta",
            "prefermento_total", "porcentaje_inoculo_puro", "porcentaje_hidratacion_total_real"
        ]:
            if clave in [
                "porcentaje_harina_sobre_masa", "porcentaje_hidratacion_final",
                "porcentaje_hidratacion_prefermento", "porcentaje_harina_prefermento",
                "porcentaje_harina_1_neta", "porcentaje_harina_2_neta", "porcentaje_harina_3_neta",
                "prefermento_total", "porcentaje_inoculo_puro", "porcentaje_hidratacion_total_real"
            ]:
                unidad = "%"
            else:
                unidad = None

            if clave == "formula_activa": icono = "mdi:notebook-check"
            elif clave == "tiempo_fermentacion_estimado": icono = "mdi:timer-sand"
            elif clave == "porcentaje_harina_sobre_masa": icono = "mdi:label-percent-outline"
            elif clave == "sensor_fisico_instalado": icono = "mdi:chip"
            elif clave in ["porcentaje_hidratacion_final", "porcentaje_hidratacion_prefermento", "porcentaje_hidratacion_total_real"]: icono = "mdi:water-percent"
            elif clave in ["porcentaje_harina_prefermento", "porcentaje_harina_1_neta", "porcentaje_harina_2_neta", "porcentaje_harina_3_neta", "porcentaje_inoculo_puro"]: icono = "mdi:blur-linear"
            else: icono = "mdi:clock-check-outline"
        else:
            unidad = "°C" if clave in ["temperatura_agua_ideal", "temperatura_utilizada", "temperatura_real"] else "g"
            if clave == "temperatura_utilizada": icono = "mdi:thermometer"
            elif clave == "temperatura_real": icono = "mdi:home-thermometer"
            elif clave == "temperatura_agua_ideal": icono = "mdi:thermometer-water"
            elif "agua" in clave or clave == "leche": icono = "mdi:water"
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
class PanSensor(SensorEntity, RestoreEntity):
    """Entidad de sensor panadero asíncrono con persistencia de disco."""

    def __init__(self, hass: HomeAssistant, tipo_sensor: str, unidad: str, icono: str, usar_fisico: bool, entidad_termometro: str):
        self._hass = hass
        self.tipo_sensor = tipo_sensor
        self._unidad = unidad
        self._icono = icono
        self.usar_fisico = usar_fisico
        self.entidad_termometro = entidad_termometro
        self._attributes = {}

        if tipo_sensor in ["formula_activa", "sensor_fisico_instalado"]:
            self._state = "---"
        else:
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
    def native_unit_of_measurement(self):
        """Fuerza a omitir la unidad si el sensor devuelve texto plano."""
        if self.tipo_sensor in ["formula_activa", "sensor_fisico_instalado"]:
            return None
        return self._unidad

    @property
    def icon(self): return self._icono
    @property
    def extra_state_attributes(self): return self._attributes

    async def async_added_to_hass(self):
        """Se ejecuta al arrancar el servidor. Escucha los cambios del obrador."""
        await super().async_added_to_hass()

        entidades_escucha = [
            "number.masa_final_objetivo", "number.harina_1", "number.harina_2", "number.harina_3",
            "number.agua_hidratacion", "number.sal", "number.levadura", "number.prefermento",
            "select.tipo_de_prefermento", "number.hidratacion_masa_madre", "number.inoculo_masa_madre",
            "select.harina_para_prefermento", "number.levadura_prefermento", "number.tang_zhong",
            "switch.habilitar_ingredientes_extras", "switch.calcular_hidratacion_real",
            "number.malta", "number.azucar", "number.aove", "number.mantequilla", "number.leche_en_polvo",
            "number.leche_liquida", "number.huevo", "number.temperatura_objetivo_masa",
            "number.temperatura_harina", "number.temperatura_prefermento", "number.temperatura_friccion_amasadora",
            "select.formula_de_receta", "button.alternar_tang_zhong_agua_leche", "select.origen_temperatura_levado",
            "number.temperatura_ambiente"
        ]
        if self.usar_fisico and self.entidad_termometro != "manual":
            entidades_escucha.append(self.entidad_termometro)

        @callback
        def _on_state_change(event):
            self.calcular_matematicas_panaderas()
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(self.hass, entidades_escucha, _on_state_change)
        )
        self.calcular_matematicas_panaderas()
    def calcular_matematicas_panaderas(self):
        """Procesa las ecuaciones panaderas leyendo tus ID reales de Lovelace."""
        try:
            def get_float(entity_id, default_val=0.0):
                state = self.hass.states.get(entity_id)
                if not state or state.state in ["unavailable", "unknown", ""]:
                    return default_val
                try: return float(state.state)
                except (ValueError, TypeError): return default_val

            def get_str(entity_id, default_val=""):
                state = self.hass.states.get(entity_id)
                if not state or state.state in ["unavailable", "unknown", ""]:
                    return default_val
                return str(state.state)

            masa_final = get_float("number.masa_final_objetivo", 1000.0)
            pct_h1 = get_float("number.harina_1", 100.0)
            pct_h2 = get_float("number.harina_2", 0.0)
            pct_h3 = get_float("number.harina_3", 0.0)
            pct_agua = get_float("number.agua_hidratacion", 60.0)
            pct_sal = get_float("number.sal", 2.0)
            pct_leva = get_float("number.levadura", 0.7)
            pct_pref = get_float("number.prefermento", 0.0)
            pct_tz = get_float("number.tang_zhong", 0.0)

            tipo_pref = get_str("select.tipo_de_prefermento", "poolish").lower()
            hyd_mm = get_float("number.hidratacion_masa_madre", 100.0)
            h_para_pref = get_str("select.harina_para_prefermento", "harina 1").lower()
            pct_leva_pref = get_float("number.levadura_prefermento", 0.0)

            st_extras = self.hass.states.get("switch.habilitar_ingredientes_extras")
            st_hidra = self.hass.states.get("switch.calcular_hidratacion_real")
            extras_on = st_extras.state.lower().strip() == "on" if st_extras else False
            hidratacion_real_on = st_hidra.state.lower().strip() == "on" if st_hidra else False

            r_malta = (get_float("number.malta", 0.0) / 100) if extras_on else 0
            r_azucar = (get_float("number.azucar", 0.0) / 100) if extras_on else 0
            r_aove = (get_float("number.aove", 0.0) / 100) if extras_on else 0
            r_mantequilla = (get_float("number.mantequilla", 0.0) / 100) if extras_on else 0
            r_leche_polvo = (get_float("number.leche_en_polvo", 0.0) / 100) if extras_on else 0
            pct_leche = get_float("number.leche_liquida", 0.0) if extras_on else 0
            pct_huevo = get_float("number.huevo", 0.0) if extras_on else 0

            from .button import obtener_tipo_levadura_actual, obtener_base_tz_actual
            tipo_leva_activa = obtener_tipo_levadura_actual()
            base_tz_activa = obtener_base_tz_actual()

            r_leva_pref_neta = 0.0
            if pct_pref > 0 and tipo_pref in ["poolish", "biga"] and pct_leva_pref > 0:
                f_harina = 0.5 if tipo_pref == "poolish" else 0.6667
                r_leva_pref_neta = (pct_pref / 100) * f_harina * (pct_leva_pref / 100)

            # LÓGICA DE DIVISOR CIENTÍFICO COMPENSADO
            if hidratacion_real_on and extras_on:
                agua_oculta_leche_ratio = (pct_leche / 100) * 0.88
                agua_oculta_huevo_ratio = (pct_huevo / 100) * 0.75
                pct_agua_ajustado = max(0.0, pct_agua - (agua_oculta_leche_ratio * 100) - (agua_oculta_huevo_ratio * 100))
                divisor = 1 + (pct_agua_ajustado / 100) + (pct_sal / 100) + (pct_leva / 100) + r_malta + r_azucar + r_aove + r_mantequilla + r_leche_polvo + (pct_leche / 100) + (pct_huevo / 100) + r_leva_pref_neta
            else:
                pct_agua_ajustado = pct_agua
                divisor = 1 + (pct_agua / 100) + (pct_sal / 100) + (pct_leva / 100) + r_malta + r_azucar + r_aove + r_mantequilla + r_leche_polvo + (pct_leche / 100) + (pct_huevo / 100) + r_leva_pref_neta

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
            leche_state = round(h_total * (pct_leche / 100), 1)
            huevo_state = round(h_total * (pct_huevo / 100), 1)

            pref_total_raw = h_total * (pct_pref / 100)

            # === DECLARACIÓN DE VARIABLES DE RESPALDO ===
            h_desc, g_inoculo_state, h_pref_raw, a_pref_raw, l_pref_state = 0.0, 0.0, 0.0, 0.0, 0.0

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
                    a_total_prefermento = pref_total_raw - h_total_prefermento

                    g_inoculo_state = round(h_total_prefermento * (pct_inoculo / 100) * factor_hyd, 1)
                    h_en_inoculo = g_inoculo_state / factor_hyd if factor_hyd != 0 else g_inoculo_state / 2
                    a_en_inoculo = g_inoculo_state - h_en_inoculo

                    # Filtramos para medir estrictamente la harina y agua NUEVA de refresco
                    h_pref_raw = h_total_prefermento - h_en_inoculo
                    a_pref_raw = a_total_prefermento - a_en_inoculo
                    
                    # La harina descontada del tazón hoy es solo la nueva del refresco
                    h_desc = h_pref_raw

            h_pref_state = round(h_pref_raw, 1)
            a_pref_state = round(a_pref_raw, 1)

            if tipo_pref == "masa madre":
                pref_total_state = round(g_inoculo_state + h_pref_state + a_pref_state, 1)
            else:
                pref_total_state = round(h_pref_state + a_pref_state + l_pref_state, 1)

            if pct_pref == 0: pref_total_state = 0.0

            h1_bruta = h_total * (pct_h1 / 100)
            h2_bruta = h_total * (pct_h2 / 100)
            h3_bruta = h_total * (pct_h3 / 100)

            h1_final_state = h1_bruta
            h2_final_state = h2_bruta
            h3_final_state = h3_bruta

            if "1" in h_para_pref: h1_final_state = h1_bruta - h_desc
            elif "2" in h_para_pref:
                if pct_h2 > 0 and (h2_bruta - h_desc) >= 0: h2_final_state = h2_bruta - h_desc
                else: h1_final_state = h1_bruta - h_desc
            elif "3" in h_para_pref:
                if pct_h3 > 0 and (h3_bruta - h_desc) >= 0: h3_final_state = h3_bruta - h_desc
                else: h1_final_state = h1_bruta - h_desc

            # SEPARACIÓN DE TEMPERATURAS
            st_origen = self.hass.states.get("select.origen_temperatura_levado")
            origen_temp = st_origen.state if st_origen else "Manual (Slider)"

            def get_termometro_real(entity_id, de_respaldo=22.0):
                st_term = self.hass.states.get(entity_id)
                if not st_term or st_term.state in ["unavailable", "unknown", ""]:
                    return de_respaldo
                try:
                    valor_limpio = str(st_term.state).replace("°C", "").replace("°F", "").strip()
                    return float(valor_limpio)
                except (ValueError, TypeError):
                    return de_respaldo

            # 1. TEMPERATURA A UTILIZAR PARA ESTIMAR LOS TIEMPOS DE FERMENTACIÓN
            if origen_temp == "Sensor Físico" and self.usar_fisico and self.entidad_termometro != "manual":
                t_fermentacion = get_termometro_real(self.entidad_termometro, 22.0)
            else:
                t_fermentacion = get_float("number.temperatura_ambiente", 22.0)

            # 2. TEMPERATURA SENSOR FÍSICO PARA CALCULAR LA TEMPERATURA DEL AGUA
            if self.usar_fisico and self.entidad_termometro != "manual":
                t_cocina_real = get_termometro_real(self.entidad_termometro, 22.0)
            else:
                t_cocina_real = get_float("number.temperatura_ambiente", 22.0)

            t_objetivo = get_float("number.temperatura_objetivo_masa", 24.0)
            t_harina = get_float("number.temperatura_harina", 20.0)
            t_friccion = get_float("number.temperatura_friccion_amasadora", 0.0)

            # MATEMÁTICAS APLICADAS DEL TANG-ZHONG (Relación 1:5)
            g_harina_tz = 0.0
            g_liquido_tz = 0.0
            g_leche_en_tz = 0.0
            g_agua_en_tz = 0.0

            if pct_tz > 0:
                g_harina_tz = h_total * (pct_tz / 100)
                g_liquido_tz = g_harina_tz * 5.0

                self._attributes["harina_tang_zhong_g"] = round(g_harina_tz, 1)
                self._attributes["liquido_tang_zhong_g"] = round(g_liquido_tz, 1)
                self._attributes["base_liquida_tang_zhong"] = base_tz_activa

            # DESCONTAMOS LA HARINA DEL ESCALDADO DE LA HARINA 1 NETA DE LA BÁSCULA
            h1_final_state = max(0.0, h1_final_state - g_harina_tz)

            h1_final_state = round(h1_final_state, 1)
            h2_final_state = round(h2_final_state, 1)
            h3_final_state = round(h3_final_state, 1)

            # EQUILIBRIO DE AGUA NETA Y LÍQUIDOS COMPENSADOS
            if hidratacion_real_on and extras_on:
                agua_neta_state = round(h_total * (pct_agua_ajustado / 100), 1)
            else:
                if tipo_pref == "masa madre":
                    g_prefermento_reales = round(g_inoculo_state + h_pref_state + a_pref_state, 1)
                else:
                    g_prefermento_reales = round(h_pref_state + a_pref_state + l_pref_state, 1)
                if pct_pref == 0: g_prefermento_reales = 0.0

                suma_otros = h1_final_state + h2_final_state + h3_final_state + sal_state + leva_state + malta_state + azucar_state + aove_state + mantequilla_state + leche_polvo_state + leche_state + huevo_state + g_prefermento_reales + g_harina_tz
                agua_neta_state = round(masa_final - suma_otros, 1)

            # DEDUCCIÓN INTELIGENTE DEL LÍQUIDO CON AVISO DE ASISTENCIA DE AGUA
            if pct_tz > 0:
                if base_tz_activa == "leche" and extras_on and leche_state > 0:
                    if leche_state >= g_liquido_tz:
                        g_leche_en_tz = g_liquido_tz
                        leche_state = round(leche_state - g_liquido_tz, 1)
                    else:
                        g_leche_en_tz = leche_state
                        g_agua_en_tz = g_liquido_tz - leche_state
                        leche_state = 0.0
                        agua_neta_state = round(max(0.0, agua_neta_state - g_agua_en_tz), 1)
                else:
                    g_agua_en_tz = g_liquido_tz
                    agua_neta_state = round(max(0.0, agua_neta_state - g_liquido_tz), 1)

                self._attributes["leche_utilizada_tz_g"] = round(g_leche_en_tz, 1)
                self._attributes["agua_asistencia_tz_g"] = round(g_agua_en_tz, 1)
                self._attributes["escaldado_mixto"] = g_agua_en_tz > 0.0

            # CÁLCULO DEL AGUA IDEAL (SÓLO CUENTA EL PREFERMENTO SI ESTÁ ACTIVO)
            tiene_prefermento = (
                pct_pref > 0
                and tipo_pref not in ["", "ninguno", "none", "no", "false", "0"]
            )

            if tiene_prefermento:
                t_pref = get_float("number.temperatura_prefermento", 20.0)
                t_agua_calc = round((t_objetivo * 4) - (t_cocina_real + t_harina + t_pref + t_friccion), 1)
            else:
                t_agua_calc = round((t_objetivo * 3) - (t_cocina_real + t_harina + t_friccion), 1)

            # NORMALIZACIÓN CORRECTA DE LA LEVADURA
            if tipo_leva_activa == "seca":
                pct_leva_normalizado = pct_leva * 3.0
            else:
                pct_leva_normalizado = pct_leva

            # VELOCIDAD METABÓLICA BASE REAL REFERENCIADA A 24ºC
            velocidad_levadura = pct_leva_normalizado * 0.25 if pct_leva_normalizado > 0 else 0.0

            velocidad_masa_madre = 0.0
            if tipo_pref == "masa madre" and pct_pref > 0:
                pct_inoculo_real = get_float("number.inoculo_masa_madre", 33.3)
                pct_inoculo_calculo = max(5.0, pct_inoculo_real)
                velocidad_masa_madre = (pct_inoculo_calculo / 100.0) * (pct_pref / 20.0) * 0.15

            velocidad_total_combinada = velocidad_levadura + velocidad_masa_madre

            if velocidad_total_combinada <= 0.005:
                texto_tiempo_levado, texto_reloj_listo = "---", "---"
            else:
                tiempo_base_horas = 1.0 / velocidad_total_combinada

                # FACTOR EXPO COMPENSADO (CURVA REAL DE FERMENTACIÓN ARRHENIUS)
                if t_fermentacion >= 24.0:
                    t_ambiente_limite = min(38.0, t_fermentacion)
                    factor_temperatura = 2.0 ** ((24.0 - t_ambiente_limite) / 10.0)
                else:
                    factor_temperatura = 2.5 ** ((24.0 - t_fermentacion) / 10.0)

                horas_totales_estimadas = tiempo_base_horas * factor_temperatura
                minutos_totales = int(round(horas_totales_estimadas * 60))
                horas_print = minutos_totales // 60
                minutos_print = minutos_totales % 60
                texto_tiempo_levado = f"{horas_print}h {minutos_print}m"

                hora_actual = datetime.now()
                hora_futura = hora_actual + timedelta(minutes=minutos_totales)
                texto_reloj_listo = hora_futura.strftime("%H:%M")

            # VOLCADO DE ESTADOS DE SALIDA DE LOS SENSORES
            if tipo_pref == "masa madre":
                g_prefermento_reales = round(g_inoculo_state + h_pref_state + a_pref_state, 1)
            else:
                g_prefermento_reales = round(h_pref_state + a_pref_state + l_pref_state, 1)
            if pct_pref == 0: g_prefermento_reales = 0.0

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
            elif self.tipo_sensor == "prefermento_total":
                if h_total > 0:
                    if tipo_pref == "masa madre":
                        self._state = round(((g_inoculo_state + h_pref_state + a_pref_state) / h_total) * 100, 1)
                    else:
                        self._state = round(((h_pref_state + a_pref_state + l_pref_state) / h_total) * 100, 1)
                else:
                    self._state = 0.0
                if pct_pref == 0: self._state = 0.0
                self._attributes["gramos_totales_reales"] = g_prefermento_reales

            elif self.tipo_sensor == "tang_zhong_total":
                g_total_tz = g_harina_tz + g_liquido_tz
                self._state = round(g_total_tz, 1)
                self._attributes["harina_g"] = round(g_harina_tz, 1)
                self._attributes["liquido_total_g"] = round(g_liquido_tz, 1)
                self._attributes["leche_utilizada_g"] = round(g_leche_en_tz, 1)
                self._attributes["agua_asistencia_g"] = round(g_agua_en_tz, 1)
                self._attributes["base_solicitada"] = base_tz_activa
                self._attributes["escaldado_mixto_por_descubierto"] = g_agua_en_tz > 0.0
            elif self.tipo_sensor == "inoculo_masa_madre": self._state = g_inoculo_state
            elif self.tipo_sensor == "harina_prefermento": self._state = h_pref_state
            elif self.tipo_sensor == "agua_prefermento": self._state = a_pref_state
            elif self.tipo_sensor == "levadura_prefermento": self._state = l_pref_state
            elif self.tipo_sensor == "harina_1_neta": self._state = h1_final_state
            elif self.tipo_sensor == "harina_2_neta": self._state = h2_final_state
            elif self.tipo_sensor == "harina_3_neta": self._state = h3_final_state
            elif self.tipo_sensor == "agua_neta": self._state = agua_neta_state
            elif self.tipo_sensor == "temperatura_agua_ideal": self._state = t_agua_calc
            elif self.tipo_sensor == "tiempo_fermentacion_estimado": self._state = texto_tiempo_levado
            elif self.tipo_sensor == "hora_fin_fermentacion": self._state = texto_reloj_listo
            elif self.tipo_sensor == "temperatura_utilizada":
                self._state = round(t_fermentacion, 1)
                self._attributes["usar_sensor_fisico"] = "true" if self.usar_fisico else "false"
                self._attributes["entidad_termometro"] = self.entidad_termometro
            elif self.tipo_sensor == "temperatura_real":
                self._state = round(t_cocina_real, 1)
            elif self.tipo_sensor == "sensor_fisico_instalado":
                if self.usar_fisico and self.entidad_termometro != "manual":
                    st_term = self.hass.states.get(self.entidad_termometro)
                    if not st_term or st_term.state in ["unavailable", "unknown", ""]:
                        self._state = "unavailable"
                    else:
                        self._state = "true"
                else:
                    self._state = "false"
            elif self.tipo_sensor == "porcentaje_harina_sobre_masa":
                if masa_final > 0: self._state = round((h_total / masa_final) * 100, 1)
                else: self._state = 0.0
            elif self.tipo_sensor == "porcentaje_hidratacion_final":
                # LÓGICA PURA DE RECETA: Slider Agua - Agua Prefermento Nueva - Agua Inóculo Vieja
                if h_total > 0:
                    pct_pref_agua = (a_pref_state / h_total) * 100
                    pct_inoculo_agua = 0.0
                    if pct_pref > 0 and tipo_pref == "masa madre":
                        pct_inoculo_agua = ((g_inoculo_state / 2) / h_total) * 100
                    
                    # Restamos de la hidratación teórica para saber cuánto queda por echar limpio en el tazón
                    self._state = round(pct_agua - pct_pref_agua - pct_inoculo_agua, 1)
                else:
                    self._state = 0.0
            elif self.tipo_sensor == "porcentaje_hidratacion_prefermento":
                if h_total > 0: self._state = round((a_pref_state / h_total) * 100, 1)
                else: self._state = 0.0
            elif self.tipo_sensor == "porcentaje_harina_prefermento":
                if h_total > 0: self._state = round((h_desc / h_total) * 100, 1)
                else: self._state = 0.0
            elif self.tipo_sensor == "porcentaje_harina_1_neta":
                if h_total > 0: self._state = round((h1_final_state / h_total) * 100, 1)
                else: self._state = 0.0
            elif self.tipo_sensor == "porcentaje_harina_2_neta":
                if h_total > 0: self._state = round((h2_final_state / h_total) * 100, 1)
                else: self._state = 0.0
            elif self.tipo_sensor == "porcentaje_harina_3_neta":
                if h_total > 0: self._state = round((h3_final_state / h_total) * 100, 1)
                else: self._state = 0.0
            elif self.tipo_sensor == "porcentaje_inoculo_puro":
                if h_total > 0 and pct_pref > 0 and tipo_pref == "masa madre":
                    self._state = round((g_inoculo_state / h_total) * 100, 1)
                else: self._state = 0.0
            elif self.tipo_sensor == "porcentaje_hidratacion_total_real":
                if h_total > 0:
                    # Aquí la hidratación total siempre va a cantar exactamente el valor de tu slider
                    self._state = round(pct_agua, 1)
                else:
                    self._state = 0.0
            elif self.tipo_sensor in ["formula_active", "formula_activa"]:
                from . import const
                self._state = const.RECETA_ACTIVA_MEMORIA

            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Error crítico en el cálculo matemático panadero: %s", ex)
