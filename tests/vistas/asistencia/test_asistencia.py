from app.models.accesos import Acceso
from app.models.asistencia import AsistenciaClase

ENTRAN = {'admin', 'instructor'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/usuarios/asistencia')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/usuarios/profile'


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/asistencia')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_guarda_la_asistencia_de_la_ficha(client, entrar_como, crear_usuario, db):
    aprendiz = crear_usuario(correo='aprendiz.ficha@sena.edu.co', documento='3000000001',
                             ficha='2758291')
    db.session.add(Acceso(punto_id=1, referencia_id=aprendiz.id,
                          tipo_referencia='Usuario', tipo='Entrada'))
    db.session.commit()
    entrar_como('instructor')
    client.post('/usuarios/asistencia',
                data={'action': 'guardar_asistencia', 'ficha_guardar': '2758291',
                      'presente': [str(aprendiz.id)]})
    registro = AsistenciaClase.query.filter_by(aprendiz_id=aprendiz.id).first()
    assert registro is not None
    assert registro.presente is True
