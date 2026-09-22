def test_entra_a_comunicados(sesion):
    assert sesion.get('/usuarios/comunicados').status_code == 200


def test_enviar_sin_destinatarios_se_rechaza(sesion):
    r = sesion.post('/usuarios/api/enviar_comunicado',
                    json={'tipo': 'Comunicado General', 'destinatarios': []})
    assert r.status_code == 400
