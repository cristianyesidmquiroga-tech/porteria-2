"""Integridad referencial al borrar personas y equipos, e indices del esquema.

Hasta ahora borrar era una limpieza manual incompleta: cualquier aprendiz con
asistencias, cualquier persona con un mensaje (una foto rechazada genera uno
automatico) y cualquier celador que hubiera operado la porteria dejaban el
borrado en error 500. Un equipo que ya cruzo la puerta tampoco se podia borrar
desde el perfil. Estas pruebas cubren los cuatro casos y comprueban, contra el
esquema real, que los indices declarados en los modelos existen.
"""
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.models.accesos import Acceso, Auditoria
from app.models.asistencia import AsistenciaClase
from app.models.entidades import Equipo, ObjetoExterno
from app.models.mensajes import Mensaje, registrar_mensaje
from app.models.movimientos import MovimientoEquipo
from app.models.usuarios import Usuario


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


def _crear_admin(crear_usuario):
    return crear_usuario(correo='admin@sena.edu.co', cargo='Administrador',
                         rol='Admin', documento='999999')


def _borrar_como_admin(client, crear_usuario, objetivo_id):
    admin = _crear_admin(crear_usuario)
    _entrar(client, admin)
    return client.delete(f'/usuarios/api/admin/eliminar_usuario/{objetivo_id}',
                         json={'autorizado_por': 'Coordinacion',
                               'motivo': 'Prueba de integridad'})


class TestBorrarUsuario:
    def test_con_asistencias(self, client, crear_usuario, db):
        """Un aprendiz con asistencias registradas se puede borrar."""
        instructor = crear_usuario(correo='instructor@sena.edu.co',
                                   cargo='Instructor', documento='111')
        aprendiz = crear_usuario(correo='aprendiz2@sena.edu.co',
                                 documento='222')
        db.session.add(AsistenciaClase(instructor_id=instructor.id,
                                       aprendiz_id=aprendiz.id,
                                       ficha='2555001', presente=True))
        db.session.commit()

        r = _borrar_como_admin(client, crear_usuario, aprendiz.id)
        assert r.status_code == 200, r.get_json()
        assert db.session.get(Usuario, aprendiz.id) is None
        # La asistencia era un dato del aprendiz: se va con el.
        assert AsistenciaClase.query.filter_by(aprendiz_id=aprendiz.id).count() == 0

    def test_instructor_con_clases_dictadas(self, client, crear_usuario, db):
        """Borrar al instructor no destruye la asistencia de sus aprendices."""
        instructor = crear_usuario(correo='instructor@sena.edu.co',
                                   cargo='Instructor', documento='111')
        aprendiz = crear_usuario(correo='aprendiz2@sena.edu.co',
                                 documento='222')
        db.session.add(AsistenciaClase(instructor_id=instructor.id,
                                       aprendiz_id=aprendiz.id,
                                       ficha='2555001', presente=True))
        db.session.commit()

        r = _borrar_como_admin(client, crear_usuario, instructor.id)
        assert r.status_code == 200, r.get_json()
        registro = AsistenciaClase.query.filter_by(aprendiz_id=aprendiz.id).one()
        assert registro.instructor_id is None

    def test_con_mensajes(self, client, crear_usuario, db):
        """Una persona con foto rechazada (mensaje automatico) se puede borrar."""
        admin = _crear_admin(crear_usuario)
        persona = crear_usuario(correo='conmensaje@sena.edu.co',
                                documento='333')
        # Mismo camino que el rechazo de foto: un mensaje automatico del admin
        # en el hilo de la persona, mas una respuesta de la propia persona.
        registrar_mensaje(persona.id, admin,
                          'Tu foto fue rechazada: rostro no visible.',
                          automatico=True)
        registrar_mensaje(persona.id, persona, 'La vuelvo a subir, gracias.')
        db.session.commit()
        assert Mensaje.query.filter_by(usuario_id=persona.id).count() == 2

        _entrar(client, admin)
        r = client.delete(f'/usuarios/api/admin/eliminar_usuario/{persona.id}',
                          json={'motivo': 'Prueba'})
        assert r.status_code == 200, r.get_json()
        # El hilo era personal: desaparece completo con la persona.
        assert Mensaje.query.filter_by(usuario_id=persona.id).count() == 0

    def test_operador_de_porteria(self, client, crear_usuario, db):
        """Un celador que registro accesos y genero auditoria se puede borrar,
        y el historial institucional sobrevive sin el."""
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='444')
        visitante_id = 12345  # referencia externa cualquiera
        acceso = Acceso(punto_id=1, referencia_id=visitante_id,
                        tipo_referencia='Visitante', tipo='Entrada',
                        operador_id=celador.id)
        auditoria = Auditoria(usuario_id=celador.id,
                              nombre_usuario=celador.nombre,
                              tabla_afectada='accesos', registro_id=1,
                              accion='Salida forzada')
        db.session.add_all([acceso, auditoria])
        db.session.commit()
        acceso_id, auditoria_id = acceso.id, auditoria.id
        nombre_celador = celador.nombre

        r = _borrar_como_admin(client, crear_usuario, celador.id)
        assert r.status_code == 200, r.get_json()
        acceso = db.session.get(Acceso, acceso_id)
        assert acceso is not None            # el acceso tiene valor institucional
        assert acceso.operador_id is None    # pero ya no apunta a nadie borrado
        auditoria = db.session.get(Auditoria, auditoria_id)
        assert auditoria is not None
        assert auditoria.usuario_id is None
        assert auditoria.nombre_usuario == nombre_celador  # sigue siendo legible


