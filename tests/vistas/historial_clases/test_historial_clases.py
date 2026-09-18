from app.models.asistencia import AsistenciaClase

ENTRAN = {'admin'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/porteria/historial_clases')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/usuarios/profile'


def test_sin_sesion_pide_login(client):
    r = client.get('/porteria/historial_clases')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_busca_por_ficha(client, entrar_como, crear_usuario, db):
    admin = entrar_como('admin')
    aprendiz = crear_usuario(correo='aprendiz.ficha@sena.edu.co', documento='3000000001',
                             nombre='Aprendiz Buscado', ficha='2758291')
    db.session.add(AsistenciaClase(instructor_id=admin.id, aprendiz_id=aprendiz.id,
                                   ficha='2758291', presente=True))
    db.session.commit()
    r = client.post('/porteria/historial_clases', data={'ficha': '2758291'})
    assert 'Aprendiz Buscado' in r.get_data(as_text=True)
