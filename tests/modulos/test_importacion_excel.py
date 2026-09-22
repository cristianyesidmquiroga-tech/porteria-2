"""Pruebas de la importación masiva de usuarios desde Excel.

Es la ruta con más lógica de seguridad del proyecto: quien PREPARA la hoja no
es quien la sube, así que el archivo decide nombres, correos, documentos,
cargos y roles de mucha gente de una vez. Aquí se comprueba lo que no puede
fallar en silencio:

  - el documento que se guarda es el mismo que la persona teclea en portería,
  - nadie se hace administrador desde una hoja de cálculo,
  - una fila mala no se lleva por delante al resto del lote,
  - cada cuenta nace con una contraseña temporal distinta,
  - y todo queda en la auditoría.
"""
import io

import pandas as pd
import pytest

from app.models.accesos import Auditoria
from app.models.usuarios import Usuario


def excel_de(filas):
    """Construye un .xlsx de verdad en memoria a partir de una lista de dicts.

    Se escribe el archivo y se vuelve a leer por la ruta real (no se simula
    pandas) porque el fallo que se persigue nace justo ahí: al leerlo.
    """
    buffer = io.BytesIO()
    pd.DataFrame(filas).to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


@pytest.fixture
def admin(crear_usuario):
    return crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                         cargo='Administrador', documento='1000000001')


@pytest.fixture
def sesion_admin(client, admin):
    client.post('/auth/login',
                data={'correo': admin.correo, 'password': 'Segura2026'},
                headers={'X-Requested-With': 'XMLHttpRequest'})
    return client


@pytest.fixture
def correos_enviados(monkeypatch):
    """Intercepta el correo de bienvenida y guarda su cuerpo.

    Sirve además para leer la contraseña temporal que se le mandó a cada
    persona, que es el único sitio donde aparece en claro.
    """
    enviados = []

    def _falso(destinatario, asunto, cuerpo_html):
        enviados.append({'para': destinatario, 'cuerpo': cuerpo_html})
        return True

    monkeypatch.setattr('app.utils.email.enviar_correo', _falso)
    return enviados


def importar(cliente, filas, nombre='usuarios.xlsx'):
    return cliente.post('/usuarios/api/admin/importar_usuarios_excel',
                        data={'file': (excel_de(filas), nombre)},
                        content_type='multipart/form-data')


class TestDocumentoNoSeCorrompe:
    def test_una_celda_vacia_no_convierte_los_documentos_en_decimales(
            self, sesion_admin, correos_enviados, db):
        # Con la columna 'Documento' medio vacía, pandas deducía que era de
        # números decimales y el documento llegaba como '1098765432.0'. Ese
        # texto se guardaba tal cual: en portería la persona teclea
        # '1098765432', no coincide con nada, y no puede entrar.
        respuesta = importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co',
             'Documento': 1098765432},
            {'Nombre': 'Beto Gil', 'Correo': 'beto@sena.edu.co',
             'Documento': None},
        ])
        assert respuesta.status_code == 200

        ana = Usuario.query.filter_by(correo='ana@sena.edu.co').first()
        assert ana is not None
        assert ana.documento == '1098765432'
        assert '.' not in ana.documento

        beto = Usuario.query.filter_by(correo='beto@sena.edu.co').first()
        assert beto.documento is None

    def test_la_ficha_tampoco_se_corrompe(self, sesion_admin, correos_enviados):
        # Misma causa que el documento: la ficha se imprime en el carnet.
        importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co',
             'Cargo': 'Aprendiz', 'Ficha': 2894567},
            {'Nombre': 'Beto Gil', 'Correo': 'beto@sena.edu.co',
             'Cargo': 'Aprendiz', 'Ficha': None},
        ])
        ana = Usuario.query.filter_by(correo='ana@sena.edu.co').first()
        assert ana.ficha == '2894567'

    def test_un_documento_invalido_no_se_guarda(self, sesion_admin,
                                                correos_enviados):
        # Guardar un documento con letras o con la longitud equivocada es peor
        # que no guardarlo: nunca va a coincidir con el que se valida en
        # portería. La persona se importa y completa su perfil después.
        respuesta = importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co',
             'Documento': '10A98'},
        ])
        ana = Usuario.query.filter_by(correo='ana@sena.edu.co').first()
        assert ana is not None
        assert ana.documento is None
        avisos = respuesta.get_json()['detalles']['errores']
        assert any('documento' in a.lower() for a in avisos)

    def test_el_documento_se_normaliza_como_en_porteria(self, sesion_admin,
                                                        correos_enviados):
        # Con puntos en la hoja y sin puntos en portería serían dos personas
        # distintas al buscar por documento.
        importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co',
             'Documento': '1.098.765.432'},
        ])
        ana = Usuario.query.filter_by(correo='ana@sena.edu.co').first()
        assert ana.documento == '1098765432'


