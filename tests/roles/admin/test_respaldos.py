def test_entra_a_respaldos(sesion):
    assert sesion.get('/usuarios/admin/respaldos').status_code == 200
