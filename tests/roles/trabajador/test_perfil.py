def test_entra_a_su_perfil(sesion, usuario):
    r = sesion.get('/usuarios/profile')
    assert r.status_code == 200
    assert usuario.nombre in r.get_data(as_text=True)


def test_actualiza_su_tipo_de_sangre(sesion, usuario, db):
    sesion.post('/usuarios/update_profile', data={'tipo_sangre': 'O+'})
    db.session.refresh(usuario)
    assert usuario.tipo_sangre == 'O+'


def test_tipo_de_sangre_invalido_se_rechaza(sesion, usuario, db):
    sesion.post('/usuarios/update_profile', data={'tipo_sangre': 'X+'})
    db.session.refresh(usuario)
    assert usuario.tipo_sangre != 'X+'
