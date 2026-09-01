"""Generacion de codigos de barras Code128 como SVG, sin dependencias.

Por que Code128 y no QR: el carnet institucional impreso del SENA lleva codigo
de barras, y el sistema debe emitir lo mismo que el formato oficial. El
sustento normativo es la Resolucion SENA 484 de 2006 (normograma.sena.edu.co),
que exige que el carnet lleve codigo de barras vinculado al numero de registro
pero NO fija la simbologia; por eso Code128 cumple.

Por que Code128 y no EAN/UPC: los codigos que circulan por porteria no son solo
digitos. Los pases manuales usan cadenas como "SENA-VISIT:1098765432" o
"SENA-VEH-E:ABC123" (ver app/routes/porteria/pases.py); solo Code128 admite
letras, digitos y simbolos en un mismo codigo.

Por que SVG dibujado aqui y no una libreria: el codigo se lee desde la pantalla
de un celular, que es el caso mas dificil para un lector lineal. Generar el SVG
propio permite controlar exactamente el ancho, la zona muda y el contraste, y
deja el codigo escalable al 100 % del ancho del carnet sin pixelarse. Una
libreria externa (python-barcode) daria lo mismo a cambio de una dependencia
mas en un proyecto que ya se despliega en contenedor.
"""

# Patrones de anchos de Code128, valores 0..106. Cada cadena alterna
# barra-espacio-barra-espacio-barra-espacio empezando siempre por barra.
# Los valores 0..102 suman 11 modulos; el 106 (Stop) suma 13 y tiene 7 tramos.
_PATRONES = (
    '212222', '222122', '222221', '121223', '121322', '131222', '122213',
    '122312', '132212', '221213', '221312', '231212', '112232', '122132',
    '122231', '113222', '123122', '123221', '223211', '221132', '221231',
    '213212', '223112', '312131', '311222', '321122', '321221', '312212',
    '322112', '322211', '212123', '212321', '232121', '111323', '131123',
    '131321', '112313', '132113', '132311', '211313', '231113', '231311',
    '112133', '112331', '132131', '113123', '113321', '133121', '313121',
    '211331', '231131', '213113', '213311', '213131', '311123', '311321',
    '331121', '312113', '312311', '332111', '314111', '221411', '431111',
    '111224', '111422', '121124', '121421', '141122', '141221', '112214',
    '112412', '122114', '122411', '142112', '142211', '241211', '221114',
    '413111', '241112', '134111', '111242', '121142', '121241', '114212',
    '124112', '124211', '411212', '421112', '421211', '212141', '214121',
    '412121', '111143', '111341', '131141', '114113', '114311', '411113',
    '411311', '113141', '114131', '311141', '411131', '211412', '211214',
    '211232', '2331112',
)

INICIO_B = 104   # Start B: ASCII 32..126 (mayusculas, minusculas, digitos, simbolos)
PARADA = 106     # Stop

# El juego B cubre del espacio (32) a la tilde (126).
_MIN_ASCII = 32
_MAX_ASCII = 126


class DatoNoCodificable(ValueError):
    """El texto tiene caracteres que Code128-B no puede representar."""


def valores_code128(dato):
    """Valores del simbolo, incluidos Start, digito de control y Stop.

    Se usa siempre el juego B: cubre el ASCII imprimible completo. El juego C
    comprimiria las cadenas de solo digitos a la mitad, pero los codigos del
    sistema mezclan letras y digitos, asi que la ganancia seria nula en la
    mayoria y a cambio el codificador seria mucho mas facil de romper.
    """
    if dato is None:
        raise DatoNoCodificable('No hay dato que codificar.')
    texto = str(dato)
    if not texto:
        raise DatoNoCodificable('No hay dato que codificar.')

    valores = [INICIO_B]
    for caracter in texto:
        punto = ord(caracter)
        if not _MIN_ASCII <= punto <= _MAX_ASCII:
            raise DatoNoCodificable(
                'El caracter "%s" no se puede representar en Code128.' % caracter)
        valores.append(punto - _MIN_ASCII)

    # Digito de control: suma ponderada modulo 103. El Start pesa 1 y cada
    # caracter pesa su posicion (1, 2, 3...).
    suma = INICIO_B
    for posicion, valor in enumerate(valores[1:], start=1):
        suma += valor * posicion
    valores.append(suma % 103)
    valores.append(PARADA)
    return valores


def modulos_code128(dato):
    """Secuencia de anchos alternando barra/espacio, empezando por barra."""
    anchos = []
    for valor in valores_code128(dato):
        anchos.extend(int(c) for c in _PATRONES[valor])
    return anchos


def _escapar(texto):
    return (texto.replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def codigo128_svg(dato, alto=70, zona_muda=12, mostrar_texto=True,
                  etiqueta=None):
    """SVG de un codigo de barras Code128-B listo para incrustar en el HTML.

    El SVG no lleva ancho ni alto fijos: solo `viewBox` y
    `preserveAspectRatio="none"`, para que el CSS lo estire al ancho completo
    del contenedor. Es deliberado: leer un codigo de barras desde la pantalla
    de un movil exige el mayor ancho posible.

    zona_muda es el margen blanco obligatorio a cada lado (la norma pide un
    minimo de 10 modulos); sin el, el lector no encuentra donde empieza.
    """
    anchos = modulos_code128(dato)
    ancho_total = sum(anchos) + zona_muda * 2

    alto_svg = alto + (14 if mostrar_texto else 0)

    partes = []
    posicion = zona_muda
    es_barra = True
    for ancho in anchos:
        if es_barra:
            partes.append(
                '<rect x="%d" y="0" width="%d" height="%d" fill="#000"/>'
                % (posicion, ancho, alto)
            )
        posicion += ancho
        es_barra = not es_barra

    texto_svg = ''
    if mostrar_texto:
        leyenda = etiqueta if etiqueta is not None else str(dato)
        texto_svg = (
            '<text x="%.1f" y="%d" text-anchor="middle" font-family="monospace" '
            'font-size="11" fill="#000" letter-spacing="1">%s</text>'
            % (ancho_total / 2, alto_svg - 2, _escapar(leyenda))
        )

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'preserveAspectRatio="none" role="img" aria-label="Codigo de barras %s">'
        '<rect x="0" y="0" width="%d" height="%d" fill="#fff"/>%s%s</svg>'
        % (ancho_total, alto_svg, _escapar(str(dato)),
           ancho_total, alto_svg, ''.join(partes), texto_svg)
    )
