"""Quien puede ver la foto de rostro de quien.

Las fotos vivian bajo static/, donde Flask las servia sin pedir sesion, con
nombres consecutivos (user_1.jpg, user_2.jpg...). Se comprobo pidiendolas sin
cookie: respondian 200. Cualquiera desde internet podia recorrer los ids y
llevarse el rostro de todo el centro.

Estas pruebas existen para que eso no vuelva a pasar en silencio: el arreglo
no tenia ninguna, asi que un cambio futuro podia deshacerlo sin que nada
fallara. La fotografia del rostro usada para identificar es dato personal
(Ley 1581 de 2012, art. 17).
"""
import os

import pytest

from app.utils.fotos import carpeta_fotos, puede_ver_la_foto


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login', data={
        'identificador': usuario.correo,
        'password': contrasena,
    }, follow_redirects=True)


@pytest.fixture
def con_foto(app, crear_usuario):
    """Un aprendiz con una foto real en disco."""
    from app import db
    usuario = crear_usuario()
    destino = os.path.join(carpeta_fotos(), f'user_{usuario.id}.jpg')
    with open(destino, 'wb') as archivo:
        archivo.write(b'\xff\xd8\xff\xe0 contenido de prueba')
    usuario.foto = f'user_{usuario.id}.jpg'
    db.session.commit()
    yield usuario
    if os.path.isfile(destino):
        os.remove(destino)


class TestSinSesion:
    def test_la_carpeta_publica_ya_no_sirve_fotos(self, client):
        # El fallo original, tal cual: pedirla por static sin cookie.
        respuesta = client.get('/static/uploads/profiles/user_1.jpg')
        assert respuesta.status_code != 200

    def test_la_vista_de_fotos_exige_sesion(self, client, con_foto):
        respuesta = client.get(f'/usuarios/foto/{con_foto.id}')
        assert respuesta.status_code in (302, 401)
        if respuesta.status_code == 302:
            assert '/auth/login' in respuesta.headers['Location']

    def test_no_confirma_si_la_persona_existe(self, client):
        # Un 403 para el id que existe y un 404 para el que no permitiria
        # averiguar quien tiene cuenta. Las dos respuestas deben ser iguales.
        existente = client.get('/usuarios/foto/1')
        inventado = client.get('/usuarios/foto/999999')
        assert existente.status_code == inventado.status_code


class TestConSesion:
    def test_cada_quien_ve_la_suya(self, client, con_foto):
        _entrar(client, con_foto)
        respuesta = client.get(f'/usuarios/foto/{con_foto.id}')
        assert respuesta.status_code == 200
        assert respuesta.mimetype == 'image/jpeg'

    def test_un_aprendiz_no_ve_la_de_otro(self, client, con_foto, crear_usuario):
        otro_id = crear_usuario(correo='otra@sena.edu.co',
                                documento='1122334455').id
        _entrar(client, con_foto)
        respuesta = client.get(f'/usuarios/foto/{otro_id}')
        assert respuesta.status_code == 404


class TestReglaDePermiso:
    """La regla en si, sin pasar por HTTP."""

    class _Espectador:
        is_authenticated = True

        def __init__(self, **atributos):
            self.id = atributos.pop('id', 1)
            for nombre in ('es_admin', 'puede_operar_porteria',
                           'puede_asesorar', 'puede_gestionar_asistencia'):
                setattr(self, nombre, atributos.get(nombre, False))

    def test_nadie_sin_autenticar(self):
        assert puede_ver_la_foto(None, 1) is False

    def test_uno_mismo_si(self):
        assert puede_ver_la_foto(self._Espectador(id=7), 7) is True

    def test_un_aprendiz_no_ve_la_de_otro(self):
        assert puede_ver_la_foto(self._Espectador(id=7), 8) is False

    @pytest.mark.parametrize('permiso', [
        'es_admin', 'puede_operar_porteria', 'puede_asesorar',
        'puede_gestionar_asistencia',
    ])
    def test_quien_la_necesita_por_su_funcion_si(self, permiso):
        # Porteria compara la cara en la puerta, quien asesora revisa la cola,
        # y el instructor la ve junto al historial.
        espectador = self._Espectador(id=7, **{permiso: True})
        assert puede_ver_la_foto(espectador, 8) is True
