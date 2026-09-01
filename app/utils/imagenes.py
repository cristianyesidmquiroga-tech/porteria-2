"""Procesado de las fotos de perfil.

Las fotos se muestran en el escaner de porteria, donde lo que importa es que
carguen rapido: el celador las mira unos segundos mientras alguien espera en la
puerta. Por eso toda imagen que entra se normaliza a un JPEG pequeno en vez de
guardarse tal cual (habia fotos de 2 MB para mostrarse a 200 px).

De paso resuelve dos problemas de privacidad:
  - Se eliminan los metadatos EXIF, que en una foto de celular incluyen
    coordenadas GPS y modelo del dispositivo.
  - El nombre de archivo es fijo por usuario, asi que una foto nueva reemplaza
    a la anterior en vez de dejarla huerfana en el disco para siempre.
"""
import io
import logging
import os

from PIL import Image, ImageOps, UnidentifiedImageError

# Tope de pixeles al descomprimir. Un PNG de paleta de 134 KB puede expandirse a
# 144 millones de pixeles; con las conversiones a RGBA y RGB vivas a la vez eso
# supera el limite de memoria del contenedor (1 GB) y mata al unico worker de
# gunicorn, dejando la porteria sin escaner. 40 millones sobra para cualquier
# foto de celular actual (un movil de 48 Mpx da 48 millones... se deja 50).
Image.MAX_IMAGE_PIXELS = 50_000_000
MAXIMO_PIXELES = 50_000_000

logger = logging.getLogger(__name__)

# Las fotos se muestran como maximo a ~200 px; 512 deja margen para pantallas
# de alta densidad sin desperdiciar peso.
LADO_MAXIMO = 512
CALIDAD_JPEG = 82

# SVG queda fuera a proposito: admite <script> y no es una imagen de mapa de bits.
EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif'}


def extension_permitida(nombre_archivo):
    if not nombre_archivo or '.' not in nombre_archivo:
        return False
    return nombre_archivo.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS


def nombre_foto(usuario_id):
    """Nombre fijo por usuario, para que cada foto nueva reemplace a la anterior."""
    return f"user_{usuario_id}.jpg"


def procesar_foto(origen, destino, lado_maximo=LADO_MAXIMO, calidad=CALIDAD_JPEG):
    """Normaliza una imagen y la guarda como JPEG optimizado.

    `origen` puede ser una ruta o un archivo en memoria. Devuelve True si la
    imagen era valida y se guardo; False si no se pudo interpretar.

    Abrir la imagen con Pillow tambien sirve de validacion: un archivo que solo
    tiene extension de imagen pero no lo es, falla aqui y nunca se guarda.
    """
    try:
        with Image.open(origen) as imagen:
            # Se comprueba el tamano ANTES de convertir: convertir es lo que
            # reserva la memoria, y para entonces ya seria tarde.
            ancho, alto = imagen.size
            if ancho * alto > MAXIMO_PIXELES:
                logger.warning("Imagen rechazada por tamano: %sx%s pixeles",
                               ancho, alto)
                return False

            # Aplica la rotacion que indica el EXIF y descarta el resto de los
            # metadatos (incluido el GPS).
            imagen = ImageOps.exif_transpose(imagen)

            # Los formatos con transparencia se aplanan sobre blanco: JPEG no
            # tiene canal alfa y sin esto el fondo saldria negro.
            if imagen.mode in ('RGBA', 'LA', 'P'):
                imagen = imagen.convert('RGBA')
                fondo = Image.new('RGB', imagen.size, (255, 255, 255))
                fondo.paste(imagen, mask=imagen.split()[-1])
                imagen = fondo
            elif imagen.mode != 'RGB':
                imagen = imagen.convert('RGB')

            imagen.thumbnail((lado_maximo, lado_maximo), Image.LANCZOS)

            os.makedirs(os.path.dirname(destino), exist_ok=True)
            imagen.save(destino, format='JPEG', quality=calidad,
                        optimize=True, progressive=True)
        return True
    except Image.DecompressionBombError as error:
        # No hereda de OSError ni de ValueError, asi que sin esta rama subia
        # como excepcion no capturada y devolvia un 500.
        logger.warning("Imagen rechazada por bomba de descompresion: %s", error)
        return False
    except (UnidentifiedImageError, OSError, ValueError) as error:
        logger.warning("No se pudo procesar la imagen: %s", error)
        return False


