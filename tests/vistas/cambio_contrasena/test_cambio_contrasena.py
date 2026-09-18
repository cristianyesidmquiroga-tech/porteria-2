def test_sin_contrasena_temporal_no_entra(client, entrar_como):
    entrar_como('aprendiz')
    r = client.get('/auth/cambiar_password_obligatorio')
    assert r.headers['Location'] == '/'


def test_cambia_la_contrasena_temporal(client, entrar_como, db):
    usuario = entrar_como('aprendiz', debe_cambiar_contrasena=True)
    client.post('/auth/cambiar_password_obligatorio',
                data={'contrasena_actual': 'Segura2026',
                      'nueva_contrasena': 'NuevaClave2026',
                      'confirmar_contrasena': 'NuevaClave2026'})
    db.session.refresh(usuario)
    assert usuario.debe_cambiar_contrasena is False
    assert usuario.check_password('NuevaClave2026')


def test_exige_la_contrasena_actual(client, entrar_como, db):
    usuario = entrar_como('aprendiz', debe_cambiar_contrasena=True)
    client.post('/auth/cambiar_password_obligatorio',
                data={'contrasena_actual': 'Incorrecta2026',
                      'nueva_contrasena': 'NuevaClave2026',
                      'confirmar_contrasena': 'NuevaClave2026'})
    db.session.refresh(usuario)
    assert usuario.debe_cambiar_contrasena is True


def test_la_nueva_debe_ser_distinta(client, entrar_como, db):
    usuario = entrar_como('aprendiz', debe_cambiar_contrasena=True)
    client.post('/auth/cambiar_password_obligatorio',
                data={'contrasena_actual': 'Segura2026',
                      'nueva_contrasena': 'Segura2026',
                      'confirmar_contrasena': 'Segura2026'})
    db.session.refresh(usuario)
    assert usuario.debe_cambiar_contrasena is True
