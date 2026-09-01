"""Almacenamiento y servicio de las fotos de perfil.

Las fotos vivian en `app/static/uploads/profiles/` con el nombre `user_<id>.jpg`.
Flask sirve todo lo que hay bajo `static/` sin pedir sesion, y los ids son
consecutivos, asi que cualquiera desde internet podia recorrer `user_1.jpg`,
`user_2.jpg`... y descargarse el rostro de todo el centro sin tener cuenta. Se
comprobo pidiendolas sin cookie: respondian 200.

Ahora viven fuera de `static/`, en la carpeta de instancia, y solo se entregan
por una vista que comprueba quien pregunta. La fotografia del rostro usada para
identificar a alguien es dato personal (Ley 1581 de 2012): dejarla accesible sin
control incumple el deber de seguridad del articulo 17.
"""
import os
import shutil

from flask import current_app

# Nombre de la carpeta dentro de instance/. Se puede mover con CARPETA_FOTOS
# para apuntarla a un volumen distinto en el servidor.
SUBCARPETA = 'fotos_perfil'

# De donde se traen las fotos que quedaron de la version anterior.
_CARPETA_ANTIGUA = ('static', 'uploads', 'profiles')

_migracion_hecha = False


def carpeta_fotos():
    """Ruta absoluta de la carpeta de fotos, creandola si no existe."""
    configurada = current_app.config.get('CARPETA_FOTOS')
    carpeta = configurada or os.path.join(current_app.instance_path, SUBCARPETA)
    os.makedirs(carpeta, exist_ok=True)
    _mover_las_antiguas(carpeta)
    return carpeta


def _mover_las_antiguas(destino):
    """Traslada las fotos que quedaron en la carpeta publica.

    Se hace aqui y no en un script aparte porque el despliegue es automatico:
    nadie va a entrar al servidor a ejecutar una migracion, y mientras las fotos
    sigan bajo `static/` continuan descargandose sin sesion. Solo se intenta una
    vez por proceso y no interrumpe el arranque si falla.
    """
    global _migracion_hecha
    if _migracion_hecha:
        return
    _migracion_hecha = True

    origen = os.path.join(current_app.root_path, *_CARPETA_ANTIGUA)
    if not os.path.isdir(origen):
        return

    movidas = 0
    for nombre in os.listdir(origen):
        if nombre.startswith('.'):
            continue
        ruta_origen = os.path.join(origen, nombre)
        if not os.path.isfile(ruta_origen):
            continue
        try:
            ruta_destino = os.path.join(destino, nombre)
            if os.path.exists(ruta_destino):
                os.remove(ruta_origen)
            else:
                shutil.move(ruta_origen, ruta_destino)
            movidas += 1
        except OSError as error:
            current_app.logger.error(
                "No se pudo mover la foto %s fuera de static/: %s", nombre, error)

    if movidas:
        current_app.logger.warning(
            "%s fotos movidas fuera de static/. Hasta ahora eran descargables "
            "sin iniciar sesion.", movidas)


def ruta_de_foto(nombre_archivo):
    """Ruta absoluta de una foto concreta, o None si no existe."""
    if not nombre_archivo:
        return None
    # El nombre lo genera el sistema, pero llega desde la base de datos: si
    # alguna vez se colara un '..', apuntaria fuera de la carpeta.
    seguro = os.path.basename(nombre_archivo)
    ruta = os.path.join(carpeta_fotos(), seguro)
    return ruta if os.path.isfile(ruta) else None


def url_de_foto(usuario_id, nombre_foto, cargo):
    """Direccion desde la que mostrar la imagen de alguien.

    Si tiene foto, apunta a la vista con sesion; si no, al avatar de su cargo,
    que si es un archivo estatico normal (es un dibujo, no una persona).
    """
    from flask import url_for
    from app.models.usuarios import avatar_de_cargo

    if usuario_id and nombre_foto and ruta_de_foto(nombre_foto):
        return url_for('usuarios.foto_perfil', usuario_id=usuario_id)
    return url_for('static', filename=avatar_de_cargo(cargo))


def puede_ver_la_foto(espectador, usuario_id):
    """Decide si `espectador` puede ver la foto de `usuario_id`.

    La foto existe para que en la porteria se compruebe que quien entra es
    quien dice ser, y para que quien revisa la cola decida si la imagen sirve.
    Fuera de eso, cada quien ve la suya.
    """
    if not espectador or not espectador.is_authenticated:
        return False
    if espectador.id == usuario_id:
        return True
    return bool(
        espectador.es_admin
        or espectador.puede_operar_porteria
        or espectador.puede_asesorar
        # El instructor ve la foto junto al historial y al pasar asistencia.
        or espectador.puede_gestionar_asistencia
    )
