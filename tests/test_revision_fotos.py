"""Pruebas de la cola de aprobación de fotos de perfil.

Ningún análisis de imagen puede confirmar que la persona de la foto sea quien
dice ser: eso lo aprueba un administrador. Hasta entonces el carnet digital no
se activa, que es lo que le da valor a la verificación en portería.
"""
import os

from app.models.accesos import Auditoria
from app.models.usuarios import (
    ESTADO_APROBADA,
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADA,
    ESTADO_SIN_FOTO,
    Usuario,
)


from app.utils.fotos import carpeta_fotos

def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


def _crear_ficha(db, numero='2999999', programa='Análisis y Desarrollo de Software'):
    from datetime import date

    from app.models.fichas import Ficha
    ficha = Ficha(numero=numero, programa=programa,
                  fecha_finalizacion=date(2027, 6, 30))
    db.session.add(ficha)
    db.session.commit()
    return ficha


def _con_foto(usuario, db, app, estado=ESTADO_PENDIENTE):
    """Le pone al usuario una foto en disco y el estado indicado."""
    carpeta = carpeta_fotos()
    os.makedirs(carpeta, exist_ok=True)
    nombre = f'user_{usuario.id}.jpg'
    with open(os.path.join(carpeta, nombre), 'wb') as f:
        f.write(b'contenido de prueba')
    usuario.foto = nombre
    usuario.foto_estado = estado
    db.session.commit()
    return os.path.join(carpeta, nombre)


class TestAcceso:
    def test_un_aprendiz_no_entra_a_la_cola(self, client, crear_usuario):
        aprendiz = crear_usuario(correo='ap@sena.edu.co', cargo='Aprendiz')
        _entrar(client, aprendiz)
        r = client.get('/usuarios/admin/fotos', follow_redirects=False)
        assert r.status_code == 302

    def test_un_celador_tampoco(self, client, crear_usuario):
        celador = crear_usuario(correo='cel@sena.edu.co', cargo='Celador',
                                documento='777')
        _entrar(client, celador)
        r = client.get('/usuarios/admin/fotos', follow_redirects=False)
        assert r.status_code == 302

    def test_un_aprendiz_no_puede_aprobar_su_propia_foto(self, client, app,
                                                         crear_usuario, db):
        aprendiz = crear_usuario(correo='ap@sena.edu.co', cargo='Aprendiz')
        ruta = _con_foto(aprendiz, db, app)
        try:
            _entrar(client, aprendiz)
            r = client.post(f'/usuarios/api/admin/fotos/{aprendiz.id}/revisar',
                            json={'decision': 'aprobar'},
                            headers={'X-CSRFToken': 'x'})
            assert r.status_code == 403
            db.session.refresh(aprendiz)
            assert aprendiz.foto_estado == ESTADO_PENDIENTE
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_el_admin_ve_la_cola(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        _entrar(client, admin)
        assert client.get('/usuarios/admin/fotos').status_code == 200


class TestAprobacion:
    def _preparar(self, client, app, crear_usuario, db, estado=ESTADO_PENDIENTE):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111', perfil_completo=False)
        ruta = _con_foto(persona, db, app, estado)
        _entrar(client, admin)
        return admin, persona, ruta

    def test_aprobar_deja_la_foto_aprobada_y_audita(self, client, app,
                                                    crear_usuario, db):
        admin, persona, ruta = self._preparar(client, app, crear_usuario, db)
        try:
            r = client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                            json={'decision': 'aprobar'})
            assert r.status_code == 200
            db.session.refresh(persona)
            assert persona.foto_estado == ESTADO_APROBADA
            assert persona.foto_revisada_por == admin.id
            assert persona.foto_fecha_revision is not None
            # La foto aprobada se conserva.
            assert os.path.isfile(ruta)
            assert Auditoria.query.filter_by(
                accion='Foto de perfil aprobada').count() == 1
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_rechazar_exige_motivo(self, client, app, crear_usuario, db):
        # Sin motivo, la persona no sabe qué corregir y volverá a subir lo mismo.
        _, persona, ruta = self._preparar(client, app, crear_usuario, db)
        try:
            r = client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                            json={'decision': 'rechazar', 'motivo': '   '})
            assert r.status_code == 400
            db.session.refresh(persona)
            assert persona.foto_estado == ESTADO_PENDIENTE
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_rechazar_borra_la_foto_y_guarda_el_motivo(self, client, app,
                                                       crear_usuario, db):
        _, persona, ruta = self._preparar(client, app, crear_usuario, db)
        motivo = 'La foto no corresponde a la persona registrada.'
        try:
            r = client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                            json={'decision': 'rechazar', 'motivo': motivo})
            assert r.status_code == 200
            db.session.refresh(persona)
            assert persona.foto_estado == ESTADO_RECHAZADA
            assert persona.foto_motivo == motivo
            assert persona.perfil_completo is False
            # No tiene sentido conservar una imagen que no corresponde a la
            # persona: se borra del disco (minimización, Ley 1581).
            assert persona.foto is None
            assert not os.path.isfile(ruta)
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_decision_invalida_se_rechaza(self, client, app, crear_usuario, db):
        _, persona, ruta = self._preparar(client, app, crear_usuario, db)
        try:
            r = client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                            json={'decision': 'aprobar_a_medias'})
            assert r.status_code == 400
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_usuario_inexistente(self, client, app, crear_usuario, db):
        self._preparar(client, app, crear_usuario, db)
        r = client.post('/usuarios/api/admin/fotos/99999/revisar',
                        json={'decision': 'aprobar'})
        assert r.status_code == 404