# Detector facial YuNet (OpenCV Zoo, licencia MIT, Shiqi Yu, 232 KB).
# Origen: https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
# El modelo viaja versionado en el repo porque el contenedor de produccion no
# tiene internet garantizado en tiempo de ejecucion. Se eligio YuNet sobre las
# cascadas Haar porque es mucho mas robusto con gafas, angulos y luz irregular
# (requisito explicito: las personas con gafas deben poder subir su foto) y
# ademas da un score de confianza, que las cascadas no dan: un rostro dibujado
# o de anime puntua por debajo del umbral, uno fotografico real por encima.
RUTA_MODELO_YUNET = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'static', 'modelos', 'face_detection_yunet_2023mar.onnx')

# Con la foto de referencia real el score fue 0.94-0.96 incluso oscurecida,
# desenfocada o rotada; 0.8 deja margen amplio para fotos reales y corta
# ilustraciones, que puntuan mas bajo.
UMBRAL_CONFIANZA_ROSTRO = 0.8

# El rostro debe ocupar al menos el 2% del area de la foto: por debajo de eso
# el celador no puede comparar la cara en el escaner (retratos normales dan
# 12-24%; 2% solo rechaza caras diminutas al fondo de la escena).
AREA_MINIMA_ROSTRO = 0.02

# YuNet tiene tamano de entrada fijo por deteccion; 640 px de lado mayor
# mantiene la deteccion rapida sin perder rostros pequenos.
LADO_MAXIMO_DETECCION = 640

# Umbrales de calidad, medidos sobre el recorte del rostro. Los valores salen
# de fotos reales: retratos normales dan nitidez 380-730 y brillo 120-130.
# Los limites se fijan MUY por debajo a proposito, porque un rechazo falso deja
# a esa persona sin carnet digital y sin poder entrar al centro: solo deben
# caer las fotos que de verdad no sirven para reconocer a nadie.
#
# Varianza del laplaciano: mide cuanto detalle hay. Una foto movida o muy
# desenfocada cae por debajo de 20; una apenas suave ronda 170.
NITIDEZ_MINIMA = 55

# Brillo medio del rostro (0-255). Una foto en penumbra baja de 40; una
# quemada por el flash pasa de 230. En ambos casos la cara no se distingue.
BRILLO_MINIMO = 55
BRILLO_MAXIMO = 205

# Con luz muy fuerte de frente la cara se "quema": los pixeles llegan al blanco
# puro y se pierden las facciones. El brillo medio por si solo no lo detecta
# bien (el contraste sube), asi que se mira que proporcion del rostro esta al
# limite del blanco.
PROPORCION_MAXIMA_QUEMADA = 0.35

# Segmentador de selfies multiclase de MediaPipe (Google, licencia Apache-2.0,
# MobileNetV3, 16.4 MB). Clasifica cada pixel en: fondo, pelo, piel del cuerpo,
# piel de la cara, ropa u otros (accesorios). Se usa para detectar el rostro
# tapado (mascarilla, bufanda, gorra): YuNet detecta la cara igual aunque este
# cubierta (medido: score 0.951 sin mascarilla vs 0.941 con ella), pero el
# segmentador deja de marcar "piel de la cara" justo donde hay tela encima.
# Origen: pack "selfie_multiclass_256x256" de MediaPipe Image Segmenter
# (https://ai.google.dev/edge/mediapipe/solutions/vision/image_segmenter),
# convertido de TFLite a ONNX con tf2onnx (salida verificada identica al
# original: diferencia maxima 1e-4, mismo argmax en el 100% de los pixeles).
# Viaja en el repo porque produccion no tiene internet garantizado.
RUTA_MODELO_SEGMENTACION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'static', 'modelos', 'selfie_multiclass_256x256.onnx')

