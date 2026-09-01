"""Pruebas del historial de ingresos por persona.

Cubren lo que puede romperse en silencio: los permisos a nivel de objeto (un
aprendiz mirando el historial de otro), el emparejado entrada/salida cuando
faltan registros, la contaminacion entre entidades por el referencia_id
polimorfico, y --sobre todo-- las tres cifras con las que la institucion toma
decisiones sobre una persona: porcentaje de asistencia, total de faltas y dia
que mas falta. Cada una tuvo un defecto medido en produccion y cada uno tiene
aqui su prueba (ver las clases TestVentanaExigible, TestTurnoNocturno,
TestPorcentajeDeAsistencia y TestDiaMasFaltado).
"""
from datetime import date, datetime, timedelta

import pytest

from app import db
from app.models.accesos import Acceso
from app.models.entidades import Equipo
from app.models.fichas import Ficha
from app.routes.porteria import historial_persona as modulo
from app.routes.porteria.historial_persona import (
    construir_historial,
    dias_esperados,
)

RUTA = '/porteria/historial-persona'
RUTA_API = '/porteria/api/historial-persona'

# Fecha fija de referencia para las pruebas de calendario. Sin esto, cada
# prueba mediria un periodo distinto segun el dia en que se ejecute.
HOY = date(2026, 9, 1)


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


def _acceso(referencia_id, tipo, momento, tipo_referencia='Usuario',
            equipos_str=None, operador_id=None):
    db.session.add(Acceso(punto_id=1, referencia_id=referencia_id,
                          tipo_referencia=tipo_referencia, tipo=tipo,
                          fecha=momento, equipos_str=equipos_str,
                          operador_id=operador_id))


def _bloques(*argumentos, **nombrados):
    return construir_historial(*argumentos, **nombrados)['bloques']


def _jornada(persona_id, dia, hora_entrada=7, hora_salida=13):
    base = datetime.combine(dia, datetime.min.time())
    _acceso(persona_id, 'Entrada', base.replace(hour=hora_entrada))
    _acceso(persona_id, 'Salida', base.replace(hour=hora_salida))


