"""Pruebas de las fichas de formación y de lo que el aprendiz hereda de ellas.

La ficha existe para que el programa y la fecha de finalización se registren
una sola vez y todos los aprendices de esa ficha salgan con lo mismo impreso.
Si la herencia se rompe, cada carnet vuelve a decir una cosa distinta y nadie
se entera hasta que alguien compara dos carnets a mano.
"""
from datetime import date

import pytest

from app.models.fichas import Ficha


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


@pytest.fixture
def ficha(db):
    registro = Ficha(numero='2847513',
                     programa='Análisis y Desarrollo de Software',
                     fecha_finalizacion=date(2027, 6, 30))
    db.session.add(registro)
    db.session.commit()
    return registro


class TestHerenciaDesdeLaFicha:
    def test_el_aprendiz_hereda_programa_y_fecha(self, crear_usuario, ficha, db):
        persona = crear_usuario(cargo='Aprendiz', documento='1010')
        persona.ficha_id = ficha.id
        db.session.commit()

        assert persona.programa_carnet == 'Análisis y Desarrollo de Software'
        assert persona.fecha_finalizacion_carnet == '30/06/2027'
        assert persona.ficha_numero == '2847513'

    def test_cambiar_la_ficha_cambia_el_carnet_de_todos_sus_aprendices(
            self, crear_usuario, ficha, db):
        una = crear_usuario(correo='a@sena.edu.co', cargo='Aprendiz', documento='1')
        otra = crear_usuario(correo='b@sena.edu.co', cargo='Aprendiz', documento='2')
        una.ficha_id = otra.ficha_id = ficha.id
        db.session.commit()

        ficha.fecha_finalizacion = date(2028, 1, 15)
        db.session.commit()

        assert una.fecha_finalizacion_carnet == '15/01/2028'
        assert otra.fecha_finalizacion_carnet == '15/01/2028'

    def test_sin_ficha_enlazada_se_usa_el_texto_historico(self, crear_usuario, db):
        """Quien tenía la ficha escrita a mano no debe quedarse sin carnet."""
        persona = crear_usuario(cargo='Aprendiz', documento='1010',
                                ficha='2999999', programa='Sistemas')
        assert persona.ficha_numero == '2999999'
        assert persona.programa_carnet == 'Sistemas'
        # La fecha sí queda vacía: nunca existió un campo donde guardarla.
        assert persona.fecha_finalizacion_carnet == ''

    def test_una_ficha_sin_fecha_no_revienta(self, crear_usuario, db):
        sin_fecha = Ficha(numero='111222', programa='Contabilidad')
        db.session.add(sin_fecha)
        db.session.commit()
        persona = crear_usuario(cargo='Aprendiz', documento='1010')
        persona.ficha_id = sin_fecha.id
        db.session.commit()
        assert persona.fecha_finalizacion_carnet == ''