# Indices de clase que devuelve el segmentador.
_SEG_PELO = 1
_SEG_PIEL_CARA = 3
_SEG_ROPA = 4
_SEG_OTROS = 5

# Fraccion minima de "piel de la cara" entre la punta de la nariz y el menton.
# Medido sobre las fotos reales de referencia y 14 variantes benignas (oscura,
# clara, borrosa, girada, pequena, en grises, encuadre apretado, con gafas y
# barba): siempre >= 0.71. Con mascarilla o bufanda simuladas (azul, negra,
# blanca e incluso color piel): siempre <= 0.06. El umbral 0.30 queda a mas
# del doble de distancia de ambos grupos, para que un rechazo falso sea
# improbable: quien no pasa esta comprobacion de verdad lleva algo encima.
CARA_MINIMA_ZONA_INFERIOR = 0.30

# Fraccion maxima de "ropa u otros" en la frente (del borde superior del
# rostro hasta un poco por encima de los ojos, para no rozar unas gafas de
# montura gruesa). Medido: 0.00 en todas las fotos legitimas —las gafas no
# llegan a esa zona— y 0.84-0.85 con gorra calada simulada.
ROPA_MAXIMA_FRENTE = 0.50

# La zona medida debe tener un minimo de pixeles para que la fraccion
# signifique algo; por debajo se omite la comprobacion (fail-open).
_MINIMO_PIXELES_ZONA = 200


def _revisar_oclusion(imagen, rostro):
    """Comprueba con el segmentador que la cara no este tapada por tela.

    `imagen` es el BGR ya reescalado donde detecto YuNet y `rostro` la fila
    que devuelve YuNet (caja + landmarks). Devuelve (valido, mensaje).
    Cualquier fallo del modelo devuelve (True, None): esta comprobacion es un
    refuerzo y nunca debe bloquear una subida por un error interno.
    """
    import cv2
    import numpy as np

    if not os.path.isfile(RUTA_MODELO_SEGMENTACION):
        logger.warning("Modelo de segmentacion no encontrado en %s: se omite "
                       "la deteccion de rostro cubierto.", RUTA_MODELO_SEGMENTACION)
        return True, None

    try:
        alto, ancho = imagen.shape[:2]
        x, y, ancho_rostro, alto_rostro = rostro[:4]
        # Landmarks de YuNet: ojo derecho, ojo izquierdo, nariz.
        ojos_y = (rostro[5] + rostro[7]) / 2.0
        nariz_y = rostro[9]

        # El segmentador esta entrenado con selfies (persona + algo de fondo),
        # no con caras recortadas al hueso: se le pasa el rostro con un margen
        # del 50% a cada lado para darle ese contexto.
        margen = 0.5
        x0 = max(0, int(x - margen * ancho_rostro))
        y0 = max(0, int(y - margen * alto_rostro))
        x1 = min(ancho, int(x + (1 + margen) * ancho_rostro))
        y1 = min(alto, int(y + (1 + margen) * alto_rostro))
        recorte = imagen[y0:y1, x0:x1]
        if recorte.size == 0:
            return True, None
        alto_rec, ancho_rec = recorte.shape[:2]

        # Entrada del modelo: 256x256, RGB, [0,1], NHWC.
        entrada = cv2.resize(recorte, (256, 256)).astype(np.float32) / 255.0
        entrada = cv2.cvtColor(entrada, cv2.COLOR_BGR2RGB)
        red = cv2.dnn.readNetFromONNX(RUTA_MODELO_SEGMENTACION)
        red.setInput(entrada[None])
        clases = red.forward()[0].argmax(-1)  # mapa 256x256 de clases

        # Pasa una coordenada de la imagen al espacio 256x256 del recorte.
        def a_seg(px, py):
            return (px - x0) * 256.0 / ancho_rec, (py - y0) * 256.0 / alto_rec

        caja_x0, caja_y0 = a_seg(x, y)
        caja_x1, caja_y1 = a_seg(x + ancho_rostro, y + alto_rostro)
        _, ojos_seg = a_seg(0, ojos_y)
        _, nariz_seg = a_seg(0, nariz_y)

        def zona(y_arriba, y_abajo):
            sub = clases[max(0, int(y_arriba)):min(256, int(y_abajo)),
                         max(0, int(caja_x0)):min(256, int(caja_x1))]
            return sub if sub.size >= _MINIMO_PIXELES_ZONA else None

        # Zona inferior: de la punta de la nariz al menton. Una mascarilla o
        # bufanda la cubre entera; una barba no la afecta (el segmentador
        # sigue marcando piel de la cara en la zona de la barba).
        inferior = zona(nariz_seg, caja_y1)
        if inferior is not None:
            piel = float((inferior == _SEG_PIEL_CARA).mean())
            if piel < CARA_MINIMA_ZONA_INFERIOR:
                return False, ("Parece que llevas la boca o la nariz tapadas "
                               "(mascarilla, bufanda o similar). Para la foto "
                               "del carnet debe verse tu cara completa: "
                               "retira lo que la cubra y vuelve a tomarla.")

        # Frente: del borde superior del rostro hasta un poco por encima de
        # los ojos (65% del tramo caja-ojos), para que unas gafas de montura
        # gruesa no entren en la zona. El pelo (flequillo) es aceptable; la
        # tela de una gorra o un gorro no.
        frente = zona(caja_y0, ojos_seg - 0.35 * (ojos_seg - caja_y0))
        if frente is not None:
            tela = float(((frente == _SEG_ROPA) | (frente == _SEG_OTROS)).mean())
            if tela > ROPA_MAXIMA_FRENTE:
                return False, ("Parece que llevas una gorra o un gorro que "
                               "tapa parte de tu cara. Quítatelo y toma la "
                               "foto con el rostro despejado, como en un "
                               "documento de identidad.")

        return True, None
    except Exception as error:
        logger.warning("La deteccion de rostro cubierto no pudo ejecutarse: %s",
                       error)
        return True, None


