def test_abre_sin_sesion(client):
    assert client.get('/politica-privacidad').status_code == 200


def test_abre_con_sesion(client, entrar_como, clave):
    entrar_como(clave)
    assert client.get('/politica-privacidad').status_code == 200