class TestBorrarEquipo:
    def test_equipo_que_cruzo_la_porteria(self, client, crear_usuario, db):
        """Borrar un equipo desde el perfil funciona aunque tenga movimientos."""
        persona = crear_usuario(correo='duenio@sena.edu.co', documento='555')
        equipo = Equipo(nombre='Portatil HP', serial='SN-001',
                        usuario_id=persona.id)
        db.session.add(equipo)
        db.session.commit()
        db.session.add(MovimientoEquipo(equipo_id=equipo.id, punto_id=1,
                                        tipo='Entrada'))
        db.session.commit()
        equipo_id = equipo.id

        _entrar(client, persona)
        r = client.post(f'/equipos/delete/{equipo_id}',
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200, r.get_json()
        assert db.session.get(Equipo, equipo_id) is None
        assert MovimientoEquipo.query.filter_by(equipo_id=equipo_id).count() == 0


class TestIndices:
    """Se inspecciona el esquema creado de verdad, no el modelo."""

    def _indices(self, db, tabla):
        return {tuple(i['column_names']) for i in
                inspect(db.engine).get_indexes(tabla)}

    def test_indice_compuesto_del_escaner(self, db):
        indices = self._indices(db, 'accesos')
        assert ('referencia_id', 'tipo_referencia', 'fecha') in indices

    def test_indice_por_fecha_de_acceso(self, db):
        assert ('fecha',) in self._indices(db, 'accesos')

    def test_indices_de_claves_ajenas(self, db):
        assert ('punto_id',) in self._indices(db, 'accesos')
        assert ('carnet_id',) in self._indices(db, 'accesos')
        assert ('operador_id',) in self._indices(db, 'accesos')
        assert ('usuario_id',) in self._indices(db, 'auditoria')
        assert ('usuario_id',) in self._indices(db, 'equipos')
        assert ('equipo_id',) in self._indices(db, 'movimientos_equipos')
        assert ('visitante_id',) in self._indices(db, 'movimientos_visitantes')
        assert ('vehiculo_id',) in self._indices(db, 'movimientos_vehiculos')
        assert ('objeto_id',) in self._indices(db, 'movimientos_objetos')
        assert ('instructor_id',) in self._indices(db, 'asistencia_clases')
        assert ('aprendiz_id',) in self._indices(db, 'asistencia_clases')


class TestUnicidad:
    def test_serial_de_objeto_externo_es_unico(self, db):
        """En un esquema creado desde el modelo, el serial duplicado se
        rechaza. (En bases migradas por ALTER la restriccion falta: eso se
        corrige en la migracion, ver reporte.)"""
        db.session.add(ObjetoExterno(descripcion='Taladro', serial='OBJ-1'))
        db.session.commit()
        db.session.add(ObjetoExterno(descripcion='Otro taladro', serial='OBJ-1'))
        try:
            db.session.commit()
            raise AssertionError('El serial duplicado no fue rechazado')
        except IntegrityError:
            db.session.rollback()
