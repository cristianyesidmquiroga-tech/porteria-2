"""Pruebas de las utilidades de seguridad y del manejo de fechas.

Cubren los defectos concretos que encontro la auditoria, para que no vuelvan.
"""
from datetime import datetime

import pytest

from app.utils import parsear_fecha_bd, get_colombia_time
from app.utils.security import (
    comparar_codigo,
    correo_permitido,
    sanitize_html,
    validar_contrasena,
)


class TestValidarContrasena:
    def test_rechaza_vacia(self):
        # Antes el registro publico no validaba nada: se podia crear una
        # cuenta con contrasena vacia.
        assert validar_contrasena('') is not None
        assert validar_contrasena(None) is not None

    @pytest.mark.parametrize('corta', ['1234', 'abc', 'Abc123', '1234567'])
    def test_rechaza_menos_de_ocho(self, corta):
        assert validar_contrasena(corta) is not None

    def test_rechaza_solo_numeros_o_solo_letras(self):
        assert validar_contrasena('123456789') is not None
        assert validar_contrasena('abcdefghi') is not None

    def test_rechaza_confirmacion_distinta(self):
        assert validar_contrasena('Segura2026', 'Otra2026x') is not None

    def test_acepta_valida(self):
        assert validar_contrasena('Segura2026', 'Segura2026') is None


class TestCompararCodigo:
    def test_iguales(self):
        assert comparar_codigo('123456', '123456') is True

    def test_distintos(self):
        assert comparar_codigo('123456', '123457') is False

    def test_vacios_no_coinciden(self):
        # Un usuario sin codigo activo no debe validar contra una cadena vacia.
        assert comparar_codigo(None, '') is False
        assert comparar_codigo('', '') is False
        assert comparar_codigo(None, '123456') is False


class TestCorreoPermitido:
    def test_lista_vacia_permite_todo(self):
        assert correo_permitido('cualquiera@gmail.com', []) is True

    def test_filtra_por_dominio(self):
        permitidos = ['sena.edu.co', 'soy.sena.edu.co']
        assert correo_permitido('juan@sena.edu.co', permitidos) is True
        assert correo_permitido('ana@soy.sena.edu.co', permitidos) is True
        assert correo_permitido('otro@gmail.com', permitidos) is False

    def test_no_se_enganya_con_subcadenas(self):
        # "sena.edu.co.atacante.com" no debe pasar como dominio del SENA.
        assert correo_permitido('x@sena.edu.co.atacante.com', ['sena.edu.co']) is False


class TestSanitizeHtml:
    def test_quita_etiquetas(self):
        assert '<script>' not in sanitize_html('<script>alert(1)</script>hola')

    def test_conserva_texto_normal(self):
        assert sanitize_html('Portatil Dell') == 'Portatil Dell'


class TestFechas:
    """La base guarda hora de Colombia sin zona horaria.

    El defecto original era reinterpretarla como UTC al mostrarla, lo que
    corria todos los reportes 5 horas hacia atras.
    """

    def test_parsea_datetime_sin_desplazar(self):
        original = datetime(2026, 8, 29, 7, 30, 0)
        assert parsear_fecha_bd(original) == original

    def test_parsea_cadena_de_sqlite(self):
        assert parsear_fecha_bd('2026-08-29 07:30:00') == datetime(2026, 8, 29, 7, 30)
        assert parsear_fecha_bd('2026-08-29 07:30:00.123456').hour == 7

    def test_devuelve_none_si_no_puede(self):
        assert parsear_fecha_bd(None) is None
        assert parsear_fecha_bd('no es una fecha') is None

    def test_una_entrada_de_la_manana_no_cae_al_dia_anterior(self):
        # Con el error de 5 horas, un ingreso a las 03:00 se atribuia al dia
        # anterior en los reportes.
        registro = datetime(2026, 8, 29, 3, 0, 0)
        assert parsear_fecha_bd(registro).date() == registro.date()

    def test_hora_colombia_es_naive(self):
        assert get_colombia_time().tzinfo is None
