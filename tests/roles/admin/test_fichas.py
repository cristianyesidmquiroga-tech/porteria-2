from app.models.fichas import Ficha


def test_entra_a_fichas(sesion):
    assert sesion.get('/usuarios/admin/fichas').status_code == 200


def test_crea_una_ficha(sesion):
    sesion.post('/usuarios/admin/fichas/crear',
                data={'numero': '2758291', 'programa': 'Analisis y Desarrollo'})
    assert Ficha.query.filter_by(numero='2758291').first() is not None
