"""Pruebas de minimización de datos (Ley 1581 de 2012, art. 4 lit. c).

Cubren cinco correcciones puntuales:
  - la bandeja del asesor y el hilo abierto ya no muestran la cédula completa
    ni el correo, pero portería sigue viendo el documento completo (lo
    necesita para identificar en la puerta);
  - la cola de revisión de fotos ya no lista todo sin tope ni muestra correo;
  - exportar el histórico de portería exige un rango de fechas y deja
    constancia en la auditoría;
  - la versión HTML del historial por persona tiene el mismo límite de
    peticiones que su versión de datos;
  - aprobar una foto ya aprobada es idempotente: no reenvía correo ni añade
    otro mensaje automático.
"""
import os
from datetime import datetime, timedelta

from app import db
from app.models.accesos import Acceso, Auditoria
from app.models.mensajes import Mensaje
from app.models.usuarios import ESTADO_APROBADA, ESTADO_PENDIENTE, ESTADO_SIN_FOTO
from app.utils.fotos import carpeta_fotos
from app.utils.limitador import LIMITES


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


def _con_foto(usuario, estado=ESTADO_PENDIENTE):
    carpeta = carpeta_fotos()
    os.makedirs(carpeta, exist_ok=True)
    nombre = f'user_{usuario.id}.jpg'
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, 'wb') as f:
        f.write(b'prueba')
    usuario.foto = nombre
    usuario.foto_estado = estado
    db.session.commit()
    return ruta


class TestDocumentoEnmascaradoParaElAsesor:
    """El asesor no necesita la cédula completa para responder una duda de
    perfil o de foto; portería sí la necesita para identificar en la
    puerta."""

    def test_la_bandeja_del_asesor_no_muestra_la_cedula_completa(self, client,
                                                                  crear_usuario):
        asesor = crear_usuario(correo='adm@sena.edu.co', cargo='Administrativo',
                               documento='999888')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='1098765432')
        _entrar(client, persona)
        client.post('/usuarios/mensajes/enviar', data={'texto': 'Ayuda con mi foto'})
        client.get('/auth/logout')

        _entrar(client, asesor)
        cuerpo = client.get('/usuarios/admin/mensajes').get_data(as_text=True)
        assert '1098765432' not in cuerpo
        assert '5432' in cuerpo  # quedan visibles los últimos cuatro dígitos

    def test_el_hilo_abierto_no_muestra_cedula_completa_ni_correo(self, client,
                                                                   crear_usuario):
        asesor = crear_usuario(correo='adm@sena.edu.co', cargo='Administrativo',
                               documento='999888')
        persona = crear_usuario(correo='ana.secreta@sena.edu.co', cargo='Aprendiz',
                                documento='1098765432')
        _entrar(client, persona)
        client.post('/usuarios/mensajes/enviar', data={'texto': 'Ayuda con mi foto'})
        client.get('/auth/logout')

        _entrar(client, asesor)
        cuerpo = client.get(f'/usuarios/admin/mensajes/{persona.id}').get_data(as_text=True)
        assert '1098765432' not in cuerpo
        assert '5432' in cuerpo
        assert 'ana.secreta@sena.edu.co' not in cuerpo

    def test_porteria_si_ve_el_documento_completo(self, client, crear_usuario):
        """Portería identifica a la persona en la puerta: ahí el documento
        completo sí hace falta y no se toca."""
        celador = crear_usuario(correo='cel@sena.edu.co', cargo='Celador',
                                documento='777777')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='1098765432')
        db.session.add(Acceso(punto_id=1, referencia_id=persona.id,
                              tipo_referencia='Usuario', tipo='Entrada'))
        db.session.commit()

        _entrar(client, celador)
        cuerpo = client.get('/porteria/dashboard?tab=history').get_data(as_text=True)
        assert '1098765432' in cuerpo


