"""Pruebas del control de acceso: permisos, coherencia de movimientos y equipos."""
from app.models.accesos import Acceso, Auditoria
from app.models.entidades import Equipo


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


class TestPermisos:
    def test_aprendiz_no_entra_al_escaner(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _entrar(client, aprendiz)
        r = client.get('/porteria/scanner', follow_redirects=False)
        assert r.status_code == 302
        assert '/usuarios/profile' in r.headers['Location']

    def test_celador_entra_al_escaner(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)
        assert client.get('/porteria/scanner').status_code == 200

    def test_aprendiz_no_registra_movimientos(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _entrar(client, aprendiz)
        r = client.post(f'/porteria/register_movement/{aprendiz.id}/Entrada',
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 403

    def test_aprendiz_no_gestiona_asistencia(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _entrar(client, aprendiz)
        r = client.get('/usuarios/asistencia', follow_redirects=False)
        assert r.status_code == 302

    def test_celador_no_entra_a_gestion_de_usuarios(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        _entrar(client, celador)
        r = client.get('/usuarios/admin_gestion', follow_redirects=False)
        assert r.status_code == 302


class TestCoherenciaDeMovimientos:
    """Antes solo las entidades validaban coherencia; las personas no.

    Se podian registrar dos entradas seguidas o la salida de alguien que nunca
    entro, sin ninguna alerta ni traza.
    """

    def _preparar(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                                 documento='123123')
        _entrar(client, celador)
        return celador, aprendiz

    def test_entrada_valida_se_registra(self, client, crear_usuario):
        _, aprendiz = self._preparar(client, crear_usuario)
        r = client.post(f'/porteria/register_movement/{aprendiz.id}/Entrada',
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200
        assert Acceso.query.filter_by(referencia_id=aprendiz.id,
                                      tipo='Entrada').count() == 1

    def test_doble_entrada_se_rechaza_y_se_audita(self, client, crear_usuario):
        _, aprendiz = self._preparar(client, crear_usuario)
        client.post(f'/porteria/register_movement/{aprendiz.id}/Entrada',
                    headers={'X-Requested-With': 'XMLHttpRequest'})
        r = client.post(f'/porteria/register_movement/{aprendiz.id}/Entrada',
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 409
        assert Acceso.query.filter_by(referencia_id=aprendiz.id,
                                      tipo='Entrada').count() == 1
        assert Auditoria.query.filter_by(
            accion='Inconsistencia de Acceso Detectada').count() == 1

    def test_salida_sin_entrada_se_rechaza(self, client, crear_usuario):
        _, aprendiz = self._preparar(client, crear_usuario)
        r = client.post(f'/porteria/register_movement/{aprendiz.id}/Salida',
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 409
        assert Acceso.query.filter_by(referencia_id=aprendiz.id).count() == 0

    def test_movimiento_invalido_se_rechaza(self, client, crear_usuario):
        _, aprendiz = self._preparar(client, crear_usuario)
        r = client.post(f'/porteria/register_movement/{aprendiz.id}/Teletransporte',
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400

    def test_entidad_inventada_no_crea_registro(self, client, crear_usuario):
        self._preparar(client, crear_usuario)
        r = client.post('/porteria/register_movement_entidad/Fantasma/99999/LoQueSea',
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400
        assert Acceso.query.filter_by(tipo_referencia='Fantasma').count() == 0

    def test_el_acceso_registra_quien_lo_hizo(self, client, crear_usuario):
        celador, aprendiz = self._preparar(client, crear_usuario)
        client.post(f'/porteria/register_movement/{aprendiz.id}/Entrada',
                    headers={'X-Requested-With': 'XMLHttpRequest'})
        acceso = Acceso.query.filter_by(referencia_id=aprendiz.id).first()
        assert acceso.operador_id == celador.id


class TestEquipos:
    def test_no_se_pueden_marcar_equipos_de_otro(self, client, crear_usuario, db):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz', documento='111')
        beto = crear_usuario(correo='beto@sena.edu.co', cargo='Aprendiz', documento='222')

        equipo_de_beto = Equipo(nombre='Portatil de Beto', usuario_id=beto.id,
                                tipo='Portatil', estado='Afuera')
        db.session.add(equipo_de_beto)
        db.session.commit()

        _entrar(client, celador)
        client.post(f'/porteria/register_movement/{ana.id}/Entrada',
                    data={'equipos_ids': str(equipo_de_beto.id)},
                    headers={'X-Requested-With': 'XMLHttpRequest'})

        db.session.refresh(equipo_de_beto)
        assert equipo_de_beto.estado == 'Afuera', 'no debe cambiar el equipo ajeno'

    def test_equipo_propio_cambia_de_estado(self, client, crear_usuario, db):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz', documento='111')
        equipo = Equipo(nombre='Portatil de Ana', usuario_id=ana.id,
                        tipo='Portatil', estado='Afuera')
        db.session.add(equipo)
        db.session.commit()

        _entrar(client, celador)
        client.post(f'/porteria/register_movement/{ana.id}/Entrada',
                    data={'equipos_ids': str(equipo.id)},
                    headers={'X-Requested-With': 'XMLHttpRequest'})

        db.session.refresh(equipo)
        assert equipo.estado == 'Adentro'

    def test_no_se_puede_borrar_el_equipo_de_otro(self, client, crear_usuario, db):
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz', documento='111')
        beto = crear_usuario(correo='beto@sena.edu.co', cargo='Aprendiz', documento='222')
        equipo = Equipo(nombre='Portatil de Beto', usuario_id=beto.id, tipo='Portatil')
        db.session.add(equipo)
        db.session.commit()
        equipo_id = equipo.id

        _entrar(client, ana)
        r = client.post(f'/equipos/delete/{equipo_id}',
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400
        assert db.session.get(Equipo, equipo_id) is not None

    def test_borrar_por_get_ya_no_funciona(self, client, crear_usuario, db):
        # Era una ruta GET: bastaba con que la victima cargara una imagen
        # apuntando a esta URL para que perdiera su equipo.
        ana = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz', documento='111')
        equipo = Equipo(nombre='Portatil de Ana', usuario_id=ana.id, tipo='Portatil')
        db.session.add(equipo)
        db.session.commit()
        equipo_id = equipo.id

        _entrar(client, ana)
        assert client.get(f'/equipos/delete/{equipo_id}').status_code == 405
        assert db.session.get(Equipo, equipo_id) is not None
