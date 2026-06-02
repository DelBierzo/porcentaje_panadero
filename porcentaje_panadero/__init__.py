import os
import json
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

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
    """Configuracion inicial por YAML."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura la integracion de forma oficial desde la seccion de Ajustes."""
    _LOGGER.info("Inicializando el cerebro de Porcentaje Panadero con paridad de estados.")
    
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
        """Busca la entidad en el Core probando todas las variantes de prefijos posibles."""
        if nombre_base in ["nombre_nueva_formula", "pan_nombre_nueva_formula"]:
            st_texto = hass.states.get("text.porcentaje_panadero_nombre_nueva_formula")
            if st_texto and st_texto.state not in ["unavailable", "unknown", ""]:
                return st_texto.state

        limpio = nombre_base.replace("pan_pct_", "").replace("pan_t_", "").replace("pan_", "")
        
        equivalencias = {
            "masa_final": "number.masa_final_objetivo",
            "agua": "number.agua_hidratacion",
            "leche": "number.leche_liquida",
            "tipo_prefermento": "select.tipo_de_prefermento",
            "harina_para_prefermento": "select.harina_para_prefermento",
            "extras": "switch.habilitar_ingredientes_extras"
        }
        
        if limpio in equivalencias:
            state = hass.states.get(equivalencias[limpio])
            if state and state.state not in ["unavailable", "unknown", ""]:
                return float(state.state) if "number" in equivalencias[limpio] else state.state

        variantes = [
            f"number.{limpio}", f"number.pan_{limpio}", f"number.porcentaje_panadero_{limpio}",
            f"select.{limpio}", f"select.pan_{limpio}",
            f"switch.{limpio}", f"switch.pan_{limpio}",
            f"text.{limpio}", f"text.pan_{limpio}"
        ]

        for entidad_id in variantes:
            state = hass.states.get(entidad_id)
            if state and state.state not in ["unavailable", "unknown", ""]:
                try: return float(state.state)
                except (ValueError, TypeError): pass

        for entidad_id in variantes:
            state = hass.states.get(entidad_id)
            if state and state.state not in ["unavailable", "unknown", ""]:
                if "select" in entidad_id or "switch" in entidad_id or "text" in entidad_id:
                    return state.state

        return default_val

    async def forzar_inyeccion_slider(nombre_base, valor):
        """Busca el ID real activo del slider e inyecta el valor de forma asincrona."""
        if nombre_base in ["nombre_nueva_formula", "pan_nombre_nueva_formula"]:
            if hass.states.get("text.porcentaje_panadero_nombre_nueva_formula") is not None:
                await hass.services.async_call("text", "set_value", {
                    "entity_id": "text.porcentaje_panadero_nombre_nueva_formula", 
                    "value": str(valor)
                })
                return True

        limpio = nombre_base.replace("pan_pct_", "").replace("pan_t_", "").replace("pan_", "")
        variantes = [
            f"number.{limpio}", f"number.pan_{limpio}", f"number.pan_pct_{limpio}", f"number.pan_t_{limpio}",
            f"number.porcentaje_panadero_{limpio}", f"number.porcentaje_panadero_pan_{limpio}",
            f"number.porcentaje_panadero_pan_pct_{limpio}", f"number.porcentaje_panadero_pan_t_{limpio}",
            f"select.{limpio}", f"select.pan_{limpio}", f"select.porcentaje_panadero_{limpio}",
            f"select.porcentaje_panadero_pan_{limpio}",
            f"switch.{limpio}", f"switch.pan_{limpio}", f"switch.porcentaje_panadero_{limpio}",
            f"switch.porcentaje_panadero_pan_{limpio}",
            f"text.{limpio}", f"text.pan_{limpio}", f"text.porcentaje_panadero_{limpio}"
        ]
        
        equivalencias_id = {
            "masa_final": "number.masa_final_objetivo",
            "agua": "number.agua_hidratacion",
            "leche": "number.leche_liquida",
            "tipo_prefermento": "select.tipo_de_prefermento",
            "harina_para_prefermento": "select.harina_para_prefermento",
            "extras": "switch.habilitar_ingredientes_extras"
        }
        
        if limpio in equivalencias_id and hass.states.get(equivalencias_id[limpio]) is not None:
            entidad_id = equivalencias_id[limpio]
            dominio = entidad_id.split(".")[0]
            servicio = "select_option" if dominio == "select" else "turn_on" if (dominio == "switch" and valor) else "turn_off" if dominio == "switch" else "set_value"
            params = {"entity_id": entidad_id, "option": str(valor)} if dominio == "select" else {"entity_id": entidad_id} if dominio == "switch" else {"entity_id": entidad_id, "value": float(valor)}
            await hass.services.async_call(dominio, servicio, params)
            return True

        for entidad_id in variantes:
            if hass.states.get(entidad_id) is not None:
                dominio = entidad_id.split(".")[0]
                servicio = "select_option" if dominio == "select" else "turn_on" if (dominio == "switch" and valor) else "turn_off" if dominio == "switch" else "set_value"
                params = {"entity_id": entidad_id, "option": str(valor)} if dominio == "select" else {"entity_id": entidad_id} if dominio == "switch" else {"entity_id": entidad_id, "value": float(valor)}
                await hass.services.async_call(dominio, servicio, params)
                return True
        return False

    def obtener_datos_interfaz():
        """Captura los estados actuales leyendo los dominios nativos de forma blindada."""
        usar_fisico = hass.data[DOMAIN][entry.entry_id]["usar_sensor_fisico"]
        sensor_id = hass.data[DOMAIN][entry.entry_id]["entidad_termometro"]
        
        if usar_fisico and sensor_id != "manual" and hass.states.get(sensor_id):
            try: t_amb = float(hass.states.get(sensor_id).state)
            except (ValueError, TypeError): t_amb = float(buscar_estado_entidad("pan_t_ambiente", 22.0))
        else:
            t_amb = float(buscar_estado_entidad("pan_t_ambiente", 22.0))

        return {
            "masa_final_objetivo": float(buscar_estado_entidad("masa_final", 1000.0)),
            "harina_1": float(buscar_estado_entidad("harina_1", 100.0)),
            "harina_2": float(buscar_estado_entidad("harina_2", 0.0)),
            "harina_3": float(buscar_estado_entidad("harina_3", 0.0)),
            "agua_hidratacion": float(buscar_estado_entidad("agua", 60.0)),
            "sal": float(buscar_estado_entidad("sal", 2.0)),
            "levadura": float(buscar_estado_entidad("levadura", 0.7)),
            "prefermento": float(buscar_estado_entidad("prefermento", 0.0)),
            "tipo_de_prefermento": str(buscar_estado_entidad("tipo_prefermento", "poolish")),
            "hidratacion_masa_madre": float(buscar_estado_entidad("hidratacion_masa_madre", 100.0)),
            "harina_para_prefermento": str(buscar_estado_entidad("harina_para_prefermento", "harina 1")),
            "levadura_prefermento": float(buscar_estado_entidad("levadura_prefermento", 0.0)),
            "habilitar_ingredientes_extras": hass.states.is_state("switch.habilitar_ingredientes_extras", "on"),
            "malta": float(buscar_estado_entidad("malta", 0.0)),
            "azucar": float(buscar_estado_entidad("azucar", 0.0)),
            "aove": float(buscar_estado_entidad("aove", 0.0)),
            "mantequilla": float(buscar_estado_entidad("mantequilla", 0.0)),
            "leche_en_polvo": float(buscar_estado_entidad("leche_en_polvo", 0.0)),
            "leche_liquida": float(buscar_estado_entidad("leche", 0.0)),
            "huevo": float(buscar_estado_entidad("huevo", 0.0))
        }

    async def guardar_formula_service(call: ServiceCall):
        """Guarda la receta leyendo el cuadro de texto o el desplegable si la caja esta vacia."""
        estado_texto = hass.states.get("text.porcentaje_panadero_nombre_nueva_formula")
        nombre_raw = estado_texto.state if estado_texto else ""
        
        if not nombre_raw or str(nombre_raw).strip() in ["", "0.0", "0", "unknown", "unavailable"]:
            estado_desplegable = hass.states.get("select.formula_de_receta")
            nombre_raw = estado_desplegable.state if estado_desplegable else ""
            
        if not nombre_raw or str(nombre_raw).strip() in ["", "---", "unknown", "unavailable"]:
            _LOGGER.warning("Intento de guardado fallido: El cuadro de texto esta vacio y no hay receta seleccionada.")
            await hass.services.async_call("persistent_notification", "create", {
                "title": "⚠️ Error de Guardado",
                "message": "No se puede guardar la receta porque el campo **'Nombre para guardar'** esta vacio y no tienes ninguna receta seleccionada en el menu desplegable.",
                "notification_id": "porcentaje_panadero_vacio"
            })
            return
        
        nombre_id = str(nombre_raw).strip().replace(" ", "_").lower()

        def leer_json():
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        data = await hass.async_add_executor_job(leer_json)

        if nombre_id in data:
            _LOGGER.info("Formula '%s' ya existe. Solicitando confirmacion.", nombre_id)
            hass.bus.fire("porcentaje_panadero_alerta_duplicado", {"nombre": str(nombre_raw)})
            return

        data[nombre_id] = obtener_datos_interfaz()
        
        def escribir_json():
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        await hass.async_add_executor_job(escribir_json)
            
        _LOGGER.info("Nueva formula '%s' creada con exito en el archivo JSON.", nombre_id)
        
        if hass.states.get("text.porcentaje_panadero_nombre_nueva_formula") is not None:
            await hass.services.async_call("text", "set_value", {
                "entity_id": "text.porcentaje_panadero_nombre_nueva_formula",
                "value": ""
            })
        else:
            await forzar_inyeccion_slider("nombre_nueva_formula", "")
            
        await actualizar_menu_desplegable(hass, list(data.keys()), nombre_id)

    async def confirmar_sobreescritura_service(call: ServiceCall):
        """Servicio forzado que se ejecuta tras confirmacion del usuario desde el movil."""
        nombre_raw = buscar_estado_entidad("nombre_nueva_formula", "")
        
        if not nombre_raw or str(nombre_raw).strip() in ["", "0.0", "0", "unknown", "unavailable"]:
            estado_desplegable = hass.states.get("select.formula_de_receta")
            nombre_raw = estado_desplegable.state if estado_desplegable else ""
            
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
            
        _LOGGER.info("Formula '%s' sobreescrita tras confirmacion del usuario.", nombre_id)
        
        if hass.states.get("text.porcentaje_panadero_nombre_nueva_formula") is not None:
            await hass.services.async_call("text", "set_value", {
                "entity_id": "text.porcentaje_panadero_nombre_nueva_formula",
                "value": ""
            })
        else:
            await forzar_inyeccion_slider("nombre_nueva_formula", "")
            
        await actualizar_menu_desplegable(hass, list(data.keys()), nombre_id)


    async def confirmar_sobreescritura_service(call: ServiceCall):
        """Servicio forzado tras confirmacion movil que rescata el nombre del desplegable si el texto se borro o esta vacio."""
        nombre_raw = buscar_estado_entidad("nombre_nueva_formula", "")
        
        if not nombre_raw or str(nombre_raw).strip() in ["", "0.0", "0", "unknown", "unavailable"]:
            estado_desplegable = hass.states.get("select.formula_de_receta")
            nombre_raw = estado_desplegable.state if estado_desplegable else ""
            
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
            
        _LOGGER.info("Formula '%s' sobreescrita tras confirmacion del usuario.", nombre_id)
        
        if hass.states.get("text.porcentaje_panadero_nombre_nueva_formula") is not None:
            await hass.services.async_call("text", "set_value", {
                "entity_id": "text.porcentaje_panadero_nombre_nueva_formula",
                "value": ""
            })
        else:
            await forzar_inyeccion_slider("nombre_nueva_formula", "")
            
        await actualizar_menu_desplegable(hass, list(data.keys()), nombre_id)
        
    async def eliminar_formula_service(call: ServiceCall):
        """No borra directo: Lanza una alerta de confirmacion al bus para evitar borrados accidentales."""
        estado_seleccionado = hass.states.get("select.formula_de_receta")
        nombre_raw = estado_seleccionado.state if estado_seleccionado else "---"
        
        if nombre_raw in ["---", "", "unknown", "unavailable"]:
            _LOGGER.warning("Intento de borrado fallido: No hay ninguna receta seleccionada en el menu desplegable.")
            return
            
        nombre_id = nombre_raw.strip().replace(" ", "_").lower()
        
        _LOGGER.info("Solicitando confirmacion de borrado para la receta: %s", nombre_id)
        hass.bus.fire("porcentaje_panadero_alerta_eliminar", {"nombre": str(nombre_raw)})

    async def confirmar_eliminacion_service(call: ServiceCall):
        """Servicio forzado que se ejecuta estrictamente tras confirmar el borrado desde el movil."""
        estado_seleccionado = hass.states.get("select.formula_de_receta")
        nombre_raw = estado_seleccionado.state if estado_seleccionado else "---"
        
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
                
            _LOGGER.info("Formula '%s' destruida del JSON tras confirmacion de seguridad.", nombre_id)
            await actualizar_menu_desplegable(hass, list(data.keys()), "---")

    hass.services.async_register(DOMAIN, "confirmar_eliminacion", confirmar_eliminacion_service)

    async def cargar_formula_en_sliders_service(call: ServiceCall):
        """Mueve los controles de la pantalla al seleccionar una receta adaptando IDs."""
        nombre_id = call.data.get("nombre").strip().replace(" ", "_").lower()
        if not os.path.exists(ruta_json): return
        
        def leer_json():
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        data = await hass.async_add_executor_job(leer_json)
        
        if nombre_id in data:
            receta = data[nombre_id]
            for key, val in receta.items():
                await forzar_inyeccion_slider(key, val)

    async def alternar_tipo_levadura_service(call: ServiceCall):
        """Conmuta entre levadura aplicando el factor x3 o /3 de forma adaptativa."""
        tipo_actual = str(buscar_estado_entidad("pan_tipo_levadura", "seca"))
        
        pct_leva_principal = float(buscar_estado_entidad("pan_pct_levadura", 0.7))
        pct_leva_pref = float(buscar_estado_entidad("pan_pct_levadura_prefermento", 0.0))

        nuevo_tipo = "fresca" if tipo_actual == "seca" else "seca"
        nuevo_pct = round(pct_leva_principal * 3.0, 2) if tipo_actual == "seca" else round(pct_leva_principal / 3.0, 2)
        nuevo_pct_pref = round(pct_leva_pref * 3.0, 2) if tipo_actual == "seca" else round(pct_leva_pref / 3.0, 2)

        await forzar_inyeccion_slider("pan_tipo_levadura", nuevo_tipo)
        await forzar_inyeccion_slider("pan_pct_levadura", nuevo_pct)
        if pct_leva_pref > 0:
            await forzar_inyeccion_slider("pan_pct_levadura_prefermento", nuevo_pct_pref)

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
            for extra_key in ["malta", "azucar", "aove", "mantequilla", "leche_en_polvo", "leche_liquida", "huevo"]:
                if buscar_estado_entidad(extra_key, 0.0) > 0.0:
                    await forzar_inyeccion_slider(extra_key, 0.0)

    async def actualizar_menu_desplegable(hass, lista_recetas, seleccion_actual):
        """Actualiza la memoria de las opciones del selector y fuerza el refresco visual en Lovelace."""
        opciones_finales = ["---"] + lista_recetas
        entidad_select_id = "select.formula_de_receta"
        
        if hass.states.get(entidad_select_id) is not None:
            hass.states.async_set(
                entidad_select_id,
                seleccion_actual,
                {"options": opciones_finales, "friendly_name": "Formula de Receta"}
            )
        
        try:
            from homeassistant.helpers import entity_component
            comp = hass.data.get("select")
            if comp and hasattr(comp, "entities"):
                for entidad in comp.entities:
                    if hasattr(entidad, "unique_id") and entidad.unique_id == "formula_de_receta":
                        entidad._options = opciones_finales
                        entidad._current_option = seleccion_actual
                        entidad.async_write_ha_state()
                        break
        except Exception:
            pass

        if hass.states.get(entidad_select_id) is not None:
            await hass.services.async_call("select", "select_option", {"entity_id": entidad_select_id, "option": "---"})
            if seleccion_actual != "---" and seleccion_actual in opciones_finales:
                await hass.services.async_call("select", "select_option", {"entity_id": entidad_select_id, "option": seleccion_actual})

    hass.services.async_register(DOMAIN, "guardar_formula", guardar_formula_service)
    hass.services.async_register(DOMAIN, "confirmar_sobreescritura", confirmar_sobreescritura_service)
    hass.services.async_register(DOMAIN, "eliminar_formula", eliminar_formula_service)
    hass.services.async_register(DOMAIN, "cargar_formula_en_sliders", cargar_formula_en_sliders_service)
    hass.services.async_register(DOMAIN, "alternar_tipo_levadura", alternar_tipo_levadura_service)
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
