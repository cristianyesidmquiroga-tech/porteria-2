def test_todos_los_perfiles_entran(client, entrar_como, clave):
    entrar_como(clave)
    assert client.get('/usuarios/profile').status_code == 200


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/profile')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_muestra_su_nombre(client, entrar_como, clave):
    usuario = entrar_como(clave)
    assert usuario.nombre in client.get('/usuarios/profile').get_data(as_text=True)


def test_documento_de_otra_persona_se_rechaza(client, entrar_como, crear_usuario, db):
    crear_usuario(correo='otra.persona@sena.edu.co', documento='1098765432')
    usuario = entrar_como('aprendiz')
    client.post('/usuarios/update_profile',
                data={'tipo_documento': 'CC', 'documento': '1098765432'})
    db.session.refresh(usuario)
    assert usuario.documento != '1098765432'


def test_nombres_con_numeros_se_rechazan(client, entrar_como, db):
    usuario = entrar_como('aprendiz')
    client.post('/usuarios/update_profile', data={'nombres': 'Ana123'})
    db.session.refresh(usuario)
    assert usuario.nombres != 'Ana123'
