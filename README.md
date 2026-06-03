<p align="center"> <img src="custom_components/porcentaje_panadero/brand/icon.png" width="300" />  </p>
 
# Porcentaje Panadero para Home Assistant
  
Herramienta para calcular masas de pan basada en el porcentaje panadero, diseñada para integrarse en tu panel de Home Assistant.

## ✨ Características

* **Gestión Total:** Añade, crea, guarda y modifica tus fórmulas fácilmente.

* **Doble visualización:** Consúltala directamente desde la tarjeta del dashboard *o ábrela en un **popup** (diseñado especialmente para hacer capturas de pantalla limpias), es requerido otros complementos de hacs.

* **Motor Matematico:** Introduce la cantidad de masa final (hasta 10kg) y mira cómo oscilan y se recalculan al milisegundo los gramos netos de harinas, agua, sal, levaduras y hasta 7 ingredientes extras enriquecidos (AOVE, mantequilla, huevo, leche...).

* **Recetario:** Guarda, modifica y elimina tus fórmulas directamente desde la tarjeta visual Lovelace sincronizándose con un archivo `formulas.json` local.

* **Confirmaciones Móviles:** Pasarela que lanza alertas de confirmación a tu teléfono móvil ante cambios y o borrados accidentales en las formulas.

* **Algoritmo Térmico:** Calcula la temperatura ideal del agua del amasado cruzando variables manuales cortas de Lovelace o enlazándose en caliente a tu termómetro Zigbee físico de la cocina.

* **Nativo & Bilingüe:** Totalmente compatible con la API moderna de Home Assistant Core, ofreciendo traducción automática e independiente en Castellano e Inglés.

* **Porcentaje Panadero** es una integración para Home Assistant que transforma tu servidor en un asistente de obrador profesional asíncrono puro. Permite calcular de forma reactiva y en tiempo real los gramos netos de cada ingrediente basándose en el porcentaje panadero y desglosar de forma dinámica elaboraciones complejas con masas madre, poolish o bigas.

## 📸 Capturas de pantalla

<p align="center">
  <img src="images/capa3.png" width="40%" alt="Vista 1">
  <img src="images/capb2.png" width="40%" alt="Vista 2">
</p>

## ⚙️ Parámetros de Configuración

Define en gramos la cantidad de **masa final** que deseas y, en **porcentaje**, el resto de los valores del cálculo.

*   **Inóculo de Masa Madre:** Cantidad exacta de masa madre activa (de tu tarro de reserva) necesaria para iniciar el prefermento. Se calcula automáticamente según el porcentaje de prefermento seleccionado.

*   **Hidratación de Masa Madre:** Porcentaje de agua respecto a la harina en tu masa madre.

*   **Porcentaje de Masa Madre:** Un porcentaje del 33.3% equivale a una proporción 1:1:1 (masa madre | harina | agua) del refresco tradicional; un 20% sería un refresco 1:2:2, etc.

*   **Harina del Prefermento:** Indica de cuál de las harinas de la receta se restará la cantidad destinada al prefermento (por defecto, se descuenta de la Harina 1). El sistema solo te permitirá elegir entre las harinas que hayas activado y estén disponibles.

*   **Control Térmico:** Control de la temperatura final de la masa, donde entran en escena las temperaturas ambiente, de la harina, del prefermento (solo válido si está activado en la fórmula) y de la fricción de la amasadora (si se utiliza).

---


## 📥 Instalación

### Método 1: HACS (Recomendado)

1. Ve a **HACS** en tu Home Assistant.
2. Haz clic en los tres puntos verticales de la esquina superior derecha y selecciona **Repositorios personalizados**.
3. Pega la URL de este repositorio: `https://github.com/DelBierzo/porcentaje_panadero`
4. En **Categoría**, selecciona estrictamente **Integración** y haz clic en **Añadir**.
5. Descarga la ultima versión, ve a Ajustes y **Reinicia** Home Assistant.
6. Ve a **Ajustes ➔ Dispositivos y servicios ➔ Añadir integración**, busca `Porcentaje Panadero` y configúralo en un clic.
---

## La integración genera de forma automática 53 entidades nativas.
 
 * en modo **basico** (Tarjeta_Lovelace_Card _v1_Basic.yaml). Instala, añade la tarjeta basica y listo!

 * en modo **avanzado** (Tarjeta_Lovelace_Card_v2_Advanced.yaml), requiere de la descarga los siguientes complementos desde **HACS** (Home Assistant Community Store):

*   📦 [card-mod](https://github.com/thomasloven/lovelace-card-mod) — Permite personalizar los estilos CSS de la tarjeta.
*   📦 [expander-card](https://github.com/MelleD/lovelace-expander-card) — Gestiona los menús desplegables de la interfaz.
*   📦 [template-entity-row](https://github.com/thomasloven/lovelace-template-entity-row) — Permite usar plantillas avanzadas en las filas.
*   📦 [Custom Features for Home Assistant Cards](https://github.com/Nerwyn/custom-card-features) — Añade características extendidas a las tarjetas.
*   📦 [Popup Card](https://github.com/olivierplante/popup-card) — Necesario para la visualización en ventana flotante.

### Activación de la Integración Popup

*   Ve a **Ajustes** → **Dispositivos y servicios** → Haz clic en **Añadir integración**.
*   Busca **"Popup Card"** y selecciónala.
*   Haz clic en **Enviar** (esta integración no requiere ninguna configuración adicional).

## 📱 Configuración De Avisos

Para habilitar las alertas interactivas de confirmación ante borrados accidentales tienes que añadir si o si, la automatizacion adjunta (Automation_ES) 

---

## 🛠️ Desarrollo Local y Contribuciones / Contributions

Si deseas modificar las ecuaciones panaderas de trastienda, optimizar el balanceo reactivo de harinas al 100% o proponer mejoras en la interfaz, eres más que bienvenido a abrir un *Pull Request* o reportar un *Issue*.

### Licencia / License
Este proyecto es software libre y está licenciado bajo los términos de la Licencia MIT.

---

Developed with 🥖 & ☕ by **[@DelBierzo](https://github.com)**.
