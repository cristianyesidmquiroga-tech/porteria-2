import pytest


@pytest.mark.parametrize('estado', ['pendiente', 'aprobada', 'rechazada', 'todos'])
def test_entra_a_revision_de_fotos(sesion, estado):
    assert sesion.get(f'/usuarios/admin/fotos?estado={estado}').status_code == 200


def test_decision_invalida_se_rechaza(sesion, otro_usuario):
    r = sesion.post(f'/usuarios/api/admin/fotos/{otro_usuario.id}/revisar',
                    json={'decision': 'otra'})
    assert r.status_code == 400
