def test_entra_al_historial_de_cambios(sesion):
    assert sesion.get('/usuarios/admin_historial').status_code == 200
