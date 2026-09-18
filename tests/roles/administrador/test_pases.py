from app.models.entidades import Vehiculo, Visitante


def test_entra_a_pases(sesion):
    assert sesion.get('/porteria/pases').status_code == 200


def test_registra_un_visitante(sesion):
    sesion.post('/porteria/pases/crear_visitante',
                data={'nombre': 'Visitante', 'documento': '2000000001',
                      'motivo': 'Reunion'})
    assert Visitante.query.filter_by(documento='2000000001').first() is not None


def test_registra_un_vehiculo(sesion):
    sesion.post('/porteria/pases/crear_vehiculo',
                data={'placa': 'abc123', 'tipo': 'Externo'})
    assert Vehiculo.query.filter_by(placa='ABC123').first() is not None
