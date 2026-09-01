"""Pruebas del escaneo en la puerta: lo que usa el celador con la gente
esperando. Cubre la verificacion por documento (la version de datos para el
escaner JS y la version de pagina), quien puede llamarla, y el reporte de
incidentes. Nada de esto tenia pruebas.
"""
from app.models.accesos import Auditoria


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


class TestApiVerifyDocumentoValido:
    def test_documento_valido_devuelve_datos_del_usuario(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123', nombre='Juan Perez')
        _entrar(client, celador)

        r = client.get(f'/porteria/api/verify/{aprendiz.documento}')
        assert r.status_code == 200
        data = r.get_json()
        assert data['found'] is True
        assert data['id'] == aprendiz.id
        assert data['nombre'] == 'Juan Perez'
        assert data['documento'] == '123123'
        assert data['tipo'] == 'Usuario'
        assert data['status'] == 'Afuera'

    def test_documento_inexistente_no_se_encuentra(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)

        r = client.get('/porteria/api/verify/999999999')
        assert r.status_code == 200
        data = r.get_json()
        assert data == {'found': False}

    def test_documento_de_perfil_incompleto_se_puede_verificar(self, client, crear_usuario):
        # El celador debe poder ver a alguien con el perfil incompleto: es
        # precisamente el caso en el que necesita informacion clara en el
        # escaner, no un 404 silencioso.
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        incompleto = crear_usuario(correo='incompleto@sena.edu.co', cargo='Aprendiz',
                                   documento='555555', perfil_completo=False)
        _entrar(client, celador)

        r = client.get(f'/porteria/api/verify/{incompleto.documento}')
        assert r.status_code == 200
        data = r.get_json()
        assert data['found'] is True
        assert data['id'] == incompleto.id

    def test_foto_no_aprobada_se_marca_explicitamente(self, client, crear_usuario):
        # foto_estado por defecto es 'sin_foto': foto_aprobada debe llegar en
        # False para que el celador sepa que esa foto no sirve para
        # confirmar identidad.
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        sin_foto = crear_usuario(correo='sinfoto@sena.edu.co', cargo='Aprendiz',
                                 documento='444444')
        _entrar(client, celador)

        r = client.get(f'/porteria/api/verify/{sin_foto.documento}')
        data = r.get_json()
        assert data['foto_aprobada'] is False

    def test_foto_aprobada_se_marca_true(self, client, crear_usuario, db):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        aprobado = crear_usuario(correo='aprobado@sena.edu.co', cargo='Aprendiz',
                                 documento='333333')
        aprobado.foto_estado = 'aprobada'
        db.session.commit()
        _entrar(client, celador)

        r = client.get(f'/porteria/api/verify/{aprobado.documento}')
        data = r.get_json()
        assert data['foto_aprobada'] is True


class TestVerifyPagina:
    """La version /verify/<doc> renderiza una pagina en vez de JSON."""

    def test_documento_valido_muestra_perfil(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123', nombre='Juan Perez')
        _entrar(client, celador)

        r = client.get(f'/porteria/verify/{aprendiz.documento}')
        assert r.status_code == 200
        assert b'Juan Perez' in r.data

    def test_documento_inexistente_redirige_con_aviso(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)

        r = client.get('/porteria/verify/999999999', follow_redirects=False)
        assert r.status_code == 302
        assert '/porteria/scanner' in r.headers['Location']

    def test_perfil_incompleto_se_puede_ver(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        incompleto = crear_usuario(correo='incompleto@sena.edu.co', cargo='Aprendiz',
                                   documento='555555', perfil_completo=False,
                                   nombre='Perfil Incompleto')
        _entrar(client, celador)

        r = client.get(f'/porteria/verify/{incompleto.documento}')
        assert r.status_code == 200
        assert b'Perfil Incompleto' in r.data

    def test_foto_no_aprobada_no_impide_ver_la_pagina(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        sin_foto = crear_usuario(correo='sinfoto@sena.edu.co', cargo='Aprendiz',
                                 documento='444444', nombre='Sin Foto Aun')
        _entrar(client, celador)

        r = client.get(f'/porteria/verify/{sin_foto.documento}')
        assert r.status_code == 200
        assert b'Sin Foto Aun' in r.data


class TestPermisoDeConsulta:
    """Un aprendiz no debe poder consultar el documento de otro por aqui."""

    def test_aprendiz_no_consulta_api_verify(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123')
        otro = crear_usuario(correo='otro@sena.edu.co', cargo='Aprendiz',
                             documento='456456')
        _entrar(client, aprendiz)

        r = client.get(f'/porteria/api/verify/{otro.documento}')
        assert r.status_code == 403
        assert b'456456' not in r.data

    def test_aprendiz_no_consulta_verify_pagina(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123')
        otro = crear_usuario(correo='otro@sena.edu.co', cargo='Aprendiz',
                             documento='456456', nombre='Datos Ajenos')
        _entrar(client, aprendiz)

        r = client.get(f'/porteria/verify/{otro.documento}', follow_redirects=False)
        assert r.status_code == 302
        assert '/usuarios/profile' in r.headers['Location']
        # Y de verdad no se filtran datos del otro usuario en el cuerpo.
        assert b'Datos Ajenos' not in r.data

    def test_no_autenticado_no_consulta(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123')
        r = client.get(f'/porteria/api/verify/{aprendiz.documento}',
                       follow_redirects=False)
        assert r.status_code in (302, 401)


class TestReporteDeIncidentes:
    def test_celador_registra_incidente(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123')
        _entrar(client, celador)

        r = client.post('/porteria/register_incidente', data={
            'entidad_id': str(aprendiz.id),
            'tipo_entidad': 'Usuario',
            'detalles': 'Documento fisico no coincide con la foto del carnet.',
        }, follow_redirects=False)
        assert r.status_code == 302

        incidente = Auditoria.query.filter_by(
            accion='Incidente Registrado por Celador').first()
        assert incidente is not None
        assert incidente.usuario_id == celador.id
        assert incidente.registro_id == aprendiz.id
        assert 'no coincide' in incidente.detalles

    def test_incidente_sin_detalles_no_se_registra(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)

        r = client.post('/porteria/register_incidente', data={
            'entidad_id': '1',
            'tipo_entidad': 'Usuario',
        }, follow_redirects=False)
        assert r.status_code == 302
        assert Auditoria.query.filter_by(
            accion='Incidente Registrado por Celador').count() == 0

    def test_aprendiz_no_registra_incidente(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123')
        _entrar(client, aprendiz)

        r = client.post('/porteria/register_incidente', data={
            'entidad_id': '1',
            'tipo_entidad': 'Usuario',
            'detalles': 'Intento de un aprendiz.',
        })
        assert r.status_code == 403
        assert Auditoria.query.filter_by(
            accion='Incidente Registrado por Celador').count() == 0

    def test_entidad_id_no_numerico_no_revienta(self, client, crear_usuario):
        # tipo_entidad/entidad_id vienen del formulario del escaner: no hay
        # que confiar en que siempre sean numericos.
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)

        r = client.post('/porteria/register_incidente', data={
            'entidad_id': 'SENA-VISIT:abc',
            'tipo_entidad': 'Visitante',
            'detalles': 'Un visitante sin identificacion clara.',
        }, follow_redirects=False)
        assert r.status_code == 302
        incidente = Auditoria.query.filter_by(
            accion='Incidente Registrado por Celador').first()
        assert incidente is not None
        assert incidente.registro_id == 0
