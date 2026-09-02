# Licencias de terceros

Este proyecto autoaloja (sirve desde su propio dominio, en vez de depender
de un CDN o servicio externo) el siguiente código y los siguientes modelos
de terceros. Se listan aquí origen, versión y licencia, y dónde vive cada
uno en el repositorio.

Todas las licencias listadas permiten uso comercial y modificación.
Los archivos JavaScript/CSS se copian sin modificar salvo donde se indica
lo contrario (banner de licencia añadido, rutas de fuentes reescritas).

---

## Código ejecutable

### html5-qrcode 2.3.8
- **Qué es:** lector de códigos QR/barras usado en `porteria/scanner.html`.
- **Origen:** https://github.com/mebjas/html5-qrcode (autor: Minhaz, `mebjas`)
- **Versión:** 2.3.8
- **Licencia:** Apache License 2.0
- **Ubicación:** `app/static/js/html5-qrcode-2.3.8.min.js`
- **Nota:** el archivo minificado se copió originalmente sin el aviso de
  copyright/licencia que exige Apache-2.0 en las redistribuciones. Se le
  añadió un banner al inicio del archivo con el aviso y el texto de la
  licencia (encabezado únicamente; el texto completo también está
  disponible en el enlace de origen).

### Chart.js 4.5.1
- **Qué es:** librería de gráficas usada en los paneles de portería
  (`porteria/dashboard.html`, `porteria/analytics_rol.html`).
- **Origen:** https://www.chartjs.org / https://github.com/chartjs/Chart.js
- **Versión:** 4.5.1
- **Licencia:** MIT
- **Ubicación:** `app/static/js/chart-4.5.1.umd.min.js`
- **Nota:** copiado a `/static` con versión fijada en el nombre del
  archivo. **Pendiente:** los templates `porteria/dashboard.html` y
  `porteria/analytics_rol.html` todavía cargan Chart.js sin versión fijada
  desde `cdn.jsdelivr.net/npm/chart.js` — quedan fuera del alcance de este
  cambio porque los edita otra persona del equipo. Deben apuntarse a este
  archivo local para completar la migración.

### particles.js 2.0.0
- **Qué es:** fondo animado decorativo, cargado en todas las páginas vía
  `base.html`.
- **Origen:** https://github.com/VincentGarreau/particles.js
- **Versión:** 2.0.0
- **Licencia:** MIT
- **Ubicación:** `app/static/js/particles-2.0.0.min.js`

### vanilla-tilt.js 1.8.0
- **Qué es:** efecto de inclinación 3D decorativo en tarjetas, cargado en
  todas las páginas vía `base.html`.
- **Origen:** https://github.com/micku7zu/vanilla-tilt.js
- **Versión:** 1.8.0
- **Licencia:** MIT
- **Ubicación:** `app/static/js/vanilla-tilt-1.8.0.min.js`

### html2canvas 1.4.1
- **Qué es:** captura el carnet como imagen para su descarga
  (`usuarios/profile.html`).
- **Origen:** https://github.com/niklasvh/html2canvas
- **Versión:** 1.4.1
- **Licencia:** MIT
- **Ubicación:** `app/static/js/html2canvas-1.4.1.min.js`

### Font Awesome Free 5.15.4
- **Qué es:** iconografía usada en toda la interfaz.
- **Origen:** https://fontawesome.com / https://github.com/FortAwesome/Font-Awesome
- **Versión:** 5.15.4
- **Licencia:** combinada —
  - Iconos: CC BY 4.0
  - Fuentes (`.woff2`, `.ttf`): SIL Open Font License 1.1
  - Código (CSS/JS): MIT
- **Ubicación:** `app/static/css/fontawesome-5.15.4.min.css` +
  `app/static/webfonts/fa-solid-900.*`, `app/static/webfonts/fa-regular-400.*`
- **Nota:** solo se autoalojan los estilos "solid" (`fas`) y "regular"
  (`far`), que son los únicos usados en el proyecto; no se incluyó el
  paquete "brands" (`fab`, iconos de marcas) por no usarse.

### Outfit (Google Fonts)
- **Qué es:** tipografía principal de la interfaz.
- **Origen:** https://fonts.google.com/specimen/Outfit —
  https://github.com/Outfitio/Outfit-Fonts
- **Versión:** v15 (la servida por Google Fonts al momento de la descarga)
- **Licencia:** SIL Open Font License 1.1 — Copyright 2021 The Outfit
  Project Authors
- **Ubicación:** `app/static/fonts/outfit/outfit-latin.woff2`,
  `app/static/fonts/outfit/outfit-latin-ext.woff2`,
  hoja de estilos en `app/static/css/outfit.css`

### Logo del SENA
- **Qué es:** logotipo institucional usado en cabecera, sidebar, carnet y
  páginas de autenticación.
- **Origen:** Wikimedia Commons —
  https://commons.wikimedia.org/wiki/File:Sena_Colombia_logo.svg
- **Licencia:** ver la página de la obra en Wikimedia Commons (logotipo
  institucional de una entidad pública colombiana).
- **Ubicación:** `app/static/img/sena-logo.svg`

---

## Modelos de detección/segmentación facial

### YuNet (face_detection_yunet_2023mar.onnx)
- **Qué es:** detector de rostros usado al validar la foto de perfil
  (`app/utils/imagenes.py`).
- **Origen:** OpenCV Zoo —
  https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
  (autor: Shiqi Yu)
- **Versión:** 2023mar
- **Licencia:** MIT
- **Ubicación:** `app/static/modelos/face_detection_yunet_2023mar.onnx`

### Segmentador de selfies multiclase (selfie_multiclass_256x256.onnx)
- **Qué es:** segmentación por clase de píxel (fondo, pelo, piel de cuerpo,
  piel de cara, ropa, accesorios), usada para detectar rostro cubierto por
  mascarilla, bufanda o gorra (`app/utils/imagenes.py`).
- **Origen:** Google MediaPipe, paquete "selfie_multiclass_256x256" del
  Image Segmenter —
  https://ai.google.dev/edge/mediapipe/solutions/vision/image_segmenter
- **Licencia:** Apache License 2.0
- **Ubicación:** `app/static/modelos/selfie_multiclass_256x256.onnx`
- **Nota:** el archivo distribuido en este repositorio es una conversión
  del modelo original de TFLite a ONNX (hecha con `tf2onnx`), verificada
  contra la salida del modelo original (diferencia máxima 1e-4, mismo
  argmax en el 100% de los píxeles comprobados). No es una modificación
  del comportamiento del modelo, solo de su formato de serialización.

---

## Lector de códigos (referencia adicional)

El lector `html5-qrcode` sustituyó una carga previa desde `unpkg.com` sin
versión fijada, precisamente por el mismo motivo que motivó este documento:
una librería sin versión fijada puede cambiar sin que nadie del proyecto lo
note. Ver el comentario en `app/templates/porteria/scanner.html`.
