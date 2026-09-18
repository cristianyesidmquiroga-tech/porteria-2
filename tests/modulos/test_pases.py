"""Pruebas del modulo de pases: visitantes, vehiculos y objetos externos.

Estas rutas manejan datos personales de visitantes y no tenian ni una
prueba. Se cubre creacion, edicion/actualizacion/eliminacion de objetos, y
el registro de entrada/salida de visitantes y vehiculos reales (que ya
estaba cubierto para usuarios pero no para estas entidades).
"""
import pytest

from app.models.accesos import Acceso, Auditoria
from app.models.entidades import ObjetoExterno, Vehiculo, Visitante


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


def _celador(crear_usuario, correo='celador@sena.edu.co', documento='777777'):
    return crear_usuario(correo=correo, cargo='Celador', documento=documento)


def _aprendiz(crear_usuario, correo='aprendiz@sena.edu.co', documento='123123'):
    return crear_usuario(correo=correo, cargo='Aprendiz', documento=documento)


class TestCrearVisitante:
    def test_celador_crea_visitante(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        r = client.post('/porteria/pases/crear_visitante', data={
            'nombre': 'Maria Gomez', 'documento': '9988776', 'motivo': 'Reunion',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200
        assert r.get_json()['status'] == 'success'

        visitante = Visitante.query.filter_by(documento='9988776').first()
        assert visitante is not None
        assert visitante.nombre == 'Maria Gomez'
        assert visitante.qr_code == 'SENA-VISIT:9988776'
        assert visitante.activo is True

    def test_aprendiz_no_crea_visitante(self, client, crear_usuario):
        aprendiz = _aprendiz(crear_usuario)
        _entrar(client, aprendiz)

        r = client.post('/porteria/pases/crear_visitante', data={
            'nombre': 'Maria Gomez', 'documento': '9988776',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 403
        assert Visitante.query.filter_by(documento='9988776').first() is None

    def test_sin_documento_no_crea_visitante(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        r = client.post('/porteria/pases/crear_visitante', data={
            'nombre': 'Maria Gomez',
        }, follow_redirects=False)
        assert r.status_code == 302
        assert Visitante.query.count() == 0

    def test_visitante_existente_se_reactiva_en_vez_de_duplicar(self, client, crear_usuario, db):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        client.post('/porteria/pases/crear_visitante', data={
            'nombre': 'Maria Gomez', 'documento': '9988776', 'motivo': 'Reunion',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        primero = Visitante.query.filter_by(documento='9988776').first()
        primero.activo = False
        db.session.commit()

        client.post('/porteria/pases/crear_visitante', data={
            'nombre': 'Maria Gomez R.', 'documento': '9988776', 'motivo': 'Entrega',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})

        assert Visitante.query.filter_by(documento='9988776').count() == 1
        actualizado = Visitante.query.filter_by(documento='9988776').first()
        assert actualizado.nombre == 'Maria Gomez R.'
        assert actualizado.activo is True


class TestCrearVehiculo:
    def test_celador_crea_vehiculo(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        r = client.post('/porteria/pases/crear_vehiculo', data={
            'placa': 'abc123', 'tipo': 'Externo', 'propietario': 'Juan',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200

        vehiculo = Vehiculo.query.filter_by(placa='ABC123').first()
        assert vehiculo is not None
        assert vehiculo.qr_code == 'SENA-VEH-E:ABC123'

    def test_vehiculo_sena_usa_prefijo_distinto(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        client.post('/porteria/pases/crear_vehiculo', data={
            'placa': 'sen001', 'tipo': 'SENA',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        vehiculo = Vehiculo.query.filter_by(placa='SEN001').first()
        assert vehiculo.qr_code == 'SENA-VEH-S:SEN001'

    def test_placa_vacia_no_crea_vehiculo(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        r = client.post('/porteria/pases/crear_vehiculo', data={'tipo': 'Externo'},
                        follow_redirects=False)
        assert r.status_code == 302
        assert Vehiculo.query.count() == 0

    def test_aprendiz_no_crea_vehiculo(self, client, crear_usuario):
        aprendiz = _aprendiz(crear_usuario)
        _entrar(client, aprendiz)

        r = client.post('/porteria/pases/crear_vehiculo', data={'placa': 'ABC123'},
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 403
        assert Vehiculo.query.count() == 0


class TestCrearObjeto:
    def test_celador_crea_objeto_con_serial(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        r = client.post('/porteria/pases/crear_objeto', data={
            'descripcion': 'Camara fotografica', 'serial': 'SN-CAM-1',
            'propietario': 'Canal Regional',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200

        objeto = ObjetoExterno.query.filter_by(serial='SN-CAM-1').first()
        assert objeto is not None
        assert objeto.qr_code == 'SENA-OBJ:SN-CAM-1'

    def test_objeto_sin_serial_genera_uno(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        r = client.post('/porteria/pases/crear_objeto', data={
            'descripcion': 'Caja sin marcar',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200

        objeto = ObjetoExterno.query.filter_by(descripcion='Caja sin marcar').first()
        assert objeto is not None
        assert objeto.serial.startswith('SN-')

    def test_descripcion_vacia_no_crea_objeto(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)

        r = client.post('/porteria/pases/crear_objeto', data={'serial': 'X1'},
                        follow_redirects=False)
        assert r.status_code == 302
        assert ObjetoExterno.query.count() == 0

    def test_aprendiz_no_crea_objeto(self, client, crear_usuario):
        aprendiz = _aprendiz(crear_usuario)
        _entrar(client, aprendiz)

        r = client.post('/porteria/pases/crear_objeto', data={
            'descripcion': 'Camara fotografica',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 403
        assert ObjetoExterno.query.count() == 0


class TestEditarActualizarEliminarObjeto:
    def _crear_objeto(self, db, descripcion='Camara', serial='SN-1', propietario='X'):
        objeto = ObjetoExterno(descripcion=descripcion, serial=serial,
                               propietario=propietario, qr_code=f'SENA-OBJ:{serial}')
        db.session.add(objeto)
        db.session.commit()
        return objeto

    def test_celador_ve_formulario_de_edicion(self, client, crear_usuario, db):
        celador = _celador(crear_usuario)
        objeto = self._crear_objeto(db)
        _entrar(client, celador)

        r = client.get(f'/porteria/pases/editar_objeto/{objeto.id}')
        assert r.status_code == 200
        assert b'Camara' in r.data

    def test_editar_objeto_inexistente_da_404(self, client, crear_usuario):
        celador = _celador(crear_usuario)
        _entrar(client, celador)
        assert client.get('/porteria/pases/editar_objeto/999999').status_code == 404

    def test_aprendiz_no_ve_formulario_de_edicion(self, client, crear_usuario, db):
        aprendiz = _aprendiz(crear_usuario)
        objeto = self._crear_objeto(db)
        _entrar(client, aprendiz)

        r = client.get(f'/porteria/pases/editar_objeto/{objeto.id}', follow_redirects=False)
        assert r.status_code == 302

    def test_celador_actualiza_objeto(self, client, crear_usuario, db):
        celador = _celador(crear_usuario)
        objeto = self._crear_objeto(db)
        objeto_id = objeto.id
        _entrar(client, celador)

        r = client.post(f'/porteria/pases/actualizar_objeto/{objeto_id}', data={
            'descripcion': 'Camara actualizada', 'serial': 'SN-1',
            'propietario': 'Nuevo dueño', 'motivo': 'Actualizado',
        }, follow_redirects=False)
        assert r.status_code == 302

        db.session.refresh(objeto)
        assert objeto.descripcion == 'Camara actualizada'
        assert objeto.propietario == 'Nuevo dueño'

    def test_aprendiz_no_actualiza_objeto(self, client, crear_usuario, db):
        aprendiz = _aprendiz(crear_usuario)
        objeto = self._crear_objeto(db)
        objeto_id = objeto.id
        _entrar(client, aprendiz)

        client.post(f'/porteria/pases/actualizar_objeto/{objeto_id}', data={
            'descripcion': 'Hackeado',
        }, follow_redirects=False)

        db.session.refresh(objeto)
        assert objeto.descripcion != 'Hackeado'

    def test_celador_elimina_objeto(self, client, crear_usuario, db):
        celador = _celador(crear_usuario)
        objeto = self._crear_objeto(db)
        objeto_id = objeto.id
        _entrar(client, celador)

        r = client.post(f'/porteria/pases/eliminar_objeto/{objeto_id}',
                        follow_redirects=False)
        assert r.status_code == 302

        db.session.refresh(objeto)
        assert objeto.activo is False

    def test_aprendiz_no_elimina_objeto(self, client, crear_usuario, db):
        aprendiz = _aprendiz(crear_usuario)
        objeto = self._crear_objeto(db)
        objeto_id = objeto.id
        _entrar(client, aprendiz)

        client.post(f'/porteria/pases/eliminar_objeto/{objeto_id}',
                    follow_redirects=False)

        db.session.refresh(objeto)
        assert objeto.activo is True

    @pytest.mark.xfail(
        reason=('FALLO CONOCIDO: ObjetoExterno/Visitante/Vehiculo no tienen '
                'ningun campo de responsable/creador, asi que cualquier '
                'celador puede editar o borrar el pase de otro. Ver el '
                'reporte de esta tarea para el detalle.'),
        strict=True)
    def test_un_celador_no_deberia_poder_editar_el_pase_creado_por_otro(
            self, client, crear_usuario, db):
        """Analogo a TestEquipos.test_no_se_pueden_marcar_equipos_de_otro:
        que un celador no pueda tocar un pase que no le pertenece.

        A diferencia de Equipo (que sí guarda `usuario_id`), ObjetoExterno,
        Visitante y Vehiculo no tienen ningun campo que registre que celador
        creo o es responsable del pase: `actualizar_objeto` y
        `eliminar_objeto` solo comprueban `puede_operar_porteria`, sin mirar
        quien lo creo. Cualquier celador puede editar o borrar el pase de
        cualquier otro. Marcada como fallo conocido: ver el reporte.
        """
        celador_1 = _celador(crear_usuario, correo='celador1@sena.edu.co',
                             documento='777777')
        celador_2 = _celador(crear_usuario, correo='celador2@sena.edu.co',
                             documento='888888')
        objeto = self._crear_objeto(db, descripcion='Pase de celador 1')
        objeto_id = objeto.id

        _entrar(client, celador_2)
        client.post(f'/porteria/pases/actualizar_objeto/{objeto_id}', data={
            'descripcion': 'Modificado por celador 2', 'serial': 'SN-1',
        }, follow_redirects=False)

        db.session.refresh(objeto)
        # FALLO CONOCIDO: no existe ownership de pases entre celadores, asi
        # que esto SI cambia hoy. Ver reporte para el detalle.
        assert objeto.descripcion == 'Pase de celador 1', (
            'un celador puede editar el pase creado/atendido por otro: '
            'ObjetoExterno no tiene ningun campo de responsable/creador')


class TestMovimientoDeVisitantesYVehiculosReales:
    """Igual que TestCoherenciaDeMovimientos en test_porteria.py, pero para
    entidades Visitante y Vehiculo reales en vez de solo Usuario."""

    def _preparar(self, client, crear_usuario, db):
        celador = _celador(crear_usuario)
        visitante = Visitante(nombre='Visita', documento='V1', qr_code='SENA-VISIT:V1')
        vehiculo = Vehiculo(placa='XYZ999', tipo='Externo', qr_code='SENA-VEH-E:XYZ999')
        db.session.add_all([visitante, vehiculo])
        db.session.commit()
        _entrar(client, celador)
        return celador, visitante, vehiculo

    def test_entrada_de_visitante_se_registra(self, client, crear_usuario, db):
        _, visitante, _ = self._preparar(client, crear_usuario, db)
        r = client.post(
            f'/porteria/register_movement_entidad/Visitante/{visitante.id}/Entrada',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200
        assert Acceso.query.filter_by(referencia_id=visitante.id,
                                      tipo_referencia='Visitante',
                                      tipo='Entrada').count() == 1

    def test_doble_entrada_de_visitante_se_rechaza_y_audita(self, client, crear_usuario, db):
        _, visitante, _ = self._preparar(client, crear_usuario, db)
        client.post(
            f'/porteria/register_movement_entidad/Visitante/{visitante.id}/Entrada',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        r = client.post(
            f'/porteria/register_movement_entidad/Visitante/{visitante.id}/Entrada',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 409
        assert Acceso.query.filter_by(referencia_id=visitante.id,
                                      tipo_referencia='Visitante',
                                      tipo='Entrada').count() == 1
        assert Auditoria.query.filter_by(
            accion='Inconsistencia de Acceso Detectada').count() == 1

    def test_salida_de_visitante_sin_entrada_se_rechaza(self, client, crear_usuario, db):
        _, visitante, _ = self._preparar(client, crear_usuario, db)
        r = client.post(
            f'/porteria/register_movement_entidad/Visitante/{visitante.id}/Salida',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 409
        assert Acceso.query.filter_by(referencia_id=visitante.id,
                                      tipo_referencia='Visitante').count() == 0

    def test_entrada_de_vehiculo_se_registra(self, client, crear_usuario, db):
        _, _, vehiculo = self._preparar(client, crear_usuario, db)
        r = client.post(
            f'/porteria/register_movement_entidad/Vehiculo/{vehiculo.id}/Entrada',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200
        assert Acceso.query.filter_by(referencia_id=vehiculo.id,
                                      tipo_referencia='Vehiculo',
                                      tipo='Entrada').count() == 1

    def test_doble_entrada_de_vehiculo_se_rechaza_y_audita(self, client, crear_usuario, db):
        _, _, vehiculo = self._preparar(client, crear_usuario, db)
        client.post(
            f'/porteria/register_movement_entidad/Vehiculo/{vehiculo.id}/Entrada',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        r = client.post(
            f'/porteria/register_movement_entidad/Vehiculo/{vehiculo.id}/Entrada',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 409
        assert Acceso.query.filter_by(referencia_id=vehiculo.id,
                                      tipo_referencia='Vehiculo',
                                      tipo='Entrada').count() == 1
        assert Auditoria.query.filter_by(
            accion='Inconsistencia de Acceso Detectada').count() == 1

    def test_salida_de_vehiculo_sin_entrada_se_rechaza(self, client, crear_usuario, db):
        _, _, vehiculo = self._preparar(client, crear_usuario, db)
        r = client.post(
            f'/porteria/register_movement_entidad/Vehiculo/{vehiculo.id}/Salida',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 409
        assert Acceso.query.filter_by(referencia_id=vehiculo.id,
                                      tipo_referencia='Vehiculo').count() == 0

    def test_entrada_y_salida_completa_de_visitante(self, client, crear_usuario, db):
        _, visitante, _ = self._preparar(client, crear_usuario, db)
        client.post(
            f'/porteria/register_movement_entidad/Visitante/{visitante.id}/Entrada',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        r = client.post(
            f'/porteria/register_movement_entidad/Visitante/{visitante.id}/Salida',
            headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200
        assert Acceso.query.filter_by(referencia_id=visitante.id,
                                      tipo_referencia='Visitante').count() == 2
