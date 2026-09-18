def test_el_carnet_muestra_su_perfil(sesion):
    r = sesion.get('/usuarios/profile')
    assert 'data-perfil="SUBDIRECTOR"' in r.get_data(as_text=True)


def test_el_carnet_muestra_su_documento(sesion, usuario):
    r = sesion.get('/usuarios/profile')
    assert usuario.documento in r.get_data(as_text=True)
