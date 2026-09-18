def test_entra_al_escaner(sesion):
    assert sesion.get('/porteria/scanner').status_code == 200


def test_verifica_un_documento(sesion, otro_usuario):
    r = sesion.get(f'/porteria/api/verify/{otro_usuario.documento}')
    assert r.get_json()['found'] is True


def test_registra_una_entrada(sesion, otro_usuario):
    r = sesion.post(f'/porteria/register_movement/{otro_usuario.id}/Entrada',
                    headers={'X-Requested-With': 'XMLHttpRequest'})
    assert r.get_json()['status'] == 'success'