def _anclar_vinculacion(persona_id, dia=date(2026, 7, 1)):
    """Deja un acceso viejo para que la ventana exigible no se recorte.

    La fecha del primer acceso hace de fecha de vinculacion (no existe esa
    columna). En las pruebas que miden otra cosa, este ancla evita que el
    recorte por vinculacion cambie el periodo sin que se note.
    """
    _acceso(persona_id, 'Entrada',
            datetime.combine(dia, datetime.min.time()).replace(hour=7))
    _acceso(persona_id, 'Salida',
            datetime.combine(dia, datetime.min.time()).replace(hour=13))


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

        movimientos = _bloques([persona], dia, dia)[0]['movimientos']
        assert len(movimientos) == 1
        assert movimientos[0]['permanencia_minutos'] == 330
        assert movimientos[0]['salida'].hour == 12

    def test_entrada_de_hoy_sin_salida_es_alguien_que_sigue_adentro(
            self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        _acceso(persona.id, 'Entrada',
                datetime.combine(dia, datetime.min.time()).replace(hour=8))
        db.session.commit()

        bloque = _bloques([persona], dia, dia)[0]
        assert len(bloque['movimientos']) == 1
        assert bloque['movimientos'][0]['salida'] is None
        assert bloque['movimientos'][0]['abierto'] is True
        # No es una anomalia de la persona: todavia no le toca salir.
        assert bloque['resumen']['sin_salida'] == 0
        assert bloque['resumen']['abiertos'] == 1

    def test_entrada_antigua_sin_salida_si_es_anomalia(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today() - timedelta(days=10)
        _acceso(persona.id, 'Entrada',
                datetime.combine(dia, datetime.min.time()).replace(hour=8))
        db.session.commit()

        resumen = _bloques([persona], dia, dia)[0]['resumen']
        assert resumen['sin_salida'] == 1
        assert resumen['abiertos'] == 0

    def test_dos_entradas_seguidas_dejan_la_primera_sin_salida(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        base = datetime.combine(dia, datetime.min.time())
        _acceso(persona.id, 'Entrada', base.replace(hour=7))
        _acceso(persona.id, 'Entrada', base.replace(hour=9))
        _acceso(persona.id, 'Salida', base.replace(hour=11))
        db.session.commit()

        bloque = _bloques([persona], dia, dia)[0]
        movimientos = bloque['movimientos']
        assert len(movimientos) == 2
        assert movimientos[0]['salida'] is None
        assert movimientos[1]['permanencia_minutos'] == 120
        # Volver a entrar sin haber salido si es un registro incompleto real,
        # aunque sea de hoy: solo el ULTIMO movimiento puede estar abierto.
        assert bloque['resumen']['sin_salida'] == 1

    def test_salida_sin_entrada_previa_se_conserva(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        _acceso(persona.id, 'Salida',
                datetime.combine(dia, datetime.min.time()).replace(hour=6))
        db.session.commit()

        movimientos = _bloques([persona], dia, dia)[0]['movimientos']
        assert len(movimientos) == 1
        assert movimientos[0]['entrada'] is None
        assert movimientos[0]['salida'].hour == 6
        assert movimientos[0]['entrada_fuera_de_ventana'] is True

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

        equipos = _bloques([persona], dia, dia)[0]['movimientos'][0]['equipos']
        assert 'Portatil Lenovo' in equipos
        assert any('9999' in nombre for nombre in equipos)


class TestCierreAutomatico:
    def test_cierre_de_medianoche_sin_operador_se_marca(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        base = datetime.combine(dia, datetime.min.time())
        _acceso(persona.id, 'Entrada', base.replace(hour=7))
        _acceso(persona.id, 'Salida',
                base.replace(hour=23, minute=59, second=59))
        db.session.commit()

        movimiento = _bloques([persona], dia, dia)[0]['movimientos'][0]
        assert movimiento['cierre_automatico'] is True

    def test_salida_real_a_las_2359_no_es_cierre_automatico(self, app, crear_usuario):
        """La hora sola no distingue: el cierre lo delata la falta de operador."""
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date.today()
        base = datetime.combine(dia, datetime.min.time())
        _acceso(persona.id, 'Entrada', base.replace(hour=7),
                operador_id=celador.id)
        _acceso(persona.id, 'Salida',
                base.replace(hour=23, minute=59, second=59),
                operador_id=celador.id)
        db.session.commit()

        movimiento = _bloques([persona], dia, dia)[0]['movimientos'][0]
        assert movimiento['cierre_automatico'] is False


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

        movimientos = _bloques([persona], dia, dia)[0]['movimientos']
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

        datos = {b['persona'].id: b for b in _bloques([ana, luis], dia, dia)}
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
        inicio, fin = date(2026, 8, 3), date(2026, 8, 9)  # lunes a domingo

        # Asiste el primer y el tercer dia del periodo.
        for desplazamiento in (0, 2):
            _jornada(persona.id, inicio + timedelta(days=desplazamiento))
        db.session.commit()

        resumen = _bloques([persona], inicio, fin, solo_habiles=False,
                           hoy=HOY)[0]['resumen']
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

        resumen = _bloques([persona], dia, dia, solo_habiles=False)[0]['resumen']
        assert resumen['total_movimientos'] == 3
        assert resumen['total_dias_asistidos'] == 1
        assert resumen['total_dias_faltados'] == 0

    def test_periodo_fuera_de_rango_no_trae_movimientos(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        antiguo = date.today() - timedelta(days=90)
        _acceso(persona.id, 'Entrada',
                datetime.combine(antiguo, datetime.min.time()).replace(hour=7))
        db.session.commit()

        reciente = date.today()
        bloque = _bloques([persona], reciente - timedelta(days=5), reciente)[0]
        assert bloque['movimientos'] == []
        assert bloque['resumen']['total_dias_asistidos'] == 0


class TestVentanaExigible:
    """Nadie falta antes de estar vinculado ni despues de terminar su ficha."""

    def test_aprendiz_recien_vinculado_con_asistencia_perfecta(
            self, app, crear_usuario):
        """El caso medido: 8,7% de asistencia y 157 faltas con asistencia perfecta.

        Se consulta desde el 1 de enero a alguien cuyo primer ingreso es del 3
        de agosto. Antes, `dias_esperados` se calculaba una sola vez sobre todo
        el rango y le anotaba una falta por cada dia habil en que ni siquiera
        pertenecia al centro.
        """
        persona = crear_usuario(correo='nuevo@sena.edu.co', cargo='Aprendiz')
        dia = date(2026, 8, 3)
        while dia <= date(2026, 8, 28):
            if dia.weekday() < 5:
                _jornada(persona.id, dia, 7, 17)
            dia += timedelta(days=1)
        db.session.commit()

        resumen = _bloques([persona], date(2026, 1, 1), date(2026, 8, 28),
                           hoy=HOY)[0]['resumen']
        assert resumen['total_dias_asistidos'] == 20
        assert resumen['total_dias_esperados'] == 20
        assert resumen['total_dias_faltados'] == 0
        assert resumen['porcentaje_asistencia'] == 100.0
        assert resumen['periodo_evaluado_inicio'] == date(2026, 8, 3)
        assert 'vinculacion' in resumen['motivos_ventana']

    def test_egresado_no_acumula_faltas_tras_terminar_su_ficha(
            self, app, crear_usuario):
        ficha = Ficha(numero='2758899', programa='ADSO',
                      fecha_finalizacion=date(2026, 8, 14))
        db.session.add(ficha)
        db.session.commit()
        persona = crear_usuario(correo='egresado@sena.edu.co', cargo='Aprendiz',
                                ficha='2758899', ficha_id=ficha.id)

        dia = date(2026, 8, 3)
        while dia <= date(2026, 8, 14):
            if dia.weekday() < 5:
                _jornada(persona.id, dia)
            dia += timedelta(days=1)
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 31),
                           hoy=HOY)[0]['resumen']
        assert resumen['periodo_evaluado_fin'] == date(2026, 8, 14)
        assert resumen['total_dias_esperados'] == 10
        assert resumen['total_dias_faltados'] == 0
        assert 'fin_de_ficha' in resumen['motivos_ventana']

    def test_sin_ningun_ingreso_se_avisa_que_no_hay_referencia(
            self, app, crear_usuario):
        """Sin un solo acceso no hay forma de acotar: se dice, no se disimula."""
        persona = crear_usuario(correo='fantasma@sena.edu.co', cargo='Aprendiz')
        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 7),
                           hoy=HOY)[0]['resumen']
        assert 'sin_referencia_de_vinculacion' in resumen['motivos_ventana']
        assert resumen['total_dias_faltados'] == 5

    def test_periodo_anterior_a_la_vinculacion_no_da_porcentaje(
            self, app, crear_usuario):
        """Consultar enero de quien entro en agosto no es 0%, es 'sin datos'."""
        persona = crear_usuario(correo='nuevo@sena.edu.co', cargo='Aprendiz')
        _jornada(persona.id, date(2026, 8, 3))
        db.session.commit()

        resumen = _bloques([persona], date(2026, 1, 5), date(2026, 1, 9),
                           hoy=HOY)[0]['resumen']
        assert resumen['total_dias_esperados'] == 0
        assert resumen['total_dias_faltados'] == 0
        assert resumen['porcentaje_asistencia'] is None


class TestTurnoNocturno:
    """Un dia con presencia comprobada no puede figurar como falta."""

    def test_la_salida_de_madrugada_marca_asistido_ese_dia(
            self, app, crear_usuario):
        celador = crear_usuario(correo='noct@sena.edu.co', cargo='Celador',
                                documento='777001')
        # Entra el domingo a las 22:00 y sale el lunes a las 06:00.
        _acceso(celador.id, 'Entrada', datetime(2026, 8, 2, 22, 0))
        _acceso(celador.id, 'Salida', datetime(2026, 8, 3, 6, 0))
        db.session.commit()

        bloque = _bloques([celador], date(2026, 8, 3), date(2026, 8, 3),
                          hoy=HOY)[0]
        movimiento = bloque['movimientos'][0]
        assert movimiento['dias'] == [date(2026, 8, 2), date(2026, 8, 3)]
        assert date(2026, 8, 3) in bloque['resumen']['dias_asistidos']
        assert bloque['resumen']['total_dias_faltados'] == 0

    def test_celador_nocturno_no_acumula_una_falta_por_noche(
            self, app, crear_usuario):
        """Antes se fechaba el movimiento por la entrada: el lunes salia falta."""
        celador = crear_usuario(correo='noct@sena.edu.co', cargo='Celador',
                                documento='777001')
        # Tres turnos domingo 22:00 -> lunes 06:00.
        for domingo in (date(2026, 8, 2), date(2026, 8, 9), date(2026, 8, 16)):
            _acceso(celador.id, 'Entrada',
                    datetime.combine(domingo, datetime.min.time()).replace(hour=22))
            _acceso(celador.id, 'Salida',
                    datetime.combine(domingo + timedelta(days=1),
                                     datetime.min.time()).replace(hour=6))
        db.session.commit()

        resumen = _bloques([celador], date(2026, 8, 3), date(2026, 8, 21),
                           hoy=HOY)[0]['resumen']
        lunes = [date(2026, 8, 3), date(2026, 8, 10), date(2026, 8, 17)]
        assert all(dia in resumen['dias_asistidos'] for dia in lunes)
        assert not any(dia in resumen['dias_faltados'] for dia in lunes)
        assert resumen['faltas_por_dia_semana'].get('Lunes', 0) == 0
        # Las noches del domingo se ven, pero no entran al calculo habil.
        assert resumen['total_dias_fuera_de_computo'] == 3


class TestPorcentajeDeAsistencia:
    """Numerador y denominador tienen que hablar del mismo calendario."""

    def test_asistir_los_siete_dias_no_pasa_de_cien(self, app, crear_usuario):
        """Medido antes del arreglo: 140%."""
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        for desplazamiento in range(7):
            _jornada(persona.id, date(2026, 8, 3) + timedelta(days=desplazamiento))
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 9),
                           solo_habiles=True, hoy=HOY)[0]['resumen']
        assert resumen['total_dias_esperados'] == 5
        assert resumen['total_dias_asistidos'] == 5
        assert resumen['porcentaje_asistencia'] == 100.0
        assert resumen['total_dias_fuera_de_computo'] == 2

    def test_asistir_solo_en_fin_de_semana_no_inventa_asistencia(
            self, app, crear_usuario):
        """Medido antes del arreglo: 40% de asistencia y 5 faltas sobre 5 dias."""
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _anclar_vinculacion(persona.id)
        _jornada(persona.id, date(2026, 8, 8))   # sabado
        _jornada(persona.id, date(2026, 8, 9))   # domingo
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 9),
                           solo_habiles=True, hoy=HOY)[0]['resumen']
        assert resumen['total_dias_esperados'] == 5
        assert resumen['total_dias_asistidos'] == 0
        assert resumen['total_dias_faltados'] == 5
        assert resumen['porcentaje_asistencia'] == 0.0
        # La asistencia real no se oculta, solo queda fuera del computo.
        assert resumen['dias_fuera_de_computo'] == [date(2026, 8, 8),
                                                    date(2026, 8, 9)]

    def test_contando_todos_los_dias_el_fin_de_semana_si_suma(
            self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        for desplazamiento in range(7):
            _jornada(persona.id, date(2026, 8, 3) + timedelta(days=desplazamiento))
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 9),
                           solo_habiles=False, hoy=HOY)[0]['resumen']
        assert resumen['total_dias_esperados'] == 7
        assert resumen['porcentaje_asistencia'] == 100.0
        assert resumen['total_dias_fuera_de_computo'] == 0


