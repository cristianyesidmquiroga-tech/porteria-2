"""Pruebas del historial de ingresos por persona.

Cubren lo que puede romperse en silencio: los permisos a nivel de objeto (un
aprendiz mirando el historial de otro), el emparejado entrada/salida cuando
faltan registros, la contaminacion entre entidades por el referencia_id
polimorfico, y el conteo de dias asistidos/faltados.
"""
from datetime import date, datetime, timedelta

import pytest

from app import db
from app.models.accesos import Acceso
from app.models.entidades import Equipo
from app.routes.porteria.historial_persona import (
    construir_historial,
    dias_esperados,
)

RUTA = '/porteria/historial-persona'
RUTA_API = '/porteria/api/historial-persona'


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


def _acceso(referencia_id, tipo, momento, tipo_referencia='Usuario',
            equipos_str=None):
    db.session.add(Acceso(punto_id=1, referencia_id=referencia_id,
                          tipo_referencia=tipo_referencia, tipo=tipo,
                          fecha=momento, equipos_str=equipos_str))


class TestPermisos:
    def test_aprendiz_ve_su_propio_historial(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _entrar(client, aprendiz)
        respuesta = client.get(f'{RUTA}?usuario_id={aprendiz.id}')
        assert respuesta.status_code == 200

    def test_aprendiz_no_ve_el_historial_de_otro(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        otro = crear_usuario(correo='otro@sena.edu.co', cargo='Aprendiz',
                             documento='999999')
        _entrar(client, aprendiz)
        respuesta = client.get(f'{RUTA}?usuario_id={otro.id}',
                               follow_redirects=False)
        assert respuesta.status_code == 302
        assert '/usuarios/profile' in respuesta.headers['Location']

    def test_api_niega_con_403_el_historial_ajeno(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        otro = crear_usuario(correo='otro@sena.edu.co', cargo='Aprendiz',
                             documento='999999')
        _entrar(client, aprendiz)
        respuesta = client.get(f'{RUTA_API}?usuario_id={otro.id}')
        assert respuesta.status_code == 403

    def test_aprendiz_no_puede_listar_una_ficha_completa(self, client, crear_usuario):
        """Filtrar por ficha no debe ser un rodeo para ver a los demas."""
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 ficha='2758899')
        crear_usuario(correo='otro@sena.edu.co', cargo='Aprendiz',
                      documento='999999', ficha='2758899')
        _entrar(client, aprendiz)
        respuesta = client.get(f'{RUTA_API}?ficha=2758899')
        assert respuesta.status_code == 200
        personas = respuesta.get_json()['personas']
        assert [p['id'] for p in personas] == [aprendiz.id]

    def test_celador_consulta_a_cualquiera(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _entrar(client, celador)
        respuesta = client.get(f'{RUTA_API}?usuario_id={aprendiz.id}')
        assert respuesta.status_code == 200
        assert respuesta.get_json()['personas'][0]['id'] == aprendiz.id

    def test_instructor_consulta_su_ficha(self, client, crear_usuario):
        instructor = crear_usuario(correo='instructor@sena.edu.co',
                                   cargo='Instructor', documento='555555')
        crear_usuario(correo='ap1@sena.edu.co', cargo='Aprendiz',
                      documento='111111', ficha='2758899')
        crear_usuario(correo='ap2@sena.edu.co', cargo='Aprendiz',
                      documento='222222', ficha='2758899')
        _entrar(client, instructor)
        respuesta = client.get(f'{RUTA_API}?ficha=2758899')
        assert respuesta.status_code == 200
        assert len(respuesta.get_json()['personas']) == 2

    def test_anonimo_es_redirigido_al_login(self, client):
        respuesta = client.get(RUTA, follow_redirects=False)
        assert respuesta.status_code == 302
        assert '/auth/login' in respuesta.headers['Location']


class TestEmparejado:
    def test_entrada_y_salida_se_emparejan_con_permanencia(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        _acceso(persona.id, 'Entrada', datetime.combine(dia, datetime.min.time())
                .replace(hour=7))
        _acceso(persona.id, 'Salida', datetime.combine(dia, datetime.min.time())
                .replace(hour=12, minute=30))
        db.session.commit()

        movimientos = construir_historial([persona], dia, dia)[0]['movimientos']
        assert len(movimientos) == 1
        assert movimientos[0]['permanencia_minutos'] == 330
        assert movimientos[0]['salida'].hour == 12

    def test_entrada_sin_salida_queda_abierta(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        _acceso(persona.id, 'Entrada',
                datetime.combine(dia, datetime.min.time()).replace(hour=8))
        db.session.commit()

        bloque = construir_historial([persona], dia, dia)[0]
        assert len(bloque['movimientos']) == 1
        assert bloque['movimientos'][0]['salida'] is None
        assert bloque['movimientos'][0]['permanencia_minutos'] is None
        assert bloque['resumen']['sin_salida'] == 1

    def test_dos_entradas_seguidas_dejan_la_primera_sin_salida(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        base = datetime.combine(dia, datetime.min.time())
        _acceso(persona.id, 'Entrada', base.replace(hour=7))
        _acceso(persona.id, 'Entrada', base.replace(hour=9))
        _acceso(persona.id, 'Salida', base.replace(hour=11))
        db.session.commit()

        movimientos = construir_historial([persona], dia, dia)[0]['movimientos']
        assert len(movimientos) == 2
        assert movimientos[0]['salida'] is None
        assert movimientos[1]['permanencia_minutos'] == 120

    def test_salida_sin_entrada_previa_se_conserva(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        _acceso(persona.id, 'Salida',
                datetime.combine(dia, datetime.min.time()).replace(hour=6))
        db.session.commit()

        movimientos = construir_historial([persona], dia, dia)[0]['movimientos']
        assert len(movimientos) == 1
        assert movimientos[0]['entrada'] is None
        assert movimientos[0]['salida'].hour == 6

    def test_cierre_automatico_de_medianoche_se_marca(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        base = datetime.combine(dia, datetime.min.time())
        _acceso(persona.id, 'Entrada', base.replace(hour=7))
        _acceso(persona.id, 'Salida',
                base.replace(hour=23, minute=59, second=59))
        db.session.commit()

        movimiento = construir_historial([persona], dia, dia)[0]['movimientos'][0]
        assert movimiento['cierre_automatico'] is True

    def test_equipos_se_traducen_a_nombres_y_toleran_borrados(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        portatil = Equipo(nombre='Portatil Lenovo', tipo='Portátil',
                          usuario_id=persona.id)
        db.session.add(portatil)
        db.session.commit()

        dia = date.today()
        _acceso(persona.id, 'Entrada',
                datetime.combine(dia, datetime.min.time()).replace(hour=7),
                equipos_str=f'{portatil.id},9999')
        db.session.commit()

        equipos = construir_historial([persona], dia, dia)[0]['movimientos'][0]['equipos']
        assert 'Portatil Lenovo' in equipos
        assert any('9999' in nombre for nombre in equipos)


class TestAislamientoDeEntidades:
    def test_no_se_mezclan_accesos_de_visitantes(self, app, crear_usuario):
        """referencia_id es polimorfico: el visitante N no es el usuario N."""
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        base = datetime.combine(dia, datetime.min.time())
        _acceso(persona.id, 'Entrada', base.replace(hour=7))
        # Mismo referencia_id, otra entidad: no debe aparecer en el historial.
        _acceso(persona.id, 'Entrada', base.replace(hour=8),
                tipo_referencia='Visitante')
        _acceso(persona.id, 'Entrada', base.replace(hour=9),
                tipo_referencia='Vehiculo')
        db.session.commit()

        movimientos = construir_historial([persona], dia, dia)[0]['movimientos']
        assert len(movimientos) == 1
        assert movimientos[0]['entrada'].hour == 7

    def test_los_accesos_no_se_cruzan_entre_personas(self, app, crear_usuario):
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                            documento='111111')
        luis = crear_usuario(correo='luis@sena.edu.co', cargo='Aprendiz',
                             documento='222222')
        dia = date.today()
        base = datetime.combine(dia, datetime.min.time())
        _acceso(ana.id, 'Entrada', base.replace(hour=7))
        _acceso(luis.id, 'Entrada', base.replace(hour=8))
        _acceso(luis.id, 'Salida', base.replace(hour=10))
        db.session.commit()

        datos = {b['persona'].id: b for b in construir_historial([ana, luis], dia, dia)}
        assert datos[ana.id]['movimientos'][0]['salida'] is None
        assert datos[luis.id]['movimientos'][0]['permanencia_minutos'] == 120


class TestDiasAsistidosYFaltados:
    def test_dias_esperados_solo_cuenta_habiles_y_no_el_futuro(self):
        # Lunes 2026-08-24 .. domingo 2026-08-30; "hoy" es el jueves 27.
        habiles = dias_esperados(date(2026, 8, 24), date(2026, 8, 30),
                                 solo_habiles=True, hoy=date(2026, 8, 27))
        assert habiles == [date(2026, 8, 24), date(2026, 8, 25),
                           date(2026, 8, 26), date(2026, 8, 27)]

    def test_dias_esperados_puede_incluir_fin_de_semana(self):
        todos = dias_esperados(date(2026, 8, 29), date(2026, 8, 30),
                               solo_habiles=False, hoy=date(2026, 8, 31))
        assert todos == [date(2026, 8, 29), date(2026, 8, 30)]

    def test_asistencias_y_faltas_del_periodo(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        # Se usa una ventana ya pasada para que "hoy" no recorte el periodo.
        hoy = date.today()
        fin = hoy - timedelta(days=1)
        inicio = fin - timedelta(days=6)  # siete dias corridos

        # Asiste el primer y el tercer dia del periodo.
        for desplazamiento in (0, 2):
            dia = inicio + timedelta(days=desplazamiento)
            base = datetime.combine(dia, datetime.min.time())
            _acceso(persona.id, 'Entrada', base.replace(hour=7))
            _acceso(persona.id, 'Salida', base.replace(hour=13))
        db.session.commit()

        resumen = construir_historial([persona], inicio, fin,
                                      solo_habiles=False)[0]['resumen']
        assert resumen['total_dias_esperados'] == 7
        assert resumen['total_dias_asistidos'] == 2
        assert resumen['total_dias_faltados'] == 5
        assert resumen['porcentaje_asistencia'] == pytest.approx(28.6)
        assert sum(resumen['faltas_por_dia_semana'].values()) == 5
        assert resumen['promedio_permanencia_minutos'] == 360

    def test_varias_entradas_el_mismo_dia_cuentan_un_solo_dia(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        base = datetime.combine(dia, datetime.min.time())
        for hora_entrada, hora_salida in ((7, 9), (10, 12), (14, 16)):
            _acceso(persona.id, 'Entrada', base.replace(hour=hora_entrada))
            _acceso(persona.id, 'Salida', base.replace(hour=hora_salida))
        db.session.commit()

        resumen = construir_historial([persona], dia, dia,
                                      solo_habiles=False)[0]['resumen']
        assert resumen['total_movimientos'] == 3
        assert resumen['total_dias_asistidos'] == 1
        assert resumen['total_dias_faltados'] == 0

    def test_dia_mas_faltado_identifica_el_dia_de_la_semana(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        # Tres lunes seguidos sin ningun registro: el lunes debe ser el peor.
        fin = date(2026, 8, 17)   # lunes
        inicio = date(2026, 8, 3)  # lunes, dos semanas antes
        base = datetime.combine(date(2026, 8, 4), datetime.min.time())
        _acceso(persona.id, 'Entrada', base.replace(hour=7))
        db.session.commit()

        resumen = construir_historial([persona], inicio, fin,
                                      solo_habiles=True)[0]['resumen']
        assert resumen['faltas_por_dia_semana']['Lunes'] == 3
        assert resumen['dia_mas_faltado'] == 'Lunes'

    def test_periodo_fuera_de_rango_no_trae_movimientos(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        antiguo = date.today() - timedelta(days=90)
        _acceso(persona.id, 'Entrada',
                datetime.combine(antiguo, datetime.min.time()).replace(hour=7))
        db.session.commit()

        reciente = date.today()
        bloque = construir_historial([persona], reciente - timedelta(days=5),
                                     reciente)[0]
        assert bloque['movimientos'] == []
        assert bloque['resumen']['total_dias_asistidos'] == 0


class TestVista:
    def test_sin_filtros_muestra_el_formulario_vacio(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)
        respuesta = client.get(RUTA)
        assert respuesta.status_code == 200
        assert 'Historial de ingresos' in respuesta.get_data(as_text=True)

    def test_la_pagina_muestra_el_nombre_y_los_equipos(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                            documento='111111', nombre='Ana Rodriguez')
        equipo = Equipo(nombre='Portatil Dell', usuario_id=ana.id)
        db.session.add(equipo)
        db.session.commit()

        base = datetime.combine(date.today(), datetime.min.time())
        _acceso(ana.id, 'Entrada', base.replace(hour=7),
                equipos_str=str(equipo.id))
        _acceso(ana.id, 'Salida', base.replace(hour=12))
        db.session.commit()

        _entrar(client, celador)
        html = client.get(f'{RUTA}?usuario_id={ana.id}').get_data(as_text=True)
        assert 'Ana Rodriguez' in html
        assert 'Portatil Dell' in html

    def test_rango_de_fechas_invertido_no_rompe_la_vista(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)
        respuesta = client.get(
            f'{RUTA_API}?usuario_id={celador.id}'
            '&fecha_inicio=2026-08-30&fecha_fin=2026-08-01')
        assert respuesta.status_code == 200
        cuerpo = respuesta.get_json()
        assert cuerpo['fecha_inicio'] == '2026-08-01'
        assert cuerpo['fecha_fin'] == '2026-08-30'