def tiene_un_solo_rostro(ruta):
    """Comprueba que la foto sea un retrato utilizable: exactamente un rostro
    humano real, claro y suficientemente grande.

    La foto se muestra al celador en el escaner de porteria para confirmar la
    identidad de quien entra, asi que se rechazan dibujos, iconos, capturas,
    paisajes y fotos con mas de una persona.

    Devuelve (valido, mensaje). Si OpenCV o el modelo no estan disponibles
    devuelve (True, None): la validacion es un apoyo, no debe bloquear el
    sistema.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.warning("OpenCV no disponible: se omite la validacion facial.")
        return True, None

    if not os.path.isfile(RUTA_MODELO_YUNET):
        logger.warning("Modelo YuNet no encontrado en %s: se omite la "
                       "validacion facial.", RUTA_MODELO_YUNET)
        return True, None

    try:
        # cv2.imread falla con rutas con acentos en Windows; leer los bytes
        # con numpy y decodificar en memoria funciona con cualquier ruta.
        datos = np.fromfile(ruta, dtype=np.uint8)
        imagen = cv2.imdecode(datos, cv2.IMREAD_COLOR)
        if imagen is None:
            return False, "No se pudo procesar la imagen. Intenta con un JPG o PNG."

        alto, ancho = imagen.shape[:2]
        lado = max(alto, ancho)
        if lado > LADO_MAXIMO_DETECCION:
            escala = LADO_MAXIMO_DETECCION / float(lado)
            imagen = cv2.resize(imagen, (int(ancho * escala), int(alto * escala)))
            alto, ancho = imagen.shape[:2]

        detector = cv2.FaceDetectorYN_create(
            RUTA_MODELO_YUNET, "", (ancho, alto),
            UMBRAL_CONFIANZA_ROSTRO, 0.3, 5000)
        _, rostros = detector.detect(imagen)
        rostros = rostros if rostros is not None else []

        if len(rostros) == 0:
            return False, ("No se reconoce un rostro en la foto. Debe ser una "
                           "foto real tuya (no un dibujo, logo o captura de "
                           "pantalla), de frente, con buena luz y la cara "
                           "despejada.")
        if len(rostros) > 1:
            return False, ("Se detectó más de una persona en la foto. "
                           "La foto de perfil debe ser individual: tómala solo "
                           "tú, sin nadie más detrás.")

        x, y, ancho_rostro, alto_rostro = [int(v) for v in rostros[0][:4]]
        if (ancho_rostro * alto_rostro) / float(ancho * alto) < AREA_MINIMA_ROSTRO:
            return False, ("Tu rostro se ve muy pequeño en la foto. Tómala más "
                           "cerca, tipo foto de documento, para que en portería "
                           "puedan reconocerte.")

        # Las dos comprobaciones siguientes miran solo el recorte del rostro,
        # no la foto entera: lo que importa es que la CARA se distinga, aunque
        # el fondo este oscuro o borroso.
        gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        recorte = gris[max(y, 0):y + alto_rostro, max(x, 0):x + ancho_rostro]
        if recorte.size == 0:
            return True, None

        brillo = float(recorte.mean())
        if brillo < BRILLO_MINIMO:
            return False, ("La foto está muy oscura y no se te reconoce la cara. "
                           "Tómala en un lugar con buena luz, de frente a la luz "
                           "y no a contraluz.")

        quemados = float((recorte >= 250).mean())
        if brillo > BRILLO_MAXIMO or quemados > PROPORCION_MAXIMA_QUEMADA:
            return False, ("La foto está demasiado quemada por la luz y no se "
                           "distinguen tus facciones. Evita el flash directo o la "
                           "luz muy fuerte de frente.")

        nitidez = cv2.Laplacian(recorte, cv2.CV_64F).var()
        if nitidez < NITIDEZ_MINIMA:
            return False, ("La foto está borrosa o movida y no se distingue tu "
                           "rostro. Apoya el celular, enfoca bien y vuelve a "
                           "tomarla.")

        # Ultimo filtro: rostro cubierto (mascarilla, bufanda, gorra). YuNet
        # detecta la cara aunque este tapada, asi que esto lo mira un modelo
        # de segmentacion aparte. Las gafas estan permitidas y no lo activan.
        return _revisar_oclusion(imagen, rostros[0])
    except Exception as error:
        logger.warning("La validacion facial no pudo ejecutarse: %s", error)
        return True, None


def comprimir_en_sitio(ruta, lado_maximo=LADO_MAXIMO, calidad=CALIDAD_JPEG):
    """Recomprime una foto ya guardada conservando su nombre y extension.

    Se usa para las fotos que ya estaban en el servidor antes de que existiera
    el procesado en la subida. Conserva el nombre para no tener que tocar la
    columna `foto` de la base de datos.
    """
    try:
        with Image.open(ruta) as imagen:
            formato = imagen.format
            imagen = ImageOps.exif_transpose(imagen)

            if formato == 'PNG' and imagen.mode in ('RGBA', 'LA', 'P'):
                imagen = imagen.convert('RGBA')
            elif imagen.mode not in ('RGB', 'RGBA'):
                imagen = imagen.convert('RGB')

            imagen.thumbnail((lado_maximo, lado_maximo), Image.LANCZOS)

            memoria = io.BytesIO()
            if formato == 'PNG':
                imagen.save(memoria, format='PNG', optimize=True)
            elif formato in ('WEBP',):
                imagen.save(memoria, format='WEBP', quality=calidad, method=6)
            else:
                if imagen.mode != 'RGB':
                    imagen = imagen.convert('RGB')
                imagen.save(memoria, format='JPEG', quality=calidad,
                            optimize=True, progressive=True)

        datos = memoria.getvalue()
        # Solo se sobrescribe si de verdad quedo mas ligera.
        if len(datos) < os.path.getsize(ruta):
            with open(ruta, 'wb') as archivo:
                archivo.write(datos)
            return True
        return False
    except (UnidentifiedImageError, OSError, ValueError) as error:
        logger.warning("No se pudo comprimir %s: %s", ruta, error)
        return False
