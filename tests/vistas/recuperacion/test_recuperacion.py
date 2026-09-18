def test_la_pagina_abre(client):
    assert client.get('/auth/recuperar').status_code == 200


def test_no_se_salta_al_paso_de_verificar(client):
    r = client.get('/auth/recuperar/verificar')
    assert r.headers['Location'] == '/auth/recuperar'


def test_no_se_salta_al_paso_de_cambiar(client):
    r = client.get('/auth/recuperar/cambiar')
    assert r.headers['Location'] == '/auth/recuperar'


def test_cualquier_perfil_pide_codigo(client, crear_usuario, clave, db):
    from app.models.usuarios import Usuario
    usuario = crear_usuario(correo=f'{clave}@sena.edu.co', documento='3000000009')
    client.post('/auth/recuperar', data={'email': usuario.correo})
    db.session.refresh(usuario)
    assert db.session.get(Usuario, usuario.id).codigo_recuperacion is not None


def test_cambia_la_contrasena_con_el_codigo(client, crear_usuario, db):
    usuario = crear_usuario(correo='ana@sena.edu.co')
    client.post('/auth/recuperar', data={'email': 'ana@sena.edu.co'})
    db.session.refresh(usuario)
    client.post('/auth/recuperar/verificar', data={'codigo': usuario.codigo_recuperacion})
    client.post('/auth/recuperar/cambiar',
                data={'password': 'NuevaClave2026', 'confirm_password': 'NuevaClave2026'})
    db.session.refresh(usuario)
    assert usuario.check_password('NuevaClave2026')
