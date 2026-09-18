from app.models.entidades import Equipo

AJAX = {'X-Requested-With': 'XMLHttpRequest'}


def test_registra_un_equipo(sesion, usuario):
    r = sesion.post('/equipos/add', headers=AJAX,
                    data={'nombre': 'Portatil HP', 'serial': 'SN-ROL-1',
                          'tipo': 'Portátil'})
    assert r.get_json()['status'] == 'success'
    assert Equipo.query.filter_by(usuario_id=usuario.id).count() == 1


def test_elimina_su_equipo(sesion, usuario):
    sesion.post('/equipos/add', headers=AJAX,
                data={'nombre': 'Tablet', 'tipo': 'Tablet'})
    equipo = Equipo.query.filter_by(usuario_id=usuario.id).first()
    r = sesion.post(f'/equipos/delete/{equipo.id}', headers=AJAX)
    assert r.get_json()['status'] == 'success'
    assert Equipo.query.filter_by(usuario_id=usuario.id).count() == 0
