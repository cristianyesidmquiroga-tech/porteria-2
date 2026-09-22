def test_entra_a_ambientes(sesion):
    assert sesion.get('/coordinacion/ambientes').status_code == 200


def test_ve_el_detalle_de_un_ambiente(sesion):
    assert sesion.get('/coordinacion/ambientes/2758291').status_code == 200
