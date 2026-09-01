"""Pruebas de la validación del documento de identidad.

En el SENA conviven cédulas, tarjetas de identidad de menores, cédulas de
extranjería y PPT. Validar solo "que sean números" deja pasar errores de
digitación que luego impiden identificar a la persona en portería.
"""
import pytest

from app.utils.documentos import (
    TIPOS_DOCUMENTO,
    descripcion_formato,
    normalizar_numero,
    tipo_probable,
    validar_documento,
)


class TestNormalizacion:
    @pytest.mark.parametrize('entrada,esperado', [
        ('1.098.765.432', '1098765432'),
        ('1 098 765 432', '1098765432'),
        ('1098-765-432', '1098765432'),
        ('  1098765432  ', '1098765432'),
    ])
    def test_quita_puntos_espacios_y_guiones(self, entrada, esperado):
        # Si uno escribe "1.098.765.432" y otro "1098765432", al buscar por
        # documento en portería parecerían dos personas distintas.
        assert normalizar_numero(entrada) == esperado

    def test_el_numero_se_guarda_normalizado(self):
        limpio, error = validar_documento('CC', '1.098.765.432')
        assert error is None
        assert limpio == '1098765432'


class TestLongitudPorTipo:
    @pytest.mark.parametrize('tipo,numero', [
        ('CC', '123456'),          # cédula antigua, 6 dígitos
        ('CC', '1098765432'),      # cédula moderna, 10
        ('TI', '1012345678'),      # tarjeta de identidad, 10
        ('TI', '10123456789'),     # tarjeta de identidad, 11
        ('CE', '123456'),
        ('CE', '1234567'),
        ('PPT', '123456789'),
        ('PPT', '1234567890'),
        ('PA', 'AB123456'),        # pasaporte alfanumérico
    ])
    def test_acepta_longitudes_validas(self, tipo, numero):
        _, error = validar_documento(tipo, numero)
        assert error is None, f'{tipo} {numero} debió aceptarse: {error}'

    @pytest.mark.parametrize('tipo,numero', [
        ('CC', '12345'),           # muy corta
        ('CC', '12345678901'),     # muy larga
        ('TI', '123456'),          # una tarjeta de identidad no tiene 6 dígitos
        ('CE', '12345678'),        # una cédula de extranjería no tiene 8
        ('PPT', '12345'),
    ])
    def test_rechaza_longitudes_invalidas(self, tipo, numero):
        _, error = validar_documento(tipo, numero)
        assert error is not None
        # El mensaje dice cuántos dígitos escribió, para que se dé cuenta de si
        # le sobra o le falta uno.
        assert str(len(numero)) in error

    def test_el_mensaje_sugiere_revisar_el_tipo(self):
        # Puede que el número esté bien y lo equivocado sea el tipo elegido.
        _, error = validar_documento('TI', '123456')
        assert 'tipo de documento' in error.lower()


class TestContenido:
    def test_rechaza_letras_donde_solo_van_numeros(self):
        _, error = validar_documento('CC', '10987A5432')
        assert error is not None
        assert 'solo números' in error

    def test_el_pasaporte_si_admite_letras(self):
        _, error = validar_documento('PA', 'AV1234567')
        assert error is None

    def test_rechaza_que_empiece_por_cero(self):
        # Casi siempre es un error de digitación, o un dato copiado de una hoja
        # de cálculo que perdió el formato.
        _, error = validar_documento('CC', '0123456789')
        assert error is not None
        assert 'cero' in error

    def test_rechaza_vacio(self):
        _, error = validar_documento('CC', '   ')
        assert error is not None

    def test_rechaza_un_tipo_inventado(self):
        _, error = validar_documento('XX', '1098765432')
        assert error is not None


class TestAyudaAlUsuario:
    def test_todos_los_tipos_describen_su_formato(self):
        # Ese texto se muestra junto al campo; si falta, la persona no sabe
        # cuántos dígitos se esperan.
        for clave in TIPOS_DOCUMENTO:
            assert descripcion_formato(clave), f'falta el formato de {clave}'

    def test_sugiere_tarjeta_de_identidad_con_once_digitos(self):
        assert tipo_probable('10123456789') == 'TI'

    def test_sugiere_pasaporte_si_tiene_letras(self):
        assert tipo_probable('AB123456') == 'PA'


class TestEnElPerfil:
    def _entrar(self, client, usuario):
        return client.post('/auth/login',
                           data={'correo': usuario.correo, 'password': 'Segura2026'},
                           headers={'X-Requested-With': 'XMLHttpRequest'})

    def test_guardar_un_documento_valido(self, client, crear_usuario, db):
        persona = crear_usuario(correo='ana@sena.edu.co', documento=None)
        self._entrar(client, persona)
        r = client.post('/usuarios/update_profile',
                        data={'documento': '1.098.765.432', 'tipo_documento': 'CC',
                              'tipo_sangre': 'O+'},
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 200
        db.session.refresh(persona)
        assert persona.documento == '1098765432'
        assert persona.tipo_documento == 'CC'

    def test_un_documento_invalido_se_rechaza(self, client, crear_usuario, db):
        persona = crear_usuario(correo='ana@sena.edu.co', documento=None)
        self._entrar(client, persona)
        r = client.post('/usuarios/update_profile',
                        data={'documento': '123', 'tipo_documento': 'CC'},
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400
        db.session.refresh(persona)
        assert persona.documento is None

    def test_no_se_puede_usar_el_documento_de_otro(self, client, crear_usuario, db):
        # La columna es única: sin comprobarlo, el choque saldría como un error
        # 500 de base de datos en vez de un mensaje entendible.
        crear_usuario(correo='beto@sena.edu.co', documento='1098765432')
        ana = crear_usuario(correo='ana@sena.edu.co', documento=None)
        self._entrar(client, ana)
        r = client.post('/usuarios/update_profile',
                        data={'documento': '1098765432', 'tipo_documento': 'CC'},
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400
        assert 'ya está registrado' in r.get_json()['message']


class TestEnElRegistro:
    def _registrar(self, client, **campos):
        datos = {
            'nombre': 'Persona Nueva',
            'correo': 'nueva@sena.edu.co',
            'documento': '1098765432',
            'tipo_documento': 'CC',
            'password': 'Segura2026',
            'confirm_password': 'Segura2026',
            'acepta_datos': 'si',
        }
        datos.update(campos)
        return client.post('/auth/register', data=datos,
                           headers={'X-Requested-With': 'XMLHttpRequest'})

    def test_registro_con_documento_valido(self, client):
        from app.models.usuarios import Usuario
        assert self._registrar(client).get_json()['status'] == 'success'
        creada = Usuario.query.filter_by(correo='nueva@sena.edu.co').first()
        assert creada.documento == '1098765432'
        assert creada.tipo_documento == 'CC'

    def test_registro_con_documento_invalido(self, client):
        from app.models.usuarios import Usuario
        r = self._registrar(client, documento='99', tipo_documento='CC')
        assert r.status_code == 400
        assert Usuario.query.filter_by(correo='nueva@sena.edu.co').first() is None

    def test_una_tarjeta_de_identidad_de_menor(self, client):
        # Muchos aprendices son menores de edad y entran con TI, no con cédula.
        from app.models.usuarios import Usuario
        r = self._registrar(client, documento='1012345678', tipo_documento='TI')
        assert r.get_json()['status'] == 'success'
        creada = Usuario.query.filter_by(correo='nueva@sena.edu.co').first()
        assert creada.tipo_documento == 'TI'