class TestElAprendizEligeFichaEnSuPerfil:
    def test_al_elegir_ficha_se_copian_numero_y_programa(self, client,
                                                         crear_usuario, ficha, db):
        persona = crear_usuario(cargo='Aprendiz', documento='1010')
        _entrar(client, persona)
        client.post('/usuarios/update_profile',
                    data={'ficha_id': str(ficha.id)},
                    headers={'X-Requested-With': 'XMLHttpRequest'})
        db.session.refresh(persona)

        assert persona.ficha_id == ficha.id
        # El número se copia a la columna de texto para no romper los reportes
        # que ya filtran por ella.
        assert persona.ficha == '2847513'
        assert persona.programa == 'Análisis y Desarrollo de Software'

    def test_una_ficha_inexistente_se_rechaza(self, client, crear_usuario, db):
        persona = crear_usuario(cargo='Aprendiz', documento='1010')
        _entrar(client, persona)
        r = client.post('/usuarios/update_profile',
                        data={'ficha_id': '99999'},
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400
        db.session.refresh(persona)
        assert persona.ficha_id is None

    def test_el_aprendiz_no_puede_escribir_su_programa(self, client,
                                                       crear_usuario, ficha, db):
        """El programa viene de la ficha; enviarlo a mano no debe pisarlo."""
        persona = crear_usuario(cargo='Aprendiz', documento='1010')
        _entrar(client, persona)
        client.post('/usuarios/update_profile',
                    data={'ficha_id': str(ficha.id), 'programa': 'Otra Cosa'},
                    headers={'X-Requested-With': 'XMLHttpRequest'})
        db.session.refresh(persona)
        assert persona.programa == 'Análisis y Desarrollo de Software'


class TestPermisosDeLaPantallaDeFichas:
    """Quien edita una ficha cambia el carnet de todos sus aprendices, así que
    la pantalla es solo para administradores."""

    def test_un_admin_entra(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='900')
        _entrar(client, admin)
        assert client.get('/usuarios/admin/fichas').status_code == 200

    @pytest.mark.parametrize('cargo', ['Aprendiz', 'Instructor', 'Celador',
                                       'Administrativo', 'Administrador'])
    def test_quien_no_es_admin_no_entra(self, client, crear_usuario, cargo):
        persona = crear_usuario(correo=f'{cargo}@sena.edu.co', rol='Usuario',
                                cargo=cargo, documento=f'77{len(cargo)}')
        _entrar(client, persona)
        r = client.get('/usuarios/admin/fichas')
        assert r.status_code == 302, f'{cargo} no debería ver las fichas'

    def test_sin_sesion_redirige_al_login(self, client):
        r = client.get('/usuarios/admin/fichas')
        assert r.status_code == 302
        assert '/auth/login' in r.headers['Location']

    @pytest.mark.parametrize('ruta,metodo', [
        ('/usuarios/admin/fichas/crear', 'post'),
        ('/usuarios/admin/fichas/1/editar', 'post'),
        ('/usuarios/admin/fichas/1/archivar', 'post'),
    ])
    def test_las_acciones_de_escritura_tambien_exigen_admin(
            self, client, crear_usuario, ruta, metodo):
        persona = crear_usuario(cargo='Aprendiz', documento='1010')
        _entrar(client, persona)
        r = getattr(client, metodo)(ruta, data={'numero': '1234',
                                                'programa': 'Cualquiera'})
        assert r.status_code == 302
        db_sigue_vacia = Ficha.query.filter_by(numero='1234').first() is None
        assert db_sigue_vacia


class TestGestionDeFichas:
    def test_crear_editar_y_archivar(self, client, crear_usuario, db):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='900')
        _entrar(client, admin)

        client.post('/usuarios/admin/fichas/crear',
                    data={'numero': '3141592', 'programa': 'Cocina',
                          'fecha_finalizacion': '2027-12-01'})
        creada = Ficha.query.filter_by(numero='3141592').first()
        assert creada is not None
        assert creada.fecha_finalizacion == date(2027, 12, 1)
        assert creada.activa is True

        client.post(f'/usuarios/admin/fichas/{creada.id}/editar',
                    data={'numero': '3141592', 'programa': 'Gastronomía',
                          'fecha_finalizacion': '2028-03-15'})
        db.session.refresh(creada)
        assert creada.programa == 'Gastronomía'
        assert creada.fecha_finalizacion == date(2028, 3, 15)

        client.post(f'/usuarios/admin/fichas/{creada.id}/archivar')
        db.session.refresh(creada)
        assert creada.activa is False

    def test_no_se_admiten_numeros_de_ficha_invalidos(self, client,
                                                      crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='900')
        _entrar(client, admin)
        for numero in ('abc', '12', '', '12345678901234'):
            client.post('/usuarios/admin/fichas/crear',
                        data={'numero': numero, 'programa': 'Cocina'})
        assert Ficha.query.count() == 0

    def test_no_se_repite_el_numero_de_ficha(self, client, crear_usuario, ficha):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='900')
        _entrar(client, admin)
        client.post('/usuarios/admin/fichas/crear',
                    data={'numero': '2847513', 'programa': 'Duplicada'})
        assert Ficha.query.filter_by(numero='2847513').count() == 1

    def test_una_fecha_invalida_no_crea_la_ficha(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='900')
        _entrar(client, admin)
        client.post('/usuarios/admin/fichas/crear',
                    data={'numero': '4567890', 'programa': 'Cocina',
                          'fecha_finalizacion': '31/12/2027'})
        assert Ficha.query.filter_by(numero='4567890').first() is None

    def test_archivar_no_borra_la_ficha_de_sus_aprendices(self, client,
                                                          crear_usuario,
                                                          ficha, db):
        aprendiz = crear_usuario(cargo='Aprendiz', documento='1010')
        aprendiz.ficha_id = ficha.id
        db.session.commit()

        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='900')
        _entrar(client, admin)
        client.post(f'/usuarios/admin/fichas/{ficha.id}/archivar')

        db.session.refresh(aprendiz)
        assert aprendiz.ficha_id == ficha.id
        assert aprendiz.programa_carnet == 'Análisis y Desarrollo de Software'


class TestAltaDesdeAdministracion:
    """El administrador y la importación masiva pasan la ficha como texto.
    Si ese número ya está registrado, el aprendiz debe heredar de una vez."""

    def test_al_crear_usuario_se_enlaza_la_ficha_existente(self, client,
                                                           crear_usuario, ficha,
                                                           db):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='900')
        _entrar(client, admin)
        rol_usuario = admin.rol.query.filter_by(nombre='Usuario').first()
        client.post('/usuarios/api/admin/crear_usuario', json={
            'nombre': 'Nueva Aprendiz', 'correo': 'nueva@sena.edu.co',
            'contraseña': 'ClaveLarga2026', 'rol_id': rol_usuario.id,
            'cargo': 'Aprendiz', 'documento': '404040', 'ficha': '2847513',
        })
        from app.models.usuarios import Usuario
        nueva = Usuario.query.filter_by(correo='nueva@sena.edu.co').first()
        assert nueva is not None
        assert nueva.ficha_id == ficha.id
        assert nueva.programa_carnet == 'Análisis y Desarrollo de Software'
        assert nueva.fecha_finalizacion_carnet == '30/06/2027'

    def test_una_ficha_no_registrada_no_se_inventa(self, crear_usuario, db):
        """Inventar un programa a partir de un número suelto sería peor que
        dejar el carnet sin fecha."""
        persona = crear_usuario(cargo='Aprendiz', documento='1010')
        assert Ficha.enlazar_por_numero(persona, '8888888') is None
        assert persona.ficha_id is None
        assert Ficha.query.filter_by(numero='8888888').first() is None
