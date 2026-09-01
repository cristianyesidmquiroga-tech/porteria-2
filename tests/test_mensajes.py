"""Pruebas del canal de mensajes entre administrador y usuario.

Quien se queda sin carnet por una foto rechazada necesita poder preguntar
dentro del sistema; si no, se queda bloqueado sin saber qué hacer.
"""
import os

from app.models.mensajes import Mensaje


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


def _con_foto(usuario, db, app):
    carpeta = os.path.join(app.root_path, 'static', 'uploads', 'profiles')
    os.makedirs(carpeta, exist_ok=True)
    nombre = f'user_{usuario.id}.jpg'
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, 'wb') as f:
        f.write(b'prueba')
    usuario.foto = nombre
    usuario.foto_estado = 'pendiente'
    db.session.commit()
    return ruta


class TestUsuarioEscribe:
    def test_puede_enviar_un_mensaje(self, client, crear_usuario, db):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _entrar(client, persona)
        r = client.post('/usuarios/mensajes/enviar',
                        data={'texto': 'No puedo subir mi foto, me sale error.'},
                        follow_redirects=False)
        assert r.status_code == 302
        mensaje = Mensaje.query.filter_by(usuario_id=persona.id).first()
        assert mensaje is not None
        assert mensaje.autor_id == persona.id
        assert mensaje.autor_es_admin is False

    def test_un_mensaje_vacio_no_se_guarda(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co')
        _entrar(client, persona)
        client.post('/usuarios/mensajes/enviar', data={'texto': '   '})
        assert Mensaje.query.count() == 0

    def test_solo_ve_su_propio_hilo(self, client, crear_usuario, db):
        ana = crear_usuario(correo='ana@sena.edu.co', documento='111')
        beto = crear_usuario(correo='beto@sena.edu.co', documento='222')
        _entrar(client, beto)
        client.post('/usuarios/mensajes/enviar', data={'texto': 'Mensaje de Beto'})
        client.get('/auth/logout')

        _entrar(client, ana)
        cuerpo = client.get('/usuarios/mensajes').get_data(as_text=True)
        assert 'Mensaje de Beto' not in cuerpo

    def test_no_puede_entrar_a_la_bandeja_del_admin(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co')
        _entrar(client, persona)
        r = client.get('/usuarios/admin/mensajes', follow_redirects=False)
        assert r.status_code == 302

    def test_no_puede_escribirle_a_otro_como_si_fuera_admin(self, client,
                                                            crear_usuario):
        ana = crear_usuario(correo='ana@sena.edu.co', documento='111')
        beto = crear_usuario(correo='beto@sena.edu.co', documento='222')
        _entrar(client, ana)
        r = client.post(f'/usuarios/api/admin/mensajes/{beto.id}',
                        json={'texto': 'Suplantando a un administrador'})
        assert r.status_code == 403
        assert Mensaje.query.count() == 0


class TestAdminResponde:
    def _preparar(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111')
        return admin, persona

    def test_el_admin_escribe_a_una_persona(self, client, crear_usuario):
        admin, persona = self._preparar(client, crear_usuario)
        _entrar(client, admin)
        r = client.post(f'/usuarios/api/admin/mensajes/{persona.id}',
                        json={'texto': 'Te falta el tipo de sangre en el perfil.'})
        assert r.status_code == 200
        mensaje = Mensaje.query.filter_by(usuario_id=persona.id).first()
        assert mensaje.autor_id == admin.id
        assert mensaje.autor_es_admin is True

    def test_la_persona_ve_lo_que_le_escribio_el_admin(self, client, crear_usuario):
        admin, persona = self._preparar(client, crear_usuario)
        _entrar(client, admin)
        client.post(f'/usuarios/api/admin/mensajes/{persona.id}',
                    json={'texto': 'Revisa tu ficha, está mal escrita.'})
        client.get('/auth/logout')

        _entrar(client, persona)
        cuerpo = client.get('/usuarios/mensajes').get_data(as_text=True)
        assert 'Revisa tu ficha' in cuerpo

    def test_abrir_el_hilo_marca_los_mensajes_como_leidos(self, client,
                                                          crear_usuario, db):
        admin, persona = self._preparar(client, crear_usuario)
        _entrar(client, admin)
        client.post(f'/usuarios/api/admin/mensajes/{persona.id}',
                    json={'texto': 'Hola'})
        client.get('/auth/logout')

        assert Mensaje.query.filter_by(leido=False).count() == 1
        _entrar(client, persona)
        client.get('/usuarios/mensajes')
        assert Mensaje.query.filter_by(leido=False).count() == 0

    def test_escribir_a_alguien_que_no_existe(self, client, crear_usuario):
        admin, _ = self._preparar(client, crear_usuario)
        _entrar(client, admin)
        r = client.post('/usuarios/api/admin/mensajes/99999',
                        json={'texto': 'Hola'})
        assert r.status_code == 404


class TestRechazoDejaMensaje:
    def test_al_rechazar_la_foto_queda_el_motivo_en_el_hilo(self, client, app,
                                                            crear_usuario, db):
        """El correo se puede perder o ir a spam; el hilo vive dentro del
        sistema y ahí mismo la persona puede responder."""
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111')
        ruta = _con_foto(persona, db, app)
        motivo = 'El rostro está tapado por una gorra.'
        try:
            _entrar(client, admin)
            r = client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                            json={'decision': 'rechazar', 'motivo': motivo})
            assert r.status_code == 200

            mensaje = Mensaje.query.filter_by(usuario_id=persona.id).first()
            assert mensaje is not None
            assert motivo in mensaje.texto
            assert mensaje.automatico is True
            # Y le dice explícitamente que puede responder ahí.
            assert 'respóndeme' in mensaje.texto.lower()
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_al_aprobar_tambien_queda_constancia(self, client, app,
                                                 crear_usuario, db):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111')
        ruta = _con_foto(persona, db, app)
        try:
            _entrar(client, admin)
            client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                        json={'decision': 'aprobar'})
            mensaje = Mensaje.query.filter_by(usuario_id=persona.id).first()
            assert mensaje is not None
            assert 'aprobada' in mensaje.texto.lower()
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)


