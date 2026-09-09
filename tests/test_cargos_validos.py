"""Pruebas de los cargos institucionales admitidos por el sistema."""
import io

import pandas as pd

from app.models.usuarios import CARGOS_VALIDOS, Rol, Usuario
from app.utils.carnet import (
    PERFIL_CONTRATISTA,
    PERFIL_FUNCIONARIO,
    PERFIL_SUBDIRECTOR,
    perfil_de_cargo,
)


NUEVOS_CARGOS = {
    'Coordinacion': PERFIL_FUNCIONARIO,
    'Subdirector': PERFIL_SUBDIRECTOR,
    'Contratista': PERFIL_CONTRATISTA,
    'Funcionario': PERFIL_FUNCIONARIO,
}


def _excel_de(filas):
    buffer = io.BytesIO()
    pd.DataFrame(filas).to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


def _iniciar_sesion_admin(client, admin):
    client.post('/auth/login',
                data={'correo': admin.correo, 'password': 'Segura2026'},
                headers={'X-Requested-With': 'XMLHttpRequest'})


class TestCargosInstitucionales:
    def test_los_cuatro_cargos_estan_en_la_lista_blanca_y_en_el_carnet(self):
        for cargo, perfil in NUEVOS_CARGOS.items():
            assert cargo in CARGOS_VALIDOS
            assert perfil_de_cargo(cargo) == perfil

    def test_el_panel_expone_la_lista_blanca(self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador')
        _iniciar_sesion_admin(client, admin)

        respuesta = client.get('/usuarios/admin_gestion')
        pagina = respuesta.data.decode('utf-8')
        assert respuesta.status_code == 200
        for cargo in NUEVOS_CARGOS:
            assert f'value="{cargo}"' in pagina

    def test_crear_y_editar_rechazan_cargos_fuera_de_la_lista(
            self, client, crear_usuario, db):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador')
        _iniciar_sesion_admin(client, admin)
        rol_usuario = Rol.query.filter_by(nombre='Usuario').first()

        respuesta = client.post('/usuarios/api/admin/crear_usuario', json={
            'nombre': 'Cargo Invalido',
            'correo': 'invalido@sena.edu.co',
            'contraseña': 'Segura2026',
            'rol_id': rol_usuario.id,
            'cargo': 'Cargo Inventado',
        })
        assert respuesta.status_code == 400
        assert Usuario.query.filter_by(correo='invalido@sena.edu.co').first() is None

        persona = crear_usuario(correo='persona@sena.edu.co', documento='123457')
        respuesta = client.put(f'/usuarios/api/admin/editar_usuario/{persona.id}',
                               json={'cargo': 'Cargo Inventado'})
        assert respuesta.status_code == 400
        db.session.refresh(persona)
        assert persona.cargo == 'Aprendiz'

    def test_registro_con_sesion_admin_tambien_valida_el_cargo(
            self, client, crear_usuario):
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador')
        _iniciar_sesion_admin(client, admin)
        respuesta = client.post('/auth/register', data={
            'nombre': 'Cargo Invalido',
            'correo': 'registro-invalido@sena.edu.co',
            'documento': '123458',
            'password': 'Segura2026',
            'confirm_password': 'Segura2026',
            'acepta_datos': 'si',
            'cargo': 'Cargo Inventado',
        }, headers={'X-Requested-With': 'XMLHttpRequest'})

        assert respuesta.status_code == 400
        assert Usuario.query.filter_by(
            correo='registro-invalido@sena.edu.co').first() is None

    def test_los_cargos_nuevos_se_crean_con_sus_permisos(
            self, client, crear_usuario, monkeypatch):
        enviados = []
        monkeypatch.setattr(
            'app.utils.email.enviar_correo',
            lambda destinatario, asunto, cuerpo: enviados.append(destinatario))
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador')
        _iniciar_sesion_admin(client, admin)
        rol_usuario = Rol.query.filter_by(nombre='Usuario').first()

        for indice, cargo in enumerate(NUEVOS_CARGOS):
            correo = f'{cargo.lower()}@sena.edu.co'
            respuesta = client.post('/usuarios/api/admin/crear_usuario', json={
                'nombre': cargo,
                'correo': correo,
                'contraseña': 'Segura2026',
                'rol_id': rol_usuario.id,
                'cargo': cargo,
                'documento': str(1000000000 + indice),
            })
            assert respuesta.status_code == 200

        assert Usuario.query.filter_by(cargo='Coordinacion').first().puede_ver_ambientes
        assert Usuario.query.filter_by(cargo='Subdirector').first().puede_ver_ambientes
        assert not Usuario.query.filter_by(cargo='Contratista').first().puede_ver_ambientes
        assert not Usuario.query.filter_by(cargo='Funcionario').first().puede_ver_ambientes
        assert len(enviados) == 4

    def test_importacion_acepta_los_cargos_nuevos_y_avisa_los_invalidos(
            self, client, crear_usuario, monkeypatch):
        monkeypatch.setattr('app.utils.email.enviar_correo', lambda *args: True)
        admin = crear_usuario(correo='admin@sena.edu.co', rol='Admin',
                              cargo='Administrador')
        _iniciar_sesion_admin(client, admin)
        filas = [
            {'Nombre': cargo, 'Correo': f'{cargo.lower()}@sena.edu.co',
             'Cargo': cargo}
            for cargo in NUEVOS_CARGOS
        ]
        filas.append({'Nombre': 'No Valido', 'Correo': 'no-valido@sena.edu.co',
                      'Cargo': 'Cargo Inventado'})
        respuesta = client.post(
            '/usuarios/api/admin/importar_usuarios_excel',
            data={'file': (_excel_de(filas), 'cargos.xlsx')},
            content_type='multipart/form-data')

        assert respuesta.status_code == 200
        detalles = respuesta.get_json()['detalles']
        assert detalles['creados'] == 5
        assert any('cargo' in aviso.lower() and 'no valido' in aviso.lower()
                   for aviso in detalles['errores'])
        for cargo in NUEVOS_CARGOS:
            assert Usuario.query.filter_by(cargo=cargo).first() is not None
        assert Usuario.query.filter_by(correo='no-valido@sena.edu.co').first().cargo == 'Aprendiz'
