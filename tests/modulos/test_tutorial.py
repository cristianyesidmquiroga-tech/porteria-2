"""Pruebas del tutorial de primer ingreso.

El tutorial existe para que quien entra por primera vez sepa que el QR no se
activa solo: debe verse una unica vez por persona, poder releerse en texto, y
su boton de acceso solo debe aparecer mientras el perfil siga incompleto.
"""
from app.models.usuarios import Usuario


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


class TestMarcarComoVisto:
    def test_se_marca_el_tutorial_como_visto(self, client, crear_usuario, db):
        persona = crear_usuario(correo='ana@sena.edu.co')
        assert persona.tutorial_visto is not True

        _entrar(client, persona)
        r = client.post('/usuarios/tutorial/completar')

        assert r.status_code == 200
        assert r.get_json()['status'] == 'success'
        assert db.session.get(Usuario, persona.id).tutorial_visto is True

    def test_marcarlo_dos_veces_no_falla(self, client, crear_usuario, db):
        persona = crear_usuario(correo='ana@sena.edu.co')
        _entrar(client, persona)
        client.post('/usuarios/tutorial/completar')
        r = client.post('/usuarios/tutorial/completar')
        assert r.status_code == 200
        assert db.session.get(Usuario, persona.id).tutorial_visto is True

    def test_sin_sesion_no_se_puede_marcar(self, client):
        r = client.post('/usuarios/tutorial/completar')
        # @login_required redirige al login en vez de ejecutar nada.
        assert r.status_code in (302, 401)

    def test_no_se_puede_marcar_el_de_otra_persona(self, client, crear_usuario, db):
        """El endpoint opera sobre current_user: un id ajeno en el cuerpo se
        ignora y el tutorial de la otra persona queda intacto."""
        ana = crear_usuario(correo='ana@sena.edu.co', documento='111')
        beto = crear_usuario(correo='beto@sena.edu.co', documento='222')

        _entrar(client, beto)
        client.post('/usuarios/tutorial/completar',
                    data={'usuario_id': ana.id, 'id': ana.id})

        assert db.session.get(Usuario, ana.id).tutorial_visto is not True
        assert db.session.get(Usuario, beto.id).tutorial_visto is True


class TestVersionEnTexto:
    def test_la_pagina_del_tutorial_carga(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co')
        _entrar(client, persona)
        r = client.get('/usuarios/tutorial')
        cuerpo = r.get_data(as_text=True)

        assert r.status_code == 200
        # Los pasos clave del flujo deben estar explicados con su ejemplo.
        assert 'Completa tu información personal' in cuerpo
        assert 'Sube tu foto de perfil' in cuerpo
        assert 'aprobación de un asesor' in cuerpo
        assert 'Ejemplo:' in cuerpo

    def test_sin_sesion_redirige_al_login(self, client):
        r = client.get('/usuarios/tutorial')
        assert r.status_code in (302, 401)

    def test_ofrece_relanzar_el_recorrido_guiado(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co')
        _entrar(client, persona)
        cuerpo = client.get('/usuarios/tutorial').get_data(as_text=True)
        # El enlace fuerza el recorrido aunque ya se haya visto (?tutorial=1).
        assert 'tutorial=1' in cuerpo


class TestBotonDeAcceso:
    """El boton "Ver tutorial de primeros pasos" vive en el aviso de perfil
    incompleto: aparece mientras falte informacion y desaparece al completarla."""

    def test_aparece_con_el_perfil_incompleto(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', perfil_completo=False)
        _entrar(client, persona)
        cuerpo = client.get('/usuarios/profile').get_data(as_text=True)
        assert 'Ver tutorial de primeros pasos' in cuerpo

    def test_desaparece_con_el_perfil_completo(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', perfil_completo=True)
        _entrar(client, persona)
        cuerpo = client.get('/usuarios/profile').get_data(as_text=True)
        assert 'Ver tutorial de primeros pasos' not in cuerpo


class TestRecorridoGuiado:
    """El guion interactivo se carga en toda pagina autenticada, con el estado
    de tutorial_visto en sus data-*, que es lo que decide si se autolanza."""

    def test_el_script_indica_que_no_se_ha_visto(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co')
        _entrar(client, persona)
        cuerpo = client.get('/usuarios/profile').get_data(as_text=True)
        assert 'js/tutorial.js' in cuerpo
        assert 'data-tutorial-visto="false"' in cuerpo
        assert 'data-en-perfil="true"' in cuerpo

    def test_el_script_indica_que_ya_se_vio(self, client, crear_usuario, db):
        persona = crear_usuario(correo='ana@sena.edu.co')
        persona.tutorial_visto = True
        db.session.commit()
        _entrar(client, persona)
        cuerpo = client.get('/usuarios/profile').get_data(as_text=True)
        assert 'data-tutorial-visto="true"' in cuerpo
