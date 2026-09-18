from datetime import timedelta

from app.utils import get_colombia_time


def test_ya_verificado_no_entra(client, entrar_como):
    entrar_como('aprendiz')
    assert client.get('/auth/verificar').headers['Location'] == '/'


def test_verifica_con_el_codigo_correcto(client, entrar_como, db):
    usuario = entrar_como('aprendiz', correo_verificado=False, codigo_verificacion='123456',
                          codigo_expiracion=get_colombia_time() + timedelta(minutes=10))
    client.post('/auth/verificar', data={'codigo': '123456'})
    db.session.refresh(usuario)
    assert usuario.correo_verificado is True


def test_codigo_incorrecto_no_verifica(client, entrar_como, db):
    usuario = entrar_como('aprendiz', correo_verificado=False, codigo_verificacion='123456',
                          codigo_expiracion=get_colombia_time() + timedelta(minutes=10))
    client.post('/auth/verificar', data={'codigo': '000000'})
    db.session.refresh(usuario)
    assert usuario.correo_verificado is False


def test_codigo_expirado_no_verifica(client, entrar_como, db):
    usuario = entrar_como('aprendiz', correo_verificado=False, codigo_verificacion='123456',
                          codigo_expiracion=get_colombia_time() - timedelta(minutes=1))
    client.post('/auth/verificar', data={'codigo': '123456'})
    db.session.refresh(usuario)
    assert usuario.correo_verificado is False
