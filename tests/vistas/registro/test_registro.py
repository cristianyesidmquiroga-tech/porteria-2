from app.models.usuarios import Usuario


def _registrar(client, **extras):
    datos = {'nombre': 'Persona Nueva', 'correo': 'nueva@sena.edu.co',
             'password': 'Segura2026', 'confirm_password': 'Segura2026',
             'acepta_datos': 'on'}
    datos.update(extras)
    return client.post('/auth/register', data=datos)


def test_la_pagina_abre(client):
    assert client.get('/auth/register').status_code == 200


def test_se_registra_como_aprendiz(client):
    _registrar(client)
    nuevo = Usuario.query.filter_by(correo='nueva@sena.edu.co').first()
    assert nuevo.cargo == 'Aprendiz'
    assert nuevo.rol.nombre == 'Usuario'


def test_no_puede_elegir_otro_cargo(client):
    _registrar(client, cargo='Administrador')
    nuevo = Usuario.query.filter_by(correo='nueva@sena.edu.co').first()
    assert nuevo is None or nuevo.cargo != 'Administrador'


def test_contrasenas_distintas_no_registran(client):
    _registrar(client, confirm_password='Otra2026')
    assert Usuario.query.filter_by(correo='nueva@sena.edu.co').first() is None


def test_correo_repetido_no_registra(client, crear_usuario):
    crear_usuario(correo='nueva@sena.edu.co')
    _registrar(client, nombre='Otra Persona')
    assert Usuario.query.filter_by(correo='nueva@sena.edu.co').count() == 1
