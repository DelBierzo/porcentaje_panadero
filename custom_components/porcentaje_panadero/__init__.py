import os
import json
import logging
import asyncio
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.components.http import StaticPathConfig
import homeassistant.helpers.config_validation as cv
from .button import (
    obtener_tipo_levadura_actual,
    establecer_tipo_levadura_actual,
    ID_BOTON_LEVADURA,
    obtener_base_tz_actual,
    establecer_base_tz_actual,
    ID_BOTON_TANG_ZHONG
)
from .const import DOMAIN, RECETA_ACTIVA_MEMORIA

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
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
    """Configuracion inicial por archivo YAML."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura la integracion de forma oficial desde Ajustes."""
    _LOGGER.info("Inicializando cerebro de Porcentaje Panadero.")

    ruta_json = hass.config.path("custom_components/porcentaje_panadero/formulas.json")
    ruta_harinas_json = hass.config.path("custom_components/porcentaje_panadero/harinas.json")

    def inicializar_archivos_persistentes_sync():
        if not os.path.exists(ruta_json):
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4, ensure_ascii=False)

        if not os.path.exists(ruta_harinas_json):
            with open(ruta_harinas_json, "w", encoding="utf-8") as f:
                base_harinas = [
                    "Harina de Media Fuerza",
                    "Harina de Fuerza",
                    "Harina de Gran Fuerza",
                    "Harina de Centeno",
                    "Harina de Espelta"
                ]
                json.dump(base_harinas, f, indent=4, ensure_ascii=False)

    await hass.async_add_executor_job(inicializar_archivos_persistentes_sync)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "usar_sensor_fisico": entry.data.get("usar_sensor_fisico", False),
        "entidad_termometro": entry.data.get("entidad_termometro", "manual")
    }

    # 🟢 SOLUCIÓN DEFINITIVA: Añadimos await para ejecutar la función asíncrona de forma nativa
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            url_path="/porcentaje_panadero_ui",
            path=hass.config.path("custom_components/porcentaje_panadero/www"),
            cache_headers=False
        )
    ])

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
        """Busca el ID real nativo activo del slider e inyecta el valor de forma asincrona."""
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
            partes = entidad_id.split(".")
            dominio = partes[0]
            
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
                partes = entidad_id.split(".")
                dominio = partes[0]
                
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

        sel_h1 = hass.states.get("select.harina_principal_1")
        sel_h2 = hass.states.get("select.harina_secundaria_2")
        sel_h3 = hass.states.get("select.harina_secundaria_3")

        return {
            "masa_final_objetivo": masa_real,
            "harina_1": float(buscar_estado_entidad("harina_1", 100.0)),
            "harina_2": float(buscar_estado_entidad("harina_2", 0.0)),
            "harina_3": float(buscar_estado_entidad("harina_3", 0.0)),
            "harina_1_nombre": sel_h1.state if sel_h1 and sel_h1.state not in ["unknown", "unavailable", ""] else "Harina de Fuerza",
            "harina_2_nombre": sel_h2.state if sel_h2 and sel_h2.state not in ["unknown", "unavailable", ""] else "Harina de Centeno",
            "harina_3_nombre": sel_h3.state if sel_h3 and sel_h3.state not in ["unknown", "unavailable", ""] else "Harina de Espelta",
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
                "title": "Error de Guardado",
                "message": "No se puede guardar la receta porque el campo **Nombre para guardar** esta vacio y no hay ninguna receta activa cargada.",
                "notification_id": "porcentaje_panadero_vacio"
            })
            return

        nombre_id = str(nombre_raw).strip().replace(" ", "_").lower()

        def leer_json():
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)

        data = await hass.async_add_executor_job(leer_json)

        if nombre_id in data:
            _LOGGER.info("Formula '%s' ya existe. Solicitando confirmacion de sobreescritura.", nombre_id)
            hass.bus.fire("porcentaje_panadero_alerta_duplicado", {"nombre": str(nombre_raw)})
            return

        data[nombre_id] = obtener_datos_interfaz()

        def escribir_json():
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        await hass.async_add_executor_job(escribir_json)
        _LOGGER.info("Nueva formula '%s' creada con exito en el archivo JSON.", nombre_id)

        # Actualiza la memoria global y fuerza al sensor a pintar el nombre recien guardado
        const.RECETA_ACTIVA_MEMORIA = nombre_raw.strip().replace("_", " ").title()
        hass.states.async_set("sensor.formula_activa", const.RECETA_ACTIVA_MEMORIA, {
            "friendly_name": "Receta en el Obrador", "icon": "mdi:notebook-check"
        })

        if hass.states.get("text.nombre_nueva_formula") is not None:
            await hass.services.async_call("text", "set_value", {"entity_id": "text.nombre_nueva_formula", "value": ""})

        # Enviamos la notificacion nativa por el bus para recargar el select de forma segura
        hass.bus.fire("porcentaje_panadero_recetas_actualizadas", {})

    async def confirmar_sobreescritura_service(call: ServiceCall):
        """Servicio definitivo que se ejecuta si una automatizacion movil llama a la confirmacion."""
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

        _LOGGER.info("Formula '%s' actualizada en el JSON tras confirmacion externa.", nombre_id)
        
        if hass.states.get("text.nombre_nueva_formula") is not None:
            await hass.services.async_call("text", "set_value", {"entity_id": "text.nombre_nueva_formula", "value": ""})

        const.RECETA_ACTIVA_MEMORIA = nombre_raw.strip().replace("_", " ").title()
        hass.states.async_set("sensor.formula_activa", const.RECETA_ACTIVA_MEMORIA, {
            "friendly_name": "Receta en el Obrador", "icon": "mdi:notebook-check"
        })

        if hass.states.get("select.formula_de_receta") is not None:
            await hass.services.async_call("select", "select_option", {"entity_id": "select.formula_de_receta", "option": "---"})

    async def eliminar_formula_service(call: ServiceCall):
        """Usa la memoria global fija de Python para saber que receta borrar."""
        from . import const
        nombre_raw = const.RECETA_ACTIVA_MEMORIA
        if nombre_raw in ["---", "", "unknown", "unavailable"]:
            _LOGGER.warning("Intento de borrado fallido: No hay ninguna receta activa en el obrador.")
            return

        nombre_id = nombre_raw.strip().replace(" ", "_").lower()
        _LOGGER.info("Solicitando confirmacion de borrado para la receta activa: %s", nombre_id)
        hass.bus.fire("porcentaje_panadero_alerta_eliminar", {"nombre": str(nombre_raw)})

    async def confirmar_eliminacion_service(call: ServiceCall):
        """Servicio definitivo que se ejecuta tras confirmar el borrado desde el movil."""
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

            _LOGGER.info("Formula '%s' destruida del JSON tras confirmacion de seguridad.", nombre_id)
            
            const.RECETA_ACTIVA_MEMORIA = "---"
            hass.states.async_set("sensor.formula_activa", "---", {
                "friendly_name": "Receta en el Obrador", "icon": "mdi:notebook-check"
            })
            
            await hass.services.async_call("button", "press", {"entity_id": "button.restablecer_parametros_base"})
            if hass.states.get("select.formula_de_receta") is not None:
                await hass.services.async_call("select", "select_option", {"entity_id": "select.formula_de_receta", "option": "---"})

    hass.services.async_register(DOMAIN, "confirmar_eliminacion", confirmar_eliminacion_service)

    async def sincronizar_selectores_harina(lista_harinas):
        """Notifica los cambios a la UI de Lovelace y actualiza la RAM interna separando comodines."""
        marcas_reales = [h for h in lista_harinas if h not in ["HARINA 1", "HARINA 2", "HARINA 3", "---"]]

        lista_bascula = list(marcas_reales)
        for texto_base in ["HARINA 1", "HARINA 2", "HARINA 3"]:
            if texto_base not in lista_bascula:
                lista_bascula.append(texto_base)

        lista_purga = ["---"] + marcas_reales

        try:
            componente_select = hass.data.get("select")
            if componente_select and hasattr(componente_select, "entities"):
                for entidad in componente_select.entities:
                    if hasattr(entidad, "_clave"):
                        if entidad._clave in ["selector_harina_1", "selector_harina_2", "selector_harina_3"]:
                            entidad._options = lista_bascula
                            entidad.async_write_ha_state()
                        elif entidad._clave == "retirar_harina_del_inventario":
                            entidad._options = lista_purga
                            entidad.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("No se pudo sincronizar la lista de harinas en la RAM del componente: %s", ex)

        for entidad_id in ["select.harina_principal_1", "select.harina_secundaria_2", "select.harina_secundaria_3"]:
            estado_actual = hass.states.get(entidad_id)
            if estado_actual:
                hass.states.async_set(entidad_id, estado_actual.state, {
                    **dict(estado_actual.attributes),
                    "options": lista_bascula
                })
        
        id_purga = "select.porcentaje_panadero_pan_select_retirar_harina_del_inventario"
        estado_purga = hass.states.get(id_purga)
        if estado_purga:
            hass.states.async_set(id_purga, estado_purga.state, {
                **dict(estado_purga.attributes),
                "options": lista_purga
            })

    async def gestion_anadir_harina_service(call: ServiceCall):
        """Toma el texto exacto escrito en tu cuadro nativo de harina y lo registra en disco."""
        estado_texto = hass.states.get("text.nombre_nueva_harina")
        nueva_harina = estado_texto.state.strip() if estado_texto else ""
        if not nueva_harina or nueva_harina.upper() in ["", "UNKNOWN", "UNAVAILABLE", "---"]: return

        _LOGGER.info("Registrando nueva materia prima en el almacen: %s", nueva_harina)

        def leer_escribir_anadir():
            with open(ruta_harinas_json, "r", encoding="utf-8") as f: harinas = json.load(f)
            if nueva_harina not in harinas:
                harinas.append(nueva_harina)
                with open(ruta_harinas_json, "w", encoding="utf-8") as f: json.dump(harinas, f, indent=4, ensure_ascii=False)
            return harinas

        lista_actualizada = await hass.async_add_executor_job(leer_escribir_anadir)
        
        if hass.states.get("text.nombre_nueva_harina") is not None:
            await hass.services.async_call("text", "set_value", {"entity_id": "text.nombre_nueva_harina", "value": ""})
            
        await sincronizar_selectores_harina(lista_actualizada)

    async def gestion_eliminar_harina_service(call: ServiceCall):
        """Purga del JSON fisico la harina seleccionada en el menu."""
        estado_select = hass.states.get("select.porcentaje_panadero_pan_select_retirar_harina_del_inventario")
        harina_a_borrar = estado_select.state if estado_select else ""
        if not harina_a_borrar or harina_a_borrar.upper() in ["", "UNKNOWN", "UNAVAILABLE", "---"]: return

        _LOGGER.info("Purgando del almacen la materia prima: %s", harina_a_borrar)

        def leer_escribir_eliminar():
            with open(ruta_harinas_json, "r", encoding="utf-8") as f: harinas = json.load(f)
            if harina_a_borrar in harinas:
                harinas.remove(harina_a_borrar)
                with open(ruta_harinas_json, "w", encoding="utf-8") as f: json.dump(harinas, f, indent=4, ensure_ascii=False)
            return harinas

        lista_actualizada = await hass.async_add_executor_job(leer_escribir_eliminar)
        await sincronizar_selectores_harina(lista_actualizada)
        
        if hass.states.get("select.porcentaje_panadero_pan_select_retirar_harina_del_inventario") is not None:
            await hass.services.async_call("select", "select_option", {"entity_id": "select.porcentaje_panadero_pan_select_retirar_harina_del_inventario", "option": "---"})

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

            try:
                async def inyectar_harina_segura(id_selector, clave_json, fallback_default):
                    marca_guardada = receta.get(clave_json, fallback_default)
                    state_obj = hass.states.get(id_selector)
                    
                    if state_obj and "options" in state_obj.attributes:
                        opciones_sistema = state_obj.attributes["options"]
                        if marca_guardada in opciones_sistema:
                            await hass.services.async_call("select", "select_option", {"entity_id": id_selector, "option": marca_guardada})
                            return
                    
                    _LOGGER.info("La harina '%s' ya no existe en el catalogo. Restableciendo %s a su estado base traducido.", marca_guardada, id_selector)
                    
                    atributos_actuales = dict(state_obj.attributes) if state_obj else {}
                    hass.states.async_set(id_selector, "unknown", atributos_actuales)

                await inyectar_harina_segura("select.harina_principal_1", "harina_1_nombre", "HARINA 1")
                await inyectar_harina_segura("select.harina_secundaria_2", "harina_2_nombre", "HARINA 2")
                await inyectar_harina_segura("select.harina_secundaria_3", "harina_3_nombre", "HARINA 3")

                for key, val in receta.items():
                    if key in ["tipo_levadura", "base_tang_zhong", "harina_1_nombre", "harina_2_nombre", "harina_3_nombre"]:
                        continue
                    await forzar_inyeccion_slider(key, val)
            finally:
                pass

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

            const.RECETA_ACTIVA_MEMORIA = nombre_id.replace("_", " ").title()
            hass.states.async_set("sensor.formula_activa", const.RECETA_ACTIVA_MEMORIA, {
                "friendly_name": "Receta en el Obrador", "icon": "mdi:notebook-check"
            })
            const.CARGANDO_RECETA_BLOQUEO = False


    async def alternar_tipo_levadura_service(call: ServiceCall):
        """Conmuta entre levadura aplicando el factor x3 o /3 leyendo los numeros reales actuales."""
        tipo_actual = obtener_tipo_levadura_actual()
        nuevo_tipo = "fresca" if tipo_actual == "seca" else "seca"

        st_leva = hass.states.get("number.levadura")
        st_leva_pref = hass.states.get("number.levadura_prefermento")

        pct_leva_principal = float(st_leva.state) if st_leva and st_leva.state not in ["unavailable", "unknown", ""] else 0.7
        pct_leva_pref_val = float(st_leva_pref.state) if st_leva_pref and st_leva_pref.state not in ["unavailable", "unknown", ""] else 0.0

        nuevo_pct = round(pct_leva_principal * 3.0, 2) if tipo_actual == "seca" else round(pct_leva_principal / 3.0, 2)
        nuevo_pct_pref = round(pct_leva_pref_val * 3.0, 2) if tipo_actual == "seca" else round(pct_leva_pref_val / 3.0, 2)

        establecer_tipo_levadura_actual(nuevo_tipo)

        if hass.states.get("number.levadura") is not None:
            await hass.services.async_call("number", "set_value", {"entity_id": "number.levadura", "value": nuevo_pct})
        if pct_leva_pref_val > 0 and hass.states.get("number.levadura_prefermento") is not None:
            await hass.services.async_call("number", "set_value", {"entity_id": "number.levadura_prefermento", "value": nuevo_pct_pref})

        estado_actual = hass.states.get(ID_BOTON_LEVADURA)
        atributos_base = dict(estado_actual.attributes) if estado_actual else {}
        atributos_base["tipo_levadura"] = nuevo_tipo
        atributos_base["options"] = ["fresca", "seca"]
        hass.states.async_set(ID_BOTON_LEVADURA, nuevo_tipo, atributos_base)

    async def alternar_tang_zhong_base_service(call: ServiceCall):
        """Conmuta la base liquida del Tang-Zhong y fuerza el balanceo matematico de liquidos."""
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

    # REGISTRO DE SERVICIOS EN EL CORE
    hass.services.async_register(DOMAIN, "guardar_formula", guardar_formula_service)
    hass.services.async_register(DOMAIN, "confirmar_sobreescritura", confirmar_sobreescritura_service)
    hass.services.async_register(DOMAIN, "eliminar_formula", eliminar_formula_service)
    hass.services.async_register(DOMAIN, "cargar_formula_en_sliders", cargar_formula_en_sliders_service)
    hass.services.async_register(DOMAIN, "alternar_tipo_levadura", alternar_tipo_levadura_service)
    hass.services.async_register(DOMAIN, "alternar_tang_zhong_base", alternar_tang_zhong_base_service)
    hass.services.async_register(DOMAIN, "balancear_harinas", balancear_harinas_service)
    hass.services.async_register(DOMAIN, "anadir_harina", gestion_anadir_harina_service)
    hass.services.async_register(DOMAIN, "eliminar_harina", gestion_eliminar_harina_service)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    try:
        def leer_json():
            if os.path.exists(ruta_json):
                with open(ruta_json, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        data = await hass.async_add_executor_job(leer_json)

        def leer_harinas_inicio():
            if os.path.exists(ruta_harinas_json):
                with open(ruta_harinas_json, "r", encoding="utf-8") as f: return json.load(f)
            return []
        listado_harinas = await hass.async_add_executor_job(leer_harinas_inicio)
        if listado_harinas:
            await sincronizar_selectores_harina(listado_harinas)
    except Exception:
        pass

    return True
