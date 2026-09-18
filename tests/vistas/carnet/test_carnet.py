import pytest

PERFIL_CARNET = {
    'admin': 'FUNCIONARIO', 'administrador': 'FUNCIONARIO',
    'administrativo': 'FUNCIONARIO', 'aprendiz': 'APRENDIZ',
    'celador': 'CONTRATISTA', 'contratista': 'CONTRATISTA',
    'coordinacion': 'FUNCIONARIO', 'funcionario': 'FUNCIONARIO',
    'instructor': 'INSTRUCTOR', 'porteria': 'CONTRATISTA',
    'subdirector': 'SUBDIRECTOR', 'trabajador': 'FUNCIONARIO',
}


def test_cada_perfil_ve_su_carnet(client, entrar_como, clave):
    entrar_como(clave)
    html = client.get('/usuarios/profile').get_data(as_text=True)
    assert f'data-perfil="{PERFIL_CARNET[clave]}"' in html


def test_con_perfil_completo_muestra_codigo_de_barras(client, entrar_como):
    entrar_como('aprendiz')
    assert '<svg' in client.get('/usuarios/profile').get_data(as_text=True)


def test_con_perfil_incompleto_no_muestra_codigo_de_barras(client, entrar_como):
    entrar_como('aprendiz', perfil_completo=False)
    html = client.get('/usuarios/profile').get_data(as_text=True)
    assert 'carnet-of-barras-caja' not in html
