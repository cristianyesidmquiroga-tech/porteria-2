import pytest


@pytest.mark.parametrize('cargo', ['Aprendiz', 'Instructor', 'Personal'])
def test_entra_a_reportes(sesion, cargo):
    assert sesion.get(f'/porteria/analytics/{cargo}').status_code == 200