class TestListaBlancaDeRoles:
    def test_una_fila_que_pide_admin_se_degrada_a_usuario(
            self, sesion_admin, correos_enviados):
        # Quien prepara el Excel no puede repartir acceso total sin que el
        # administrador que sube el archivo se entere.
        respuesta = importar(sesion_admin, [
            {'Nombre': 'Intruso', 'Correo': 'intruso@sena.edu.co',
             'Rol': 'Admin'},
        ])
        creado = Usuario.query.filter_by(correo='intruso@sena.edu.co').first()
        assert creado.rol.nombre == 'Usuario'
        assert creado.es_admin is False
        avisos = respuesta.get_json()['detalles']['errores']
        assert any('rol' in a.lower() for a in avisos)

    def test_un_cargo_inventado_se_degrada_a_aprendiz(self, sesion_admin,
                                                      correos_enviados):
        # El cargo gobierna permisos de portería, asesoría y asistencia.
        importar(sesion_admin, [
            {'Nombre': 'Intruso', 'Correo': 'intruso@sena.edu.co',
             'Cargo': 'Celador Jefe Supremo'},
        ])
        creado = Usuario.query.filter_by(correo='intruso@sena.edu.co').first()
        assert creado.cargo == 'Aprendiz'
        assert creado.puede_operar_porteria is False

    def test_la_importacion_no_la_puede_lanzar_cualquiera(self, client,
                                                          crear_usuario):
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co')
        client.post('/auth/login',
                    data={'correo': aprendiz.correo, 'password': 'Segura2026'},
                    headers={'X-Requested-With': 'XMLHttpRequest'})
        respuesta = importar(client, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co'},
        ])
        assert respuesta.status_code == 403
        assert Usuario.query.filter_by(correo='ana@sena.edu.co').first() is None


class TestFilasProblematicas:
    def test_un_correo_repetido_se_omite_y_el_resto_entra(
            self, sesion_admin, correos_enviados, crear_usuario):
        crear_usuario(correo='ana@sena.edu.co', documento='1098765432')
        respuesta = importar(sesion_admin, [
            {'Nombre': 'Ana Repetida', 'Correo': 'ana@sena.edu.co'},
            {'Nombre': 'Beto Gil', 'Correo': 'beto@sena.edu.co'},
        ])
        detalles = respuesta.get_json()['detalles']
        assert detalles['omitidos'] == 1
        assert detalles['creados'] == 1
        assert Usuario.query.filter_by(correo='beto@sena.edu.co').first() is not None
        # La cuenta que ya existía no se toca.
        assert Usuario.query.filter_by(correo='ana@sena.edu.co').count() == 1

    def test_un_documento_repetido_no_tumba_el_lote(
            self, sesion_admin, correos_enviados, crear_usuario):
        # La columna es única: sin comprobarlo, el choque salta al vaciar la
        # sesión y se lleva por delante a las filas que iban bien.
        crear_usuario(correo='previa@sena.edu.co', documento='1098765432')
        respuesta = importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co',
             'Documento': 1098765432},
            {'Nombre': 'Beto Gil', 'Correo': 'beto@sena.edu.co',
             'Documento': 1012345678},
        ])
        assert respuesta.status_code == 200
        assert Usuario.query.filter_by(correo='ana@sena.edu.co').first().documento is None
        assert Usuario.query.filter_by(correo='beto@sena.edu.co').first().documento == '1012345678'

    def test_una_fila_corrupta_no_impide_que_se_importen_las_demas(
            self, sesion_admin, monkeypatch):
        # Se simula un fallo real de una sola fila (el envío del correo de
        # bienvenida): el lote debe seguir y anotarlo como aviso.
        def _falla_para_beto(destinatario, asunto, cuerpo_html):
            if destinatario == 'beto@sena.edu.co':
                raise RuntimeError('servidor SMTP caido')
            return True

        monkeypatch.setattr('app.utils.email.enviar_correo', _falla_para_beto)
        respuesta = importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co'},
            {'Nombre': 'Beto Gil', 'Correo': 'beto@sena.edu.co'},
            {'Nombre': 'Caro Diaz', 'Correo': 'caro@sena.edu.co'},
        ])
        assert respuesta.status_code == 200
        for correo in ('ana@sena.edu.co', 'beto@sena.edu.co', 'caro@sena.edu.co'):
            assert Usuario.query.filter_by(correo=correo).first() is not None
        assert respuesta.get_json()['detalles']['creados'] == 3

    def test_las_filas_vacias_del_final_se_omiten_sin_avisos(
            self, sesion_admin, correos_enviados):
        respuesta = importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co'},
            {"Nombre": None, "Correo": None, "Documento": 1098765432},
        ])
        detalles = respuesta.get_json()['detalles']
        assert detalles['creados'] == 1
        assert detalles['omitidos'] == 1
        assert detalles['errores'] == []
        # 'nan' es un nombre real si la celda vacía se convierte a texto sin
        # mirar si estaba vacía.
        assert Usuario.query.filter_by(nombre='nan').first() is None


