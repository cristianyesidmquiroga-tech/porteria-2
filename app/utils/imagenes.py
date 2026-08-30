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
    except (UnidentifiedImageError, OSError, ValueError) as error:
        logger.warning("No se pudo procesar la imagen: %s", error)
        return False


def tiene_un_solo_rostro(ruta):
    """Comprueba que la foto muestre exactamente una cara.

    Devuelve (valido, mensaje). Si OpenCV no esta disponible devuelve
    (True, None): la validacion es un apoyo, no debe bloquear el sistema.
    """
    try:
        import cv2
    except ImportError:
        logger.warning("OpenCV no disponible: se omite la validacion facial.")
        return True, None

    try:
        clasificador = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        imagen = cv2.imread(ruta)
        if imagen is None:
            return False, "No se pudo procesar la imagen. Intenta con un JPG o PNG."

        gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        rostros = clasificador.detectMultiScale(gris, 1.1, 4)

        if len(rostros) == 0:
            return False, ("No se detectó ningún rostro en la foto. "
                           "Sube una foto donde se vea tu cara.")
        if len(rostros) > 1:
            return False, ("Se detectó más de una persona en la foto. "
                           "La foto de perfil debe ser individual.")
        return True, None
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
