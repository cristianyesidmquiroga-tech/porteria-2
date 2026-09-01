"""Tipos de documento de identidad y validación de su número.

En el SENA conviven personas con documentos distintos: aprendices menores de
edad con tarjeta de identidad, mayores con cédula, y población migrante con
cédula de extranjería o PPT. Cada tipo tiene su propio formato, así que validar
"que sean números y ya" deja pasar errores de digitación que después impiden
identificar a la persona en portería.

Referencias de longitud (Registraduría Nacional y Migración Colombia):
  - Cédula de ciudadanía: 6 a 10 dígitos. Las antiguas tienen 6-8; las expedidas
    desde 2000 empiezan por 1 y tienen 10.
  - Tarjeta de identidad: 10 u 11 dígitos (las azules antiguas tenían 10).
  - Cédula de extranjería: 6 o 7 dígitos.
  - PPT (Permiso por Protección Temporal): 7 a 10 dígitos. La Resolución 572
    de 2022 del Ministerio de Salud fijó el número del PPT como numérico de
    7 dígitos, y Migración Colombia advirtió que ese cupo puede crecer, así
    que el rango se deja abierto hasta 10 en vez de exigir 9 como antes
    (exigir 9 rechazaba los PPT que hoy se expiden).
  - Pasaporte: alfanumérico, de 5 a 15 caracteres según el país emisor.
"""
import re

# clave -> (etiqueta, longitud minima, longitud maxima, solo digitos)
TIPOS_DOCUMENTO = {
    'CC': ('Cédula de ciudadanía', 6, 10, True),
    'TI': ('Tarjeta de identidad', 10, 11, True),
    'CE': ('Cédula de extranjería', 6, 7, True),
    'PPT': ('Permiso por Protección Temporal', 7, 10, True),
    'PA': ('Pasaporte', 5, 15, False),
}

TIPO_POR_DEFECTO = 'CC'

# Tipos cuyo número NO puede empezar por cero, y el porqué de cada uno:
#
#   - CC y TI comparten el NUIP (Resolución 3571 de 2003 de la Registraduría
#     Nacional), que se asigna de forma consecutiva a partir de 1.000.000.000:
#     por construcción empieza por 1. Las cédulas anteriores al NUIP se
#     asignaron también en rangos consecutivos desde el 1 y se imprimen sin
#     ceros de relleno.
#
# CE, PPT y PA quedan deliberadamente FUERA: no hay norma publicada de
# Migración Colombia que prohíba el cero inicial en esos números, y varios
# países imprimen pasaportes con ceros delante. La prohibición absoluta que
# había aquí antes (cualquier tipo, cualquier longitud) no tenía respaldo
# normativo y dejaba fuera del sistema a población migrante con documentos
# legítimos, que es justo a quien más caro le sale no poder entrar.
#
# El motivo original de la regla —documentos copiados de una hoja de cálculo
# que perdieron el formato— se ataja donde de verdad ocurre: leyendo el Excel
# con las columnas forzadas a texto (ver api_importar_usuarios_excel).
TIPOS_SIN_CERO_INICIAL = ('CC', 'TI')


def etiqueta_tipo(tipo):
    datos = TIPOS_DOCUMENTO.get((tipo or '').upper())
    return datos[0] if datos else 'Documento'


def descripcion_formato(tipo):
    """Texto de ayuda para mostrar junto al campo."""
    datos = TIPOS_DOCUMENTO.get((tipo or '').upper())
    if not datos:
        return ''
    _, minimo, maximo, solo_digitos = datos
    unidad = 'dígitos' if solo_digitos else 'caracteres'
    if minimo == maximo:
        return f'{minimo} {unidad}'
    return f'entre {minimo} y {maximo} {unidad}'


def normalizar_numero(numero):
    """Quita espacios, puntos y guiones, que la gente escribe por costumbre."""
    if not numero:
        return ''
    return re.sub(r'[\s.\-]', '', str(numero)).strip()


def validar_documento(tipo, numero):
    """Valida el número según el tipo. Devuelve (numero_limpio, error_o_None).

    El número se devuelve ya normalizado para guardarlo siempre igual: si uno
    escribe "1.098.765.432" y otro "1098765432", en portería serían dos
    personas distintas al buscar por documento.
    """
    tipo = (tipo or TIPO_POR_DEFECTO).upper()
    if tipo not in TIPOS_DOCUMENTO:
        return '', 'Selecciona un tipo de documento válido.'

    limpio = normalizar_numero(numero)
    if not limpio:
        return '', 'Escribe tu número de documento.'

    etiqueta, minimo, maximo, solo_digitos = TIPOS_DOCUMENTO[tipo]

    if solo_digitos:
        if not limpio.isdigit():
            return limpio, f'El número de {etiqueta.lower()} debe tener solo números.'
        # Solo para los tipos donde la numeración oficial lo impide (ver
        # TIPOS_SIN_CERO_INICIAL); en CE y PPT un cero inicial puede ser real.
        if tipo in TIPOS_SIN_CERO_INICIAL and limpio.startswith('0'):
            return limpio, (f'Un número de {etiqueta.lower()} no empieza por '
                            f'cero. Revísalo o cambia el tipo de documento.')
    else:
        if not limpio.isalnum():
            return limpio, f'El {etiqueta.lower()} solo admite letras y números.'

    if len(limpio) < minimo or len(limpio) > maximo:
        if minimo == maximo:
            esperado = f'{minimo}'
        else:
            esperado = f'entre {minimo} y {maximo}'
        unidad = 'dígitos' if solo_digitos else 'caracteres'
        return limpio, (f'Un número de {etiqueta.lower()} debe tener {esperado} '
                        f'{unidad}, y escribiste {len(limpio)}. '
                        f'Revísalo o cambia el tipo de documento.')

    return limpio, None


def tipo_probable(numero):
    """Sugiere el tipo más probable a partir del número.

    Solo es una ayuda para preseleccionar el desplegable: la persona siempre
    puede corregirlo, porque las longitudes se solapan entre tipos.
    """
    limpio = normalizar_numero(numero)
    if not limpio.isdigit():
        return 'PA' if limpio else TIPO_POR_DEFECTO
    if limpio.startswith('0'):
        # Ni la cédula ni la tarjeta de identidad empiezan por cero
        # (ver TIPOS_SIN_CERO_INICIAL), así que sugerir CC sería sugerir un
        # tipo con el que el número no puede validar.
        return 'CE' if len(limpio) <= 7 else 'PPT'
    if len(limpio) == 11:
        return 'TI'
    if len(limpio) == 10:
        # Las cédulas modernas empiezan por 1; las TI de menores también, pero
        # la cédula es mucho más frecuente en el sistema.
        return 'CC'
    if len(limpio) in (6, 7):
        return 'CC'
    return TIPO_POR_DEFECTO
