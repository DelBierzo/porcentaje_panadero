import os
import json
import logging
import asyncio
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from .button import (
    obtener_tipo_levadura_actual, 
    establecer_tipo_levadura_actual, 
    ID_BOTON_LEVADURA,
    obtener_base_tz_actual,
    establecer_base_tz_actual,
    ID_BOTON_TANG_ZHONG
)
from .const import DOMAIN, RECETA_ACTIVA_MEMORIA

_LOGGER = logging.getLogger(__name__)
DOMAIN = "porcentaje_panadero"

PLATFORMS = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TEXT,
    Platform.BUTTON,
]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configuración inicial por archivo YAML."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura la integración de forma oficial desde Ajustes."""
    _LOGGER.info("Inicializando cerebro de Porcentaje Panadero.")
    
    ruta_json = hass.config.path("custom_components/porcentaje_panadero/formulas.json")
    if not os.path.exists(ruta_json):
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4, ensure_ascii=False)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "usar_sensor_fisico": entry.data.get("usar_sensor_fisico", False),
        "entidad_termometro": entry.data.get("entidad_termometro", "manual")
    }

    def buscar_estado_entidad(nombre_base, default_val=0.0):
        """Busca la entidad en el Core probando todas las variantes unificadas posibles."""
        if nombre_base in ["nombre_nueva_formula", "pan_nombre_nueva_formula"]:
            st_texto = hass.states.get("text.nombre_nueva_formula")
            if st_texto and st_texto.state not in ["unavailable", "unknown", ""]:
                return st_texto.state

        limpio = nombre_base.replace("pan_pct_", "").replace("pan_t_", "").replace("pan_", "")
        
        equivalencias = {
            "masa_final": "number.masa_final_objetivo",
            "harina_1": "number.harina_1",
            "harina_2": "number.harina_2",
            "harina_3": "number.harina_3",
            "agua": "number.agua_hidratacion",
            "sal": "number.sal",
            "levadura": "number.levadura",
            "prefermento": "number.prefermento",
            "hidratacion_masa_madre": "number.hidratacion_masa_madre",
            "levadura_prefermento": "number.levadura_prefermento",
            "tang_zhong": "number.tang_zhong",
            "malta": "number.malta",
            "azucar": "number.azucar",
            "aove": "number.aove",
            "mantequilla": "number.mantequilla",
            "leche_en_polvo": "number.leche_en_polvo",
            "leche_liquida": "number.leche_liquida",
            "leche": "number.leche_liquida",
            "huevo": "number.huevo",
            "t_objetivo_masa": "number.temperatura_objetivo_masa",
            "t_harina": "number.temperatura_harina",
            "t_prefermento": "number.temperatura_prefermento",
            "t_friccion_amasadora": "number.temperatura_friccion_amasadora",
            "t_ambiente": "number.temperatura_ambiente",
            "tipo_prefermento": "select.tipo_de_prefermento",
            "harina_para_prefermento": "select.harina_para_prefermento",
            "extras": "switch.habilitar_ingredientes_extras"
        }
        
        if limpio in equivalencias:
            state = hass.states.get(equivalencias[limpio])
            if state and state.state not in ["unavailable", "unknown", ""]:
                return float(state.state) if "number" in equivalencias[limpio] else state.state

        variantes = [
            f"number.pan_pct_{limpio}", f"number.pan_t_{limpio}", f"number.pan_{limpio}", f"number.{limpio}",
            f"select.{limpio}", f"switch.{limpio}", f"text.{limpio}"
        ]

        for entidad_id in variantes:
            state = hass.states.get(entidad_id)
            if state and state.state not in ["unavailable", "unknown", ""]:
                try: return float(state.state)
                except (ValueError, TypeError): pass

        for entidad_id in variantes:
            state = hass.states.get(entidad_id)
            if state and state.state not in ["unavailable", "unknown", ""]:
                return state.state

        return default_val

    async def forzar_inyeccion_slider(nombre_base, valor):
        """Busca el ID real nativo activo del slider e inyecta el valor de forma asíncrona."""
        if nombre_base in ["nombre_nueva_formula", "pan_nombre_nueva_formula"]:
            if hass.states.get("text.nombre_nueva_formula") is not None:
                await hass.services.async_call("text", "set_value", {
                    "entity_id": "text.nombre_nueva_formula", 
                    "value": str(valor)
                })
                return True

        limpio = nombre_base.replace("pan_pct_", "").replace("pan_t_", "").replace("pan_", "")
        
        equivalencias_id = {
            "masa_final_objetivo": "number.masa_final_objetivo",
            "masa_final": "number.masa_final_objetivo",
            "harina_1": "number.harina_1",
            "harina_2": "number.harina_2",
            "harina_3": "number.harina_3",
            "agua_hidratacion": "number.agua_hidratacion",
            "agua": "number.agua_hidratacion",
            "sal": "number.sal",
            "levadura": "number.levadura",
            "prefermento": "number.prefermento",
            "hidratacion_masa_madre": "number.hidratacion_masa_madre",
            "inoculo_masa_madre": "number.inoculo_masa_madre",
            "levadura_prefermento": "number.levadura_prefermento",
            "tang_zhong": "number.tang_zhong",
            "malta": "number.malta",
            "azucar": "number.azucar",
            "aove": "number.aove",
            "mantequilla": "number.mantequilla",
            "leche_en_polvo": "number.leche_en_polvo",
            "leche_liquida": "number.leche_liquida",
            "leche": "number.leche_liquida",
            "huevo": "number.huevo",
            "t_objetivo_masa": "number.temperatura_objetivo_masa",
            "t_harina": "number.temperatura_harina",
            "t_prefermento": "number.temperatura_prefermento",
            "t_friccion_amasadora": "number.temperatura_friccion_amasadora",
            "t_ambiente": "number.temperatura_ambiente",
            "tipo_prefermento": "select.tipo_de_prefermento",
            "tipo_de_prefermento": "select.tipo_de_prefermento",
            "harina_para_prefermento": "select.harina_para_prefermento",
            "habilitar_ingredientes_extras": "switch.habilitar_ingredientes_extras",
            "extras": "switch.habilitar_ingredientes_extras",
            "calcular_hidratacion_real": "switch.calcular_hidratacion_real"
        }

        if limpio in equivalencias_id and hass.states.get(equivalencias_id[limpio]) is not None:
            entidad_id = equivalencias_id[limpio]
            dominio = entidad_id.split(".")[0]
            if dominio == "select":
                servicio = "select_option"
                params = {"entity_id": entidad_id, "option": str(valor)}
            elif dominio == "switch":
                servicio = "turn_on" if valor else "turn_off"
                params = {"entity_id": entidad_id}
            else:
                servicio = "set_value"
                params = {"entity_id": entidad_id, "value": float(valor)}
            await hass.services.async_call(dominio, servicio, params)
            return True

        variantes = [
            f"number.{limpio}", f"select.{limpio}", f"switch.{limpio}"
        ]
        for entidad_id in variantes:
            if hass.states.get(entidad_id) is not None:
                dominio = entidad_id.split(".")[0]
                if dominio == "select":
                    servicio = "select_option"
                    params = {"entity_id": entidad_id, "option": str(valor)}
                elif dominio == "switch":
                    servicio = "turn_on" if valor else "turn_off"
                    params = {"entity_id": entidad_id}
                else:
                    servicio = "set_value"
                    params = {"entity_id": entidad_id, "value": float(valor)}
                await hass.services.async_call(dominio, servicio, params)
                return True
        return False

    def obtener_datos_interfaz():
        """Captura los estados actuales leyendo los dominios nativos de forma blindada."""
        st_masa = hass.states.get("number.masa_final_objetivo")
        try:
            masa_real = float(st_masa.state) if st_masa and st_masa.state not in ["unavailable", "unknown", ""] else 1000.0
        except (ValueError, TypeError):
            masa_real = 1000.0

        st_inoculo = hass.states.get("number.inoculo_masa_madre")
        try:
            inoculo_real = float(st_inoculo.state) if st_inoculo and st_inoculo.state not in ["unavailable", "unknown", ""] else 33.3
        except (ValueError, TypeError):
            inoculo_real = 33.3

        return {
            "masa_final_objetivo": masa_real,
            "harina_1": float(buscar_estado_entidad("harina_1", 100.0)),
            "harina_2": float(buscar_estado_entidad("harina_2", 0.0)),
            "harina_3": float(buscar_estado_entidad("harina_3", 0.0)),
            "agua_hidratacion": float(buscar_estado_entidad("agua", 60.0)),
            "sal": float(buscar_estado_entidad("sal", 2.0)),
            "levadura": float(buscar_estado_entidad("levadura", 0.7)),
            "tipo_levadura": obtener_tipo_levadura_actual(),
            "prefermento": float(buscar_estado_entidad("prefermento", 0.0)),
            "tipo_de_prefermento": str(buscar_estado_entidad("tipo_prefermento", "poolish")),
            "inoculo_masa_madre": inoculo_real,
            "hidratacion_masa_madre": float(buscar_estado_entidad("hidratacion_masa_madre", 100.0)),
            "harina_para_prefermento": str(buscar_estado_entidad("harina_para_prefermento", "harina 1")),
            "levadura_prefermento": float(buscar_estado_entidad("levadura_prefermento", 0.0)),
            "tang_zhong": float(buscar_estado_entidad("tang_zhong", 0.0)),
            "base_tang_zhong": obtener_base_tz_actual(),
            "habilitar_ingredientes_extras": hass.states.is_state("switch.habilitar_ingredientes_extras", "on"),
            "malta": float(buscar_estado_entidad("malta", 0.0)),
            "azucar": float(buscar_estado_entidad("azucar", 0.0)),
            "aove": float(buscar_estado_entidad("aove", 0.0)),
            "mantequilla": float(buscar_estado_entidad("mantequilla", 0.0)),
            "leche_en_polvo": float(buscar_estado_entidad("leche_en_polvo", 0.0)),
            "leche_liquida": float(buscar_estado_entidad("leche", 0.0)),
            "huevo": float(buscar_estado_entidad("huevo", 0.0)),
            "calcular_hidratacion_real": hass.states.is_state("switch.calcular_hidratacion_real", "on")
        }

    async def guardar_formula_service(call: ServiceCall):
        """Guarda una receta nueva o actualiza la activa leyendo la memoria global blindada."""
        from . import const
        estado_texto = hass.states.get("text.nombre_nueva_formula")
        nombre_raw = estado_texto.state if estado_texto else ""
        
        if not nombre_raw or str(nombre_raw).strip() in ["", "0.0", "0", "unknown", "unavailable"]:
            nombre_raw = const.RECETA_ACTIVA_MEMORIA
            
        if not nombre_raw or str(nombre_raw).strip() in ["", "---", "unknown", "unavailable"]:
            _LOGGER.warning("Intento de guardado fallido: No hay nombre en el cuadro de texto ni receta activa.")
            await hass.services.async_call("persistent_notification", "create", {
                "title": "⚠️ Error de Guardado",
                "message": "No se puede guardar la receta porque el campo **'Nombre para guardar'** está vacío y no hay ninguna receta activa cargada.",
                "notification_id": "porcentaje_panadero_vacio"
            })
            return
        
        nombre_id = str(nombre_raw).strip().replace(" ", "_").lower()

        def leer_json():
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        data = await hass.async_add_executor_job(leer_json)

        if nombre_id in data:
            _LOGGER.info("Fórmula '%s' ya existe. Solicitando confirmación de sobreescritura.", nombre_id)
            hass.bus.fire("porcentaje_panadero_alerta_duplicado", {"nombre": str(nombre_raw)})
            return

        data[nombre_id] = obtener_datos_interfaz()
        
        def escribir_json():
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        await hass.async_add_executor_job(escribir_json)
            
        _LOGGER.info("Nueva fórmula '%s' creada con éxito en el archivo JSON.", nombre_id)
        
        if hass.states.get("text.nombre_nueva_formula") is not None:
            await hass.services.async_call("text", "set_value", {"entity_id": "text.nombre_nueva_formula", "value": ""})
            
        await actualizar_menu_desplegable(hass, list(data.keys()), nombre_id)

    async def confirmar_sobreescritura_service(call: ServiceCall):
        """Servicio definitivo que se ejecuta si una automatización móvil llama a la confirmación."""
        from . import const
        nombre_raw = const.RECETA_ACTIVA_MEMORIA
        if not nombre_raw or str(nombre_raw).strip() in ["", "---", "unknown", "unavailable"]: 
            return
            
        nombre_id = str(nombre_raw).strip().replace(" ", "_").lower()

        def leer_json():
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        data = await hass.async_add_executor_job(leer_json)
        data[nombre_id] = obtener_datos_interfaz()
        
        def escribir_json():
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        await hass.async_add_executor_job(escribir_json)
            
        _LOGGER.info("Fórmula '%s' actualizada en el JSON tras confirmación externa.", nombre_id)
        if hass.states.get("text.nombre_nueva_formula") is not None:
            await hass.services.async_call("text", "set_value", {"entity_id": "text.nombre_nueva_formula", "value": ""})
            
        await actualizar_menu_desplegable(hass, list(data.keys()), nombre_id)

    async def eliminar_formula_service(call: ServiceCall):
        """Usa la memoria global fija de Python para saber qué receta borrar."""
        from . import const
        nombre_raw = const.RECETA_ACTIVA_MEMORIA
        if nombre_raw in ["---", "", "unknown", "unavailable"]:
            _LOGGER.warning("Intento de borrado fallido: No hay ninguna receta activa en el obrador.")
            return
            
        nombre_id = nombre_raw.strip().replace(" ", "_").lower()
        _LOGGER.info("Solicitando confirmación de borrado para la receta activa: %s", nombre_id)
        hass.bus.fire("porcentaje_panadero_alerta_eliminar", {"nombre": str(nombre_raw)})

    async def confirmar_eliminacion_service(call: ServiceCall):
        """Servicio forzado que se ejecuta tras confirmar el borrado desde el móvil."""
        from . import const
        nombre_raw = const.RECETA_ACTIVA_MEMORIA
        if nombre_raw in ["---", "", "unknown", "unavailable"]: 
            return
            
        nombre_id = nombre_raw.strip().replace(" ", "_").lower()

        def leer_json():
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        data = await hass.async_add_executor_job(leer_json)
            
        if nombre_id in data:
            del data[nombre_id]
            def escribir_json():
                with open(ruta_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            await hass.async_add_executor_job(escribir_json)
                
            _LOGGER.info("Fórmula '%s' destruida del JSON tras confirmación de seguridad.", nombre_id)
            await actualizar_menu_desplegable(hass, list(data.keys()), "---")
            await hass.services.async_call("button", "press", {"entity_id": "button.restablecer_parametros_base"})

    hass.services.async_register(DOMAIN, "confirmar_eliminacion", confirmar_eliminacion_service)

    async def cargar_formula_en_sliders_service(call: ServiceCall):
        """Mueve los controles de la pantalla al seleccionar una receta adaptando IDs."""
        from . import const
        nombre_id = call.data.get("nombre").strip().replace(" ", "_").lower()
        if not os.path.exists(ruta_json): return
        
        def leer_json():
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        data = await hass.async_add_executor_job(leer_json)
        
        if nombre_id in data:
            const.CARGANDO_RECETA_BLOQUEO = True
            receta = data[nombre_id]
            
            for key, val in receta.items():
                if key in ["tipo_levadura", "base_tang_zhong"]:
                    continue
                await forzar_inyeccion_slider(key, val)

            tipo_leva_receta = receta.get("tipo_levadura", "seca")
            establecer_tipo_levadura_actual(tipo_leva_receta)
            estado_actual = hass.states.get(ID_BOTON_LEVADURA)
            atributos_base = dict(estado_actual.attributes) if estado_actual else {}
            atributos_base["tipo_levadura"] = tipo_leva_receta
            atributos_base["options"] = ["fresca", "seca"]
            hass.states.async_set(ID_BOTON_LEVADURA, tipo_leva_receta, atributos_base)

            tipo_base_tz = receta.get("base_tang_zhong", "agua")
            establecer_base_tz_actual(tipo_base_tz)
            estado_tz = hass.states.get(ID_BOTON_TANG_ZHONG)
            atributos_tz = dict(estado_tz.attributes) if estado_tz else {}
            atributos_tz["base_liquida"] = tipo_base_tz
            atributos_tz["options"] = ["agua", "leche"]
            hass.states.async_set(ID_BOTON_TANG_ZHONG, tipo_base_tz, atributos_tz)
            
            await actualizar_menu_desplegable(hass, list(data.keys()), nombre_id)
            const.CARGANDO_RECETA_BLOQUEO = False

    async def alternar_tipo_levadura_service(call: ServiceCall):
        """Conmuta entre levadura aplicando el factor x3 o /3 leyendo los números reales actuales."""
        tipo_actual = obtener_tipo_levadura_actual()
        nuevo_tipo = "fresca" if tipo_actual == "seca" else "seca"

        st_leva = hass.states.get("number.levadura")
        st_leva_pref = hass.states.get("number.levadura_prefermento")

        pct_leva_principal = float(st_leva.state) if st_leva and st_leva.state not in ["unavailable", "unknown", ""] else 0.7
        pct_leva_pref = float(st_leva_pref.state) if st_leva_pref and st_leva_pref.state not in ["unavailable", "unknown", ""] else 0.0

        nuevo_pct = round(pct_leva_principal * 3.0, 2) if tipo_actual == "seca" else round(pct_leva_principal / 3.0, 2)
        nuevo_pct_pref = round(pct_leva_pref * 3.0, 2) if tipo_actual == "seca" else round(pct_leva_pref / 3.0, 2)

        establecer_tipo_levadura_actual(nuevo_tipo)

        if hass.states.get("number.levadura") is not None:
            await hass.services.async_call("number", "set_value", {"entity_id": "number.levadura", "value": nuevo_pct})
        if pct_leva_pref > 0 and hass.states.get("number.levadura_prefermento") is not None:
            await hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": nuevo_pct_pref})

        estado_actual = hass.states.get(ID_BOTON_LEVADURA)
        atributos_base = dict(estado_actual.attributes) if estado_actual else {}
        atributos_base["tipo_levadura"] = nuevo_tipo
        atributos_base["options"] = ["fresca", "seca"]
        hass.states.async_set(ID_BOTON_LEVADURA, nuevo_tipo, atributos_base)

    async def alternar_tang_zhong_base_service(call: ServiceCall):
        """Conmuta la base líquida del Tang-Zhong y fuerza el balanceo matemático de líquidos."""
        base_actual = obtener_base_tz_actual()
        nueva_base = "leche" if base_actual == "agua" else "agua"
        establecer_base_tz_actual(nueva_base)
        
        estado_tz = hass.states.get(ID_BOTON_TANG_ZHONG)
        atributos_tz = dict(estado_tz.attributes) if estado_tz else {}
        atributos_tz["base_liquida"] = nueva_base
        atributos_tz["options"] = ["agua", "leche"]
        hass.states.async_set(ID_BOTON_TANG_ZHONG, nueva_base, atributos_tz)
        await hass.services.async_call(DOMAIN, "balancear_harinas", {"harina_origen": 1})

    async def balancear_harinas_service(call: ServiceCall):
        """Mantiene el balance reactivo al 100% y resetea extras de forma limpia."""
        harina_cambiada = call.data.get("harina_origen", 1)
        h1 = float(buscar_estado_entidad("harina_1", 100.0))
        h2 = float(buscar_estado_entidad("harina_2", 0.0))
        h3 = float(buscar_estado_entidad("harina_3", 0.0))

        if (h1 + h2 + h3) != 100:
            if harina_cambiada == 1:
                nuevo_h2 = max(0.0, 100.0 - h1 - h3)
                nuevo_h3 = max(0.0, 100.0 - h1 - nuevo_h2)
                await forzar_inyeccion_slider("harina_2", nuevo_h2)
                await forzar_inyeccion_slider("harina_3", nuevo_h3)
            elif harina_cambiada == 2:
                nuevo_h1 = max(0.0, 100.0 - h2 - h3)
                await forzar_inyeccion_slider("harina_1", nuevo_h1)
                if (nuevo_h1 + h2 + h3) != 100:
                    nuevo_h3 = max(0.0, 100.0 - h2)
                    await forzar_inyeccion_slider("harina_3", nuevo_h3)
            elif harina_cambiada == 3:
                nuevo_h1 = max(0.0, 100.0 - h2 - h3)
                await forzar_inyeccion_slider("harina_1", nuevo_h1)
                if (nuevo_h1 + h2 + h3) != 100:
                    nuevo_h2 = max(0.0, 100.0 - h3)
                    await forzar_inyeccion_slider("harina_2", nuevo_h2)

        extras_on = hass.states.is_state("switch.habilitar_ingredientes_extras", "on")
        if not extras_on:
            for extra_key in ["malta", "azucar", "aove", "mantequilla", "leche_en_polvo", "leche_liquida", "huevo", "tang_zhong"]:
                if buscar_estado_entidad(extra_key, 0.0) > 0.0:
                    await forzar_inyeccion_slider(extra_key, 0.0)

    async def actualizar_menu_desplegable(hass, lista_recetas, seleccion_actual):
        """Actualiza la memoria de las opciones del selector y fuerza el refresco visual en Lovelace."""
        opciones_finales = ["---"] + lista_recetas
        entidad_select_id = "select.formula_de_receta"
        entidad_sensor_id = "sensor.formula_activa"
        
        try:
            componente_select = hass.data.get("select")
            if componente_select and hasattr(componente_select, "entities"):
                for entidad in componente_select.entities:
                    if hasattr(entidad, "unique_id") and entidad.unique_id == "formula_de_receta":
                        entidad._options = opciones_finales
                        entidad._current_option = "---"
                        entidad.async_write_ha_state()
                        break
        except Exception as ex:
            _LOGGER.error("No se pudo actualizar el objeto select en memoria: %s", ex)

        if seleccion_actual != "---":
            const.RECETA_ACTIVA_MEMORIA = seleccion_actual.replace("_", " ").title()
            hass.states.async_set(entidad_sensor_id, const.RECETA_ACTIVA_MEMORIA, {"friendly_name": "Receta en el Obrador", "icon": "mdi:notebook-check"})
            receta_atributo = seleccion_actual
        else:
            const.RECETA_ACTIVA_MEMORIA = "---"
            hass.states.async_set(entidad_sensor_id, "---", {"friendly_name": "Receta en el Obrador", "icon": "mdi:notebook-check"})
            receta_atributo = "---"

        atributos = {"options": opciones_finales, "friendly_name": "Fórmula de Receta", "receta_activa": receta_atributo}
        await asyncio.sleep(0.4)
        if hass.states.get(entidad_select_id) is not None:
            hass.states.async_set(entidad_select_id, "---", atributos)

    # REGISTRO DE SERVICIOS EN EL CORE
    hass.services.async_register(DOMAIN, "guardar_formula", guardar_formula_service)
    hass.services.async_register(DOMAIN, "confirmar_sobreescritura", confirmar_sobreescritura_service)
    hass.services.async_register(DOMAIN, "eliminar_formula", eliminar_formula_service)
    hass.services.async_register(DOMAIN, "cargar_formula_en_sliders", cargar_formula_en_sliders_service)
    hass.services.async_register(DOMAIN, "alternar_tipo_levadura", alternar_tipo_levadura_service)
    hass.services.async_register(DOMAIN, "alternar_tang_zhong_base", alternar_tang_zhong_base_service)
    hass.services.async_register(DOMAIN, "balancear_harinas", balancear_harinas_service)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    try:
        def leer_json():
            if os.path.exists(ruta_json):
                with open(ruta_json, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        data = await hass.async_add_executor_job(leer_json)
        if data:
            await actualizar_menu_desplegable(hass, list(data.keys()), "---")
    except Exception:
        pass

    return True