class TestColaDeRevisionDeFotos:
    def test_no_muestra_el_correo_en_las_tarjetas(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        persona = crear_usuario(correo='correo.secreto@sena.edu.co',
                                cargo='Aprendiz', documento='111')
        ruta = _con_foto(persona)
        try:
            _entrar(client, admin)
            cuerpo = client.get('/usuarios/admin/fotos?estado=todos').get_data(as_text=True)
            assert 'correo.secreto@sena.edu.co' not in cuerpo
            assert persona.nombre in cuerpo
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_la_lista_esta_paginada(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        rutas = []
        try:
            for i in range(30):
                persona = crear_usuario(correo=f'foto{i}@sena.edu.co',
                                        cargo='Aprendiz', documento=f'50000{i:03d}')
                rutas.append(_con_foto(persona, estado=ESTADO_APROBADA))

            _entrar(client, admin)
            r = client.get('/usuarios/admin/fotos?estado=todos')
            assert r.status_code == 200
            cuerpo = r.get_data(as_text=True)
            # Con 30 usuarios y una pagina de 24, debe existir un enlace a la
            # pagina siguiente: si no hubiera paginacion, las 30 tarjetas
            # saldrian todas de una vez.
            assert 'pagina=2' in cuerpo
        finally:
            for ruta in rutas:
                if os.path.isfile(ruta):
                    os.remove(ruta)


class TestExportacionExigeRangoDeFechas:
    def _preparar(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111', programa='ADSO', ficha='2999999')
        db.session.add(Acceso(punto_id=1, referencia_id=persona.id,
                              tipo_referencia='Usuario', tipo='Entrada'))
        db.session.commit()
        _entrar(client, admin)
        return admin, persona

    def test_sin_fechas_no_exporta_y_avisa(self, client, crear_usuario):
        self._preparar(client, crear_usuario)
        r = client.get('/porteria/export_dashboard', follow_redirects=False)
        assert r.status_code == 302
        assert 'text/csv' not in (r.content_type or '')
        assert Auditoria.query.filter_by(
            accion='Exportación de histórico de accesos').count() == 0

    def test_con_fechas_exporta_y_deja_constancia_en_auditoria(self, client,
                                                                crear_usuario):
        admin, persona = self._preparar(client, crear_usuario)
        hoy = datetime.now().strftime('%Y-%m-%d')
        manana = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        r = client.get('/porteria/export_dashboard'
                       f'?fecha_inicio={hoy}&fecha_fin={manana}')
        assert r.status_code == 200
        assert 'text/csv' in r.content_type
        cuerpo = r.get_data(as_text=True)
        assert persona.documento in cuerpo

        auditoria = Auditoria.query.filter_by(
            accion='Exportación de histórico de accesos').first()
        assert auditoria is not None
        assert auditoria.usuario_id == admin.id
        assert hoy in auditoria.detalles

    def test_rango_invertido_se_rechaza(self, client, crear_usuario):
        self._preparar(client, crear_usuario)
        hoy = datetime.now().strftime('%Y-%m-%d')
        ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        r = client.get('/porteria/export_dashboard'
                       f'?fecha_inicio={hoy}&fecha_fin={ayer}', follow_redirects=False)
        assert r.status_code == 302
        assert Auditoria.query.filter_by(
            accion='Exportación de histórico de accesos').count() == 0


class TestLimiteDelHistorialHTML:
    def test_el_historial_html_esta_en_el_catalogo_de_limites(self):
        declarados = {endpoint for endpoint, _, _ in LIMITES}
        assert 'porteria.historial_persona' in declarados

    def test_el_escaner_de_porteria_sigue_libre(self):
        """No se toco la lista de exentos: el celador no debe quedar limitado."""
        from app.utils.limitador import EXENTOS
        assert 'porteria.scanner' in EXENTOS
        assert 'porteria.api_verify' in EXENTOS
        assert 'porteria.register_movement' in EXENTOS


class TestAprobacionIdempotente:
    def test_aprobar_dos_veces_no_duplica_mensajes(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111', perfil_completo=False)
        ruta = _con_foto(persona, estado=ESTADO_PENDIENTE)
        try:
            _entrar(client, admin)
            primero = client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                                  json={'decision': 'aprobar'})
            assert primero.status_code == 200
            assert Mensaje.query.filter_by(usuario_id=persona.id).count() == 1

            segundo = client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                                  json={'decision': 'aprobar'})
            assert segundo.status_code == 200
            # Ni el mensaje automático ni la auditoria se duplican.
            assert Mensaje.query.filter_by(usuario_id=persona.id).count() == 1
            assert Auditoria.query.filter_by(
                accion='Foto de perfil aprobada').count() == 1
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_la_foto_sigue_aprobada_tras_el_segundo_intento(self, client,
                                                             crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador', documento='999')
        persona = crear_usuario(correo='ana@sena.edu.co', cargo='Aprendiz',
                                documento='111', perfil_completo=False)
        ruta = _con_foto(persona, estado=ESTADO_APROBADA)
        try:
            _entrar(client, admin)
            r = client.post(f'/usuarios/api/admin/fotos/{persona.id}/revisar',
                            json={'decision': 'aprobar'})
            assert r.status_code == 200
            assert r.get_json()['status'] == 'success'
            db.session.refresh(persona)
            assert persona.foto_estado == ESTADO_APROBADA
            assert os.path.isfile(ruta)
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)
