"""Pruebas de permisos de los reportes agregados: analitica por rol,
historial de clases, y que la exportacion del panel neutralice formulas.

Nada de esto tenia pruebas: la analitica y el historial de clases solo se
habian probado a mano, y la neutralizacion de formulas del CSV (que existe
en el codigo, senal de que el problema paso) no tenia ninguna prueba que la
sostuviera.
"""
import csv
import io

from app.models.accesos import Acceso, Auditoria

# export_dashboard exige un rango de fechas (inicio y fin) para no volcar
# todo el historico de un clic; estas fechas cubren cualquier Acceso que
# las pruebas creen con la fecha por defecto (hoy).
_RANGO_HOY = {'fecha_inicio': '2020-01-01', 'fecha_fin': '2035-01-01'}


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


class TestPermisosAnalytics:
    def test_aprendiz_no_entra_a_analytics(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _entrar(client, aprendiz)

        r = client.get('/porteria/analytics/Aprendiz', follow_redirects=False)
        assert r.status_code == 302
        assert '/porteria/dashboard' in r.headers['Location']

    def test_celador_entra_a_analytics(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)

        r = client.get('/porteria/analytics/Aprendiz')
        assert r.status_code == 200

    def test_admin_entra_a_analytics(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', cargo='Administrador',
                              rol='Admin', documento='111111')
        _entrar(client, admin)

        r = client.get('/porteria/analytics/Instructor')
        assert r.status_code == 200

    def test_no_autenticado_no_entra_a_analytics(self, client):
        r = client.get('/porteria/analytics/Aprendiz', follow_redirects=False)
        assert r.status_code in (302, 401)


class TestPermisosHistorialClases:
    def test_aprendiz_no_entra(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _entrar(client, aprendiz)

        r = client.get('/porteria/historial_clases', follow_redirects=False)
        assert r.status_code == 302
        assert '/usuarios/profile' in r.headers['Location']

    def test_celador_no_entra(self, client, crear_usuario):
        # Esta vista es solo para administradores: ni siquiera el celador
        # que si puede operar porteria debe verla.
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)

        r = client.get('/porteria/historial_clases', follow_redirects=False)
        assert r.status_code == 302
        assert '/usuarios/profile' in r.headers['Location']

    def test_admin_entra(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', cargo='Administrador',
                              rol='Admin', documento='111111')
        _entrar(client, admin)

        r = client.get('/porteria/historial_clases')
        assert r.status_code == 200

    def test_admin_busca_por_ficha(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', cargo='Administrador',
                              rol='Admin', documento='111111')
        _entrar(client, admin)

        r = client.post('/porteria/historial_clases', data={'ficha': '999999'})
        assert r.status_code == 200


class TestExportacionCsvPermisos:
    def test_aprendiz_no_exporta(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _entrar(client, aprendiz)

        r = client.get('/porteria/export_dashboard', follow_redirects=False)
        assert r.status_code == 302
        assert '/usuarios/profile' in r.headers['Location']

    def test_celador_exporta(self, client, crear_usuario, db):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123', nombre='Juan Perez')
        db.session.add(Acceso(punto_id=1, referencia_id=aprendiz.id,
                              tipo_referencia='Usuario', tipo='Entrada',
                              operador_id=celador.id))
        db.session.commit()
        _entrar(client, celador)

        r = client.get('/porteria/export_dashboard', query_string=_RANGO_HOY)
        assert r.status_code == 200
        assert r.mimetype == 'text/csv'
        assert 'Juan Perez' in r.get_data(as_text=True)

    def test_sin_rango_de_fechas_no_exporta(self, client, crear_usuario):
        # Sin fechas obligatorias, un clic volcaba todo el historico de una
        # vez (documento, nombre, programa, ficha) fuera del sistema.
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)

        r = client.get('/porteria/export_dashboard', follow_redirects=False)
        assert r.status_code == 302
        assert '/porteria/dashboard' in r.headers['Location']

    def test_rango_invertido_no_exporta(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)

        r = client.get('/porteria/export_dashboard', query_string={
            'fecha_inicio': '2026-01-31', 'fecha_fin': '2026-01-01',
        }, follow_redirects=False)
        assert r.status_code == 302
        assert '/porteria/dashboard' in r.headers['Location']

    def test_exportar_deja_constancia_en_auditoria(self, client, crear_usuario, db):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123', nombre='Juan Perez')
        db.session.add(Acceso(punto_id=1, referencia_id=aprendiz.id,
                              tipo_referencia='Usuario', tipo='Entrada',
                              operador_id=celador.id))
        db.session.commit()
        _entrar(client, celador)

        client.get('/porteria/export_dashboard', query_string=_RANGO_HOY)

        registro = Auditoria.query.filter_by(
            accion='Exportación de histórico de accesos').first()
        assert registro is not None
        assert registro.usuario_id == celador.id


class TestExportacionCsvNeutralizaFormulas:
    """El propio codigo (_celda_segura) dice que un aprendiz podia ejecutar
    codigo en el equipo del administrador que abriera el reporte, mediante
    un nombre que empezara con =, +, -, @ o tabulador. Nada verificaba que
    la proteccion siguiera funcionando.
    """

    def _fila_de(self, contenido_csv, documento):
        contenido_csv = contenido_csv.lstrip('﻿')
        lector = csv.reader(io.StringIO(contenido_csv), delimiter=';')
        filas = list(lector)
        for fila in filas[1:]:
            if fila and fila[0] == documento:
                return fila
        return None

    def test_nombre_con_formula_se_neutraliza(self, client, crear_usuario, db):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        atacante = crear_usuario(
            correo='atacante@sena.edu.co', cargo='Aprendiz', documento='666666',
            nombre='=cmd|\'/c calc\'!A1')
        db.session.add(Acceso(punto_id=1, referencia_id=atacante.id,
                              tipo_referencia='Usuario', tipo='Entrada',
                              operador_id=celador.id))
        db.session.commit()
        _entrar(client, celador)

        r = client.get('/porteria/export_dashboard', query_string=_RANGO_HOY)
        contenido = r.get_data(as_text=True)
        fila = self._fila_de(contenido, '666666')
        assert fila is not None
        nombre_celda = fila[1]
        assert nombre_celda.startswith("'"), (
            f'la celda de nombre debia neutralizar la formula, quedo: {nombre_celda!r}')
        assert not nombre_celda.startswith('=')

    def test_documento_con_formula_se_neutraliza(self, client, crear_usuario, db):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        atacante = crear_usuario(
            correo='atacante2@sena.edu.co', cargo='Aprendiz', documento='+666666',
            nombre='Ataque por documento')
        db.session.add(Acceso(punto_id=1, referencia_id=atacante.id,
                              tipo_referencia='Usuario', tipo='Entrada',
                              operador_id=celador.id))
        db.session.commit()
        _entrar(client, celador)

        r = client.get('/porteria/export_dashboard', query_string=_RANGO_HOY)
        contenido = r.get_data(as_text=True).lstrip('﻿')
        lector = csv.reader(io.StringIO(contenido), delimiter=';')
        filas = list(lector)
        fila = next((f for f in filas[1:] if f and 'Ataque por documento' in f[1]), None)
        assert fila is not None
        assert fila[0].startswith("'")

    def test_nombre_normal_no_se_toca(self, client, crear_usuario, db):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        normal = crear_usuario(correo='normal@sena.edu.co', cargo='Aprendiz',
                               documento='222222', nombre='Ana Torres')
        db.session.add(Acceso(punto_id=1, referencia_id=normal.id,
                              tipo_referencia='Usuario', tipo='Entrada',
                              operador_id=celador.id))
        db.session.commit()
        _entrar(client, celador)

        r = client.get('/porteria/export_dashboard', query_string=_RANGO_HOY)
        contenido = r.get_data(as_text=True)
        fila = self._fila_de(contenido, '222222')
        assert fila is not None
        assert fila[1] == 'Ana Torres'