class TestCarnet:
    """El codigo de barras es la llave de entrada: no debe existir sin foto
    aprobada."""

    def _subir_datos(self, client, ficha_id):
        # El aprendiz ya no teclea programa ni ficha: elige una ficha y hereda
        # de ella el programa y la fecha de finalizacion.
        return client.post('/usuarios/update_profile',
                           data={'documento': '1098765432', 'tipo_documento': 'CC',
                                 'tipo_sangre': 'O+', 'ficha_id': str(ficha_id)},
                           headers={'X-Requested-With': 'XMLHttpRequest'})

    def test_sin_aprobar_no_hay_carnet(self, client, app, crear_usuario, db):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111', perfil_completo=False)
        ficha = _crear_ficha(db)
        ruta = _con_foto(persona, db, app, ESTADO_PENDIENTE)
        try:
            _entrar(client, persona)
            self._subir_datos(client, ficha.id)
            db.session.refresh(persona)
            assert persona.perfil_completo is False, (
                'el carnet no debe activarse con la foto sin revisar')
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_con_la_foto_aprobada_si_hay_carnet(self, client, app,
                                                crear_usuario, db):
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111', perfil_completo=False)
        ficha = _crear_ficha(db)
        ruta = _con_foto(persona, db, app, ESTADO_APROBADA)
        try:
            _entrar(client, persona)
            self._subir_datos(client, ficha.id)
            db.session.refresh(persona)
            assert persona.perfil_completo is True
            # Y entonces sí aparece el código de barras en el carnet.
            pagina = client.get('/usuarios/profile').data
            assert b'carnet-of-barras-caja' in pagina
            assert b'<svg' in pagina
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)


class TestEstadoInicial:
    def test_un_usuario_nuevo_empieza_sin_foto(self, crear_usuario):
        persona = crear_usuario(correo='nueva@sena.edu.co')
        assert persona.foto_estado == ESTADO_SIN_FOTO
        assert persona.foto_aprobada is False
        assert persona.foto_pendiente is False


class TestAvisoAlCelador:
    def test_la_api_del_escaner_dice_si_la_foto_esta_aprobada(self, client, app,
                                                              crear_usuario, db):
        # Si la foto no está verificada, el celador debe pedir el documento
        # físico en vez de fiarse de ella.
        celador = crear_usuario(correo='cel@sena.edu.co', cargo='Celador',
                                documento='777')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111')
        ruta = _con_foto(persona, db, app, ESTADO_PENDIENTE)
        try:
            _entrar(client, celador)
            datos = client.get('/porteria/api/verify/111').get_json()
            assert datos['found'] is True
            assert datos['foto_aprobada'] is False

            persona.foto_estado = ESTADO_APROBADA
            db.session.commit()
            datos = client.get('/porteria/api/verify/111').get_json()
            assert datos['foto_aprobada'] is True
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)


class TestPaginaDeError:
    def test_un_404_no_revienta_para_un_usuario_autenticado(self, client, crear_usuario):
        """`request.endpoint` es None cuando la URL no existe. El menú lateral
        hacía `'x' in request.endpoint` y eso convertía cualquier 404 en un 500,
        dejando al usuario ante la página de error cruda de Flask."""
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        _entrar(client, admin)
        r = client.get('/esta-ruta-no-existe')
        assert r.status_code == 404
        assert 'Página no encontrada' in r.get_data(as_text=True)
