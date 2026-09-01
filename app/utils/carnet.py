"""Reglas del carnet institucional: perfiles impresos y particion del nombre.

Este modulo es el UNICO sitio donde se decide que perfil oficial le toca a cada
cargo del sistema. El motivo es que `cargo` gobierna permisos (ver las
propiedades puede_operar_porteria / puede_asesorar / puede_gestionar_asistencia
en app/models/usuarios.py): cambiar sus valores para que coincidan con los del
carnet impreso le quitaria o le daria permisos a personas reales. Asi que los
cargos se dejan como estan y aqui solo se traduce cargo -> perfil impreso.
"""

import os

# Perfiles que existen en el formato impreso del SENA. El de APRENDIZ es el
# unico con disposicion distinta (ficha, programa, fecha y poliza).
PERFIL_APRENDIZ = 'APRENDIZ'
PERFIL_INSTRUCTOR = 'INSTRUCTOR'
PERFIL_CONTRATISTA = 'CONTRATISTA'
PERFIL_FUNCIONARIO = 'FUNCIONARIO'
PERFIL_SUBDIRECTOR = 'SUBDIRECTOR'

PERFILES_VALIDOS = (
    PERFIL_APRENDIZ, PERFIL_INSTRUCTOR, PERFIL_CONTRATISTA,
    PERFIL_FUNCIONARIO, PERFIL_SUBDIRECTOR,
)

# Traduccion por defecto de los cargos que existen HOY en la base a los cinco
# perfiles del formato impreso. Los cargos del sistema y los perfiles del
# carnet no coinciden uno a uno, asi que:
#   - Administrativo y Administrador -> FUNCIONARIO (personal de planta del
#     centro; "Administrador" aqui es un rol operativo del sistema, no el
#     subdirector del centro).
#   - Celador -> CONTRATISTA, porque la vigilancia se contrata a un tercero,
#     no es planta del SENA.
#   - SUBDIRECTOR no tiene cargo equivalente en el sistema: se emite solo si
#     se anade el cargo y se declara aqui (o por variable de entorno).
PERFILES_POR_CARGO_POR_DEFECTO = {
    'aprendiz': PERFIL_APRENDIZ,
    'instructor': PERFIL_INSTRUCTOR,
    'celador': PERFIL_CONTRATISTA,
    'porteria': PERFIL_CONTRATISTA,
    'portería': PERFIL_CONTRATISTA,
    'contratista': PERFIL_CONTRATISTA,
    'administrativo': PERFIL_FUNCIONARIO,
    'administrador': PERFIL_FUNCIONARIO,
    'funcionario': PERFIL_FUNCIONARIO,
    'subdirector': PERFIL_SUBDIRECTOR,
}

PERFIL_POR_DEFECTO = PERFIL_FUNCIONARIO


def _leer_mapeo_entorno():
    """Lee CARNET_PERFILES: "Cargo:PERFIL,Otro Cargo:PERFIL".

    Permite que otro centro reasigne los cargos sin tocar el codigo. Un valor
    mal escrito se ignora en lugar de tumbar el arranque: quedarse sin carnet
    por un error de tipeo en una variable seria peor que usar el mapeo base.
    """
    crudo = os.environ.get('CARNET_PERFILES', '')
    mapeo = {}
    for pareja in crudo.split(','):
        if ':' not in pareja:
            continue
        cargo, perfil = pareja.split(':', 1)
        cargo = cargo.strip().lower()
        perfil = perfil.strip().upper()
        if cargo and perfil in PERFILES_VALIDOS:
            mapeo[cargo] = perfil
    return mapeo


def perfiles_por_cargo():
    """Mapeo efectivo cargo -> perfil, con las sobrescrituras del entorno."""
    mapeo = dict(PERFILES_POR_CARGO_POR_DEFECTO)
    mapeo.update(_leer_mapeo_entorno())
    return mapeo


def perfil_de_cargo(cargo):
    """Perfil impreso que le corresponde a un cargo del sistema."""
    if not cargo:
        return PERFIL_POR_DEFECTO
    return perfiles_por_cargo().get(str(cargo).strip().lower(),
                                    PERFIL_POR_DEFECTO)


# Como se abrevia cada tipo de documento en el carnet impreso. El formato
# oficial escribe "C.C." para los perfiles que no son aprendiz, pero muchos
# aprendices son menores y llevan tarjeta de identidad, asi que se imprime la
# abreviatura que de verdad corresponde en vez de "C.C." para todo el mundo.
ABREVIATURAS_DOCUMENTO = {
    'CC': 'C.C.',
    'TI': 'T.I.',
    'CE': 'C.E.',
    'PPT': 'PPT',
    'PA': 'Pasaporte',
}


def abreviatura_documento(tipo):
    return ABREVIATURAS_DOCUMENTO.get((tipo or 'CC').upper(), 'C.C.')


def partir_nombre(nombre_completo, nombres=None, apellidos=None):
    """Devuelve (nombres, apellidos) para las dos lineas del carnet.

    Si la persona ya declaro sus nombres y apellidos por separado se usan tal
    cual: es el unico dato fiable. Solo cuando faltan se reparte el campo
    `nombre` (que es el unico que existe en la base historica), y se hace SOLO
    para pintar: nunca se guarda el resultado. Un reparto equivocado en un
    apellido compuesto ("De La Cruz", "Van Der Berg") deja una linea fea, no
    un dato corrupto.

    Reparto: con 4 o mas palabras, mitad y mitad dejando la palabra sobrante
    del lado de los apellidos; con 3, una de nombre y dos de apellido, que es
    la forma habitual en Colombia.
    """
    nombres = (nombres or '').strip()
    apellidos = (apellidos or '').strip()
    if nombres and apellidos:
        return nombres, apellidos

    palabras = (nombre_completo or '').split()
    if not palabras:
        return (nombres, apellidos)
    if len(palabras) == 1:
        return palabras[0], apellidos
    if len(palabras) == 2:
        return palabras[0], palabras[1]
    if len(palabras) == 3:
        return palabras[0], ' '.join(palabras[1:])
    corte = len(palabras) // 2
    return ' '.join(palabras[:corte]), ' '.join(palabras[corte:])
