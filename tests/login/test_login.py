import pytest

from app.models.usuarios import CARGOS_VALIDOS

CONTRASENA = 'Segura2026'

USUARIOS = [
    pytest.param({'rol': 'Admin', 'cargo': 'Administrador',
                  'correo': 'admin@sena.edu.co', 'documento': '1000000001',
                  'nombre': 'Admin de Prueba'},
                 id='Admin'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Administrador',
                  'correo': 'administrador@sena.edu.co', 'documento': '1000000002',
                  'nombre': 'Administrador de Prueba'},
                 id='Administrador'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Aprendiz',
                  'correo': 'aprendiz@sena.edu.co', 'documento': '1000000003',
                  'nombre': 'Aprendiz de Prueba'},
                 id='Aprendiz'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Instructor',
                  'correo': 'instructor@sena.edu.co', 'documento': '1000000004',
                  'nombre': 'Instructor de Prueba'},
                 id='Instructor'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Administrativo',
                  'correo': 'administrativo@sena.edu.co', 'documento': '1000000005',
                  'nombre': 'Administrativo de Prueba'},
                 id='Administrativo'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Celador',
                  'correo': 'celador@sena.edu.co', 'documento': '1000000006',
                  'nombre': 'Celador de Prueba'},
                 id='Celador'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Portería',
                  'correo': 'porteria@sena.edu.co', 'documento': '1000000007',
                  'nombre': 'Portería de Prueba'},
                 id='Portería'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Coordinacion',
                  'correo': 'coordinacion@sena.edu.co', 'documento': '1000000008',
                  'nombre': 'Coordinacion de Prueba'},
                 id='Coordinacion'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Subdirector',
                  'correo': 'subdirector@sena.edu.co', 'documento': '1000000009',
                  'nombre': 'Subdirector de Prueba'},
                 id='Subdirector'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Contratista',
                  'correo': 'contratista@sena.edu.co', 'documento': '1000000010',
                  'nombre': 'Contratista de Prueba'},
                 id='Contratista'),
    pytest.param({'rol': 'Usuario', 'cargo': 'Funcionario',
                  'correo': 'funcionario@sena.edu.co', 'documento': '1000000011',
                  'nombre': 'Funcionario de Prueba'},
                 id='Funcionario'),
]


def _login(client, identificador, contrasena, ajax=True):
    headers = {'X-Requested-With': 'XMLHttpRequest'} if ajax else {}
    return client.post('/auth/login',
                       data={'correo': identificador, 'password': contrasena},
                       headers=headers)


def test_cubre_todos_los_cargos():
    cargos = {p.values[0]['cargo'] for p in USUARIOS
              if p.values[0]['rol'] == 'Usuario'}
    assert cargos == set(CARGOS_VALIDOS)


@pytest.mark.parametrize('datos', USUARIOS)
class TestLoginPorUsuario:
    @pytest.fixture
    def nuevo(self, crear_usuario, datos):
        def _crear(**extras):
            return crear_usuario(correo=datos['correo'],
                                 documento=datos['documento'],
                                 nombre=datos['nombre'], rol=datos['rol'],
                                 cargo=datos['cargo'], **extras)
        return _crear

    def test_entra_con_correo(self, client, nuevo, datos):
        nuevo()
        r = _login(client, datos['correo'], CONTRASENA)
        assert r.status_code == 200
        assert r.get_json()['status'] == 'success'

    def test_entra_con_documento(self, client, nuevo, datos):
        nuevo()
        r = _login(client, datos['documento'], CONTRASENA)
        assert r.get_json()['status'] == 'success'

    def test_correo_sin_importar_mayusculas_ni_espacios(self, client, nuevo, datos):
        nuevo()
        r = _login(client, f"  {datos['correo'].upper()} ", CONTRASENA)
        assert r.get_json()['status'] == 'success'

    def test_formulario_sin_ajax_redirige(self, client, nuevo, datos):
        nuevo()
        r = _login(client, datos['correo'], CONTRASENA, ajax=False)
        assert r.status_code == 302

    def test_ya_autenticado_no_vuelve_a_ver_el_login(self, client, nuevo, datos):
        nuevo()
        _login(client, datos['correo'], CONTRASENA)
        assert client.get('/auth/login').status_code == 302

    def test_contrasena_incorrecta_no_entra(self, client, db, nuevo, datos):
        usuario = nuevo()
        r = _login(client, datos['correo'], 'Incorrecta2026')
        assert r.status_code == 401
        db.session.refresh(usuario)
        assert usuario.intentos_fallidos == 1

    def test_bloqueo_tras_cinco_intentos(self, client, db, nuevo, datos):
        usuario = nuevo()
        for _ in range(5):
            _login(client, datos['correo'], 'Incorrecta2026')
        db.session.refresh(usuario)
        assert usuario.bloqueado_hasta is not None
        r = _login(client, datos['correo'], CONTRASENA)
        assert r.status_code == 403
        assert r.get_json()['bloqueado_segundos'] > 0


class TestLoginGeneral:
    def test_no_revela_si_la_cuenta_existe(self, client, crear_usuario):
        crear_usuario(correo='ana@sena.edu.co', contrasena=CONTRASENA)
        existente = _login(client, 'ana@sena.edu.co', 'ContrasenaMala1')
        inexistente = _login(client, 'nadie@sena.edu.co', 'ContrasenaMala1')
        assert existente.get_json()['message'] == inexistente.get_json()['message']
        assert existente.status_code == inexistente.status_code

    def test_el_contador_se_reinicia_al_acertar(self, client, crear_usuario, db):
        usuario = crear_usuario(correo='ana@sena.edu.co', contrasena=CONTRASENA)
        for _ in range(3):
            _login(client, 'ana@sena.edu.co', 'incorrecta1')
        _login(client, 'ana@sena.edu.co', CONTRASENA)
        db.session.refresh(usuario)
        assert usuario.intentos_fallidos == 0

    @pytest.mark.parametrize('identificador,contrasena', [
        ('ana@sena.edu.co', ''),
        ('', CONTRASENA),
        ('', ''),
    ], ids=['sin-contrasena', 'sin-identificador', 'vacio'])
    def test_campos_vacios_no_entran(self, client, crear_usuario,
                                     identificador, contrasena):
        crear_usuario(correo='ana@sena.edu.co', contrasena=CONTRASENA)
        assert _login(client, identificador, contrasena).status_code == 401

    def test_la_pagina_de_login_abre(self, client):
        assert client.get('/auth/login').status_code == 200