class TestContrasenasTemporales:
    def test_cada_fila_recibe_una_contrasena_distinta(self, sesion_admin,
                                                      correos_enviados):
        # Una contraseña fija escrita en el código deja entrar a cualquier
        # cuenta importada antes de que su dueño la use por primera vez.
        importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co'},
            {'Nombre': 'Beto Gil', 'Correo': 'beto@sena.edu.co'},
        ])
        ana = Usuario.query.filter_by(correo='ana@sena.edu.co').first()
        beto = Usuario.query.filter_by(correo='beto@sena.edu.co').first()

        # La contraseña de Ana no sirve para entrar como Beto.
        clave_ana = _clave_del_correo(correos_enviados, 'ana@sena.edu.co')
        clave_beto = _clave_del_correo(correos_enviados, 'beto@sena.edu.co')
        assert clave_ana and clave_beto
        assert clave_ana != clave_beto
        assert ana.check_password(clave_ana)
        assert beto.check_password(clave_beto)
        assert not beto.check_password(clave_ana)

        # Y tampoco hay un valor fijo escrito en el código.
        for previsible in ('sena123', 'Sena123*', '123456', 'password',
                           'cambiar123', 'Temporal123'):
            assert not ana.check_password(previsible)

        assert ana.debe_cambiar_contrasena is True

    def test_los_hashes_no_se_repiten(self, sesion_admin, correos_enviados):
        importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co'},
            {'Nombre': 'Beto Gil', 'Correo': 'beto@sena.edu.co'},
        ])
        claves = {u.contraseña for u in Usuario.query.filter(
            Usuario.correo.in_(['ana@sena.edu.co', 'beto@sena.edu.co']))}
        assert len(claves) == 2


def _clave_del_correo(enviados, destinatario):
    """Saca la contraseña temporal del cuerpo del correo de bienvenida."""
    import re
    for mensaje in enviados:
        if mensaje['para'] == destinatario:
            encontrado = re.search(
                r'Contraseña temporal:</strong>\s*(.+?)</p>', mensaje['cuerpo'])
            return encontrado.group(1).strip() if encontrado else None
    return None


class TestAuditoria:
    def test_el_lote_queda_registrado(self, sesion_admin, correos_enviados,
                                      admin):
        # El alta individual sí se auditaba; la masiva no dejaba ningún rastro,
        # justo donde se reparten roles y cargos a mucha gente de una vez.
        importar(sesion_admin, [
            {'Nombre': 'Ana Ruiz', 'Correo': 'ana@sena.edu.co'},
            {'Nombre': 'Beto Gil', 'Correo': 'beto@sena.edu.co'},
        ], nombre='aprendices_2026.xlsx')

        registro = Auditoria.query.filter_by(
            accion='Importación masiva de usuarios').first()
        assert registro is not None
        assert registro.usuario_id == admin.id
        assert 'aprendices_2026.xlsx' in registro.detalles
        assert 'Creados: 2' in registro.detalles