class TestDiaMasFaltado:
    """Debe reflejar conducta, no cuantos lunes trae el calendario."""

    def test_usa_la_tasa_y_no_el_conteo_bruto(self, app, crear_usuario):
        """Lunes y miercoles empatan a 3 faltas, pero hay 4 lunes y 3 miercoles."""
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _anclar_vinculacion(persona.id)
        dia = date(2026, 8, 3)
        while dia <= date(2026, 8, 24):
            # Asiste martes, jueves y viernes; un solo lunes; ningun miercoles.
            if dia.weekday() in (1, 3, 4) or dia == date(2026, 8, 24):
                _jornada(persona.id, dia)
            dia += timedelta(days=1)
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 24),
                           hoy=HOY)[0]['resumen']
        assert resumen['faltas_por_dia_semana']['Lunes'] == 3
        assert resumen['faltas_por_dia_semana']['Miercoles'] == 3
        assert resumen['detalle_dias_semana']['Lunes']['oportunidades'] == 4
        assert resumen['detalle_dias_semana']['Miercoles']['oportunidades'] == 3
        assert resumen['dia_mas_faltado'] == 'Miercoles'

    def test_quien_nunca_asiste_no_tiene_un_dia_peor(self, app, crear_usuario):
        """Antes salia siempre 'Lunes', que era el dia mas frecuente del mes."""
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _anclar_vinculacion(persona.id)
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 21),
                           hoy=HOY)[0]['resumen']
        assert resumen['total_dias_faltados'] == 15
        assert resumen['dia_mas_faltado'] is None
        assert resumen['motivo_sin_dia_mas_faltado'] == 'empate'
        assert len(resumen['dias_mas_faltados_empatados']) == 5

    def test_empate_entre_dos_dias_no_devuelve_el_primero(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _anclar_vinculacion(persona.id)
        dia = date(2026, 8, 3)
        while dia <= date(2026, 8, 21):
            # Falta todos los lunes y todos los miercoles, asiste el resto.
            if dia.weekday() in (1, 3, 4):
                _jornada(persona.id, dia)
            dia += timedelta(days=1)
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 21),
                           hoy=HOY)[0]['resumen']
        assert resumen['dia_mas_faltado'] is None
        assert resumen['dias_mas_faltados_empatados'] == ['Lunes', 'Miercoles']

    def test_periodo_corto_no_afirma_un_patron(self, app, crear_usuario):
        """Con un solo lunes en el periodo, faltar a el no es una costumbre."""
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _anclar_vinculacion(persona.id)
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 7),
                           hoy=HOY)[0]['resumen']
        assert resumen['total_dias_faltados'] == 5
        assert resumen['dia_mas_faltado'] is None
        assert resumen['motivo_sin_dia_mas_faltado'] == 'datos_insuficientes'

    def test_sin_faltas_no_hay_dia_peor(self, app, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        dia = date(2026, 8, 3)
        while dia <= date(2026, 8, 21):
            if dia.weekday() < 5:
                _jornada(persona.id, dia)
            dia += timedelta(days=1)
        db.session.commit()

        resumen = _bloques([persona], date(2026, 8, 3), date(2026, 8, 21),
                           hoy=HOY)[0]['resumen']
        assert resumen['dia_mas_faltado'] is None
        assert resumen['motivo_sin_dia_mas_faltado'] == 'sin_faltas'


class TestCortesDelRango:
    """El filtro de fechas no puede fabricar anomalias de la persona."""

    def test_entrada_el_ultimo_dia_conserva_su_salida(self, app, crear_usuario):
        celador = crear_usuario(correo='noct@sena.edu.co', cargo='Celador',
                                documento='777001')
        _acceso(celador.id, 'Entrada', datetime(2026, 8, 7, 22, 0))
        _acceso(celador.id, 'Salida', datetime(2026, 8, 8, 6, 0))
        db.session.commit()

        bloque = _bloques([celador], date(2026, 8, 3), date(2026, 8, 7),
                          hoy=HOY)[0]
        movimiento = bloque['movimientos'][0]
        assert movimiento['salida'] is not None
        assert movimiento['permanencia_minutos'] == 480
        assert movimiento['salida_posterior_al_rango'] is True
        # La anomalia "sin salida registrada" la fabricaba el corte del rango.
        assert bloque['resumen']['sin_salida'] == 0

    def test_salida_el_primer_dia_conserva_su_entrada(self, app, crear_usuario):
        celador = crear_usuario(correo='noct@sena.edu.co', cargo='Celador',
                                documento='777001')
        _acceso(celador.id, 'Entrada', datetime(2026, 8, 2, 22, 0))
        _acceso(celador.id, 'Salida', datetime(2026, 8, 3, 6, 0))
        db.session.commit()

        movimiento = _bloques([celador], date(2026, 8, 3), date(2026, 8, 7),
                              hoy=HOY)[0]['movimientos'][0]
        assert movimiento['entrada'] is not None
        assert movimiento['entrada_fuera_de_ventana'] is False
        assert movimiento['entrada_previa_al_rango'] is True

    def test_movimiento_totalmente_fuera_del_rango_no_se_cuela(
            self, app, crear_usuario):
        """El margen sirve para emparejar, no para ampliar lo que se muestra."""
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _jornada(persona.id, date(2026, 8, 8))  # un dia despues del rango
        db.session.commit()

        bloque = _bloques([persona], date(2026, 8, 3), date(2026, 8, 7),
                          hoy=HOY)[0]
        assert bloque['movimientos'] == []


class TestTopesDeCarga:
    """El contenedor tiene 1 GB y un solo proceso: una consulta no puede tumbarlo."""

    def test_rango_demasiado_amplio_se_recorta_y_se_avisa(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)
        respuesta = client.get(
            f'{RUTA_API}?usuario_id={celador.id}'
            '&fecha_inicio=2025-01-01&fecha_fin=2026-08-28')
        assert respuesta.status_code == 200
        cuerpo = respuesta.get_json()
        assert cuerpo['rango_recortado'] is True
        inicio = date.fromisoformat(cuerpo['fecha_inicio'])
        fin = date.fromisoformat(cuerpo['fecha_fin'])
        assert (fin - inicio).days + 1 == modulo.MAXIMO_DIAS_RANGO

    def test_rango_normal_no_se_recorta(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)
        respuesta = client.get(
            f'{RUTA_API}?usuario_id={celador.id}'
            '&fecha_inicio=2026-08-01&fecha_fin=2026-08-28')
        assert respuesta.get_json()['rango_recortado'] is False

    def test_exceso_de_accesos_deja_personas_fuera_en_vez_de_traerlas_a_medias(
            self, app, crear_usuario, monkeypatch):
        monkeypatch.setattr(modulo, 'MAXIMO_ACCESOS', 2)
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                            documento='111111', nombre='Ana')
        luis = crear_usuario(correo='luis@sena.edu.co', cargo='Aprendiz',
                             documento='222222', nombre='Luis')
        _jornada(ana.id, date(2026, 8, 3))
        _jornada(luis.id, date(2026, 8, 3))
        db.session.commit()

        historial = construir_historial([ana, luis], date(2026, 8, 3),
                                        date(2026, 8, 7), hoy=HOY)
        assert historial['truncado'] is True
        assert [p.id for p in historial['omitidas']] == [luis.id]
        assert [b['persona'].id for b in historial['bloques']] == [ana.id]


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
        assert 'Periodo evaluado para esta persona' in html

    def test_la_pagina_no_pinta_un_porcentaje_sin_dias_exigibles(
            self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                            documento='111111', nombre='Ana Rodriguez')
        _jornada(ana.id, date.today())
        db.session.commit()

        _entrar(client, celador)
        futuro = date.today() + timedelta(days=10)
        html = client.get(
            f'{RUTA}?usuario_id={ana.id}'
            f'&fecha_inicio={futuro.isoformat()}'
            f'&fecha_fin={(futuro + timedelta(days=4)).isoformat()}'
        ).get_data(as_text=True)
        assert 'Sin días exigibles en el periodo' in html

    def test_la_pagina_explica_el_empate_en_vez_de_afirmar_un_dia(
            self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                            documento='111111', nombre='Ana Rodriguez')
        _anclar_vinculacion(ana.id)
        db.session.commit()

        _entrar(client, celador)
        html = client.get(f'{RUTA}?usuario_id={ana.id}'
                          '&fecha_inicio=2026-08-03&fecha_fin=2026-08-21'
                          ).get_data(as_text=True)
        assert 'Sin día destacado: empatan' in html

    def test_la_pagina_avisa_cuando_recorta_el_rango(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)
        html = client.get(f'{RUTA}?usuario_id={celador.id}'
                          '&fecha_inicio=2025-01-01&fecha_fin=2026-08-28'
                          ).get_data(as_text=True)
        assert f'se limitó a {modulo.MAXIMO_DIAS_RANGO} días' in html

    def test_la_pagina_avisa_de_las_personas_no_analizadas(
            self, client, crear_usuario, monkeypatch):
        monkeypatch.setattr(modulo, 'MAXIMO_ACCESOS', 2)
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                            documento='111111', nombre='Ana Rodriguez',
                            ficha='2758899')
        luis = crear_usuario(correo='luis@sena.edu.co', cargo='Aprendiz',
                             documento='222222', nombre='Luis Perez',
                             ficha='2758899')
        _jornada(ana.id, date.today())
        _jornada(luis.id, date.today())
        db.session.commit()

        _entrar(client, celador)
        html = client.get(f'{RUTA}?ficha=2758899').get_data(as_text=True)
        assert 'quedaron sin analizar' in html
        assert 'Luis Perez' in html

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
