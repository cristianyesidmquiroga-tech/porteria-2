def test_entra_al_panel(sesion):
    assert sesion.get('/porteria/dashboard').status_code == 200


def test_exporta_el_historial(sesion):
    r = sesion.get('/porteria/export_dashboard'
                   '?fecha_inicio=2026-01-01&fecha_fin=2026-12-31')
    assert r.mimetype == 'text/csv'