class TestCentroDeAyuda:
    def test_cualquiera_puede_ver_las_preguntas_frecuentes(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _entrar(client, persona)
        cuerpo = client.get('/usuarios/ayuda').get_data(as_text=True)
        assert '¿Por qué no me aparece el código de barras?' in cuerpo
        assert 'Hablar con un asesor' in cuerpo

    def test_contactar_abre_la_conversacion(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz')
        _entrar(client, persona)
        client.post('/usuarios/ayuda/contactar',
                    data={'asunto': 'Problema con mi foto de perfil',
                          'detalle': 'Me dice que está borrosa pero se ve bien.'})
        mensaje = Mensaje.query.filter_by(usuario_id=persona.id).first()
        assert mensaje is not None
        # El asunto va dentro del texto para que el asesor sepa de qué se trata
        # sin tener que preguntar.
        assert 'Problema con mi foto de perfil' in mensaje.texto
        assert 'borrosa' in mensaje.texto

    def test_sin_detalle_no_se_abre_nada(self, client, crear_usuario):
        persona = crear_usuario(correo='ana@sena.edu.co')
        _entrar(client, persona)
        client.post('/usuarios/ayuda/contactar',
                    data={'asunto': 'Otro', 'detalle': '  '})
        assert Mensaje.query.count() == 0


class TestQuienPuedeAsesorar:
    """Quién atiende el centro de ayuda se define en CARGOS_ASESORES."""

    def test_el_administrativo_puede_asesorar(self, client, crear_usuario):
        # No solo el rol Admin: en el centro hay personal administrativo que
        # atiende a los aprendices a diario. Si solo asesorara una persona,
        # quien se queda sin carnet no puede entrar hasta que esa persona lea.
        asesor = crear_usuario(correo='adm@sena.edu.co', cargo='Administrativo',
                               documento='888')
        assert asesor.puede_asesorar is True
        _entrar(client, asesor)
        assert client.get('/usuarios/admin/mensajes').status_code == 200

    def test_el_aprendiz_no_puede_asesorar(self, crear_usuario):
        assert crear_usuario(correo='ap@sena.edu.co', cargo='Aprendiz').puede_asesorar is False

    def test_el_celador_no_puede_asesorar(self, crear_usuario):
        celador = crear_usuario(correo='cel@sena.edu.co', cargo='Celador', documento='777')
        assert celador.puede_asesorar is False

    def test_el_instructor_no_puede_asesorar(self, crear_usuario):
        inst = crear_usuario(correo='ins@sena.edu.co', cargo='Instructor', documento='666')
        assert inst.puede_asesorar is False
