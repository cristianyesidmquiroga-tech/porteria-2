"""Pruebas de los avatares por cargo.

Sustituyen tanto a las fotos de prueba que vivían en el repositorio como al
servicio externo ui-avatars.com, al que se le enviaba el nombre real de cada
usuario en la URL.
"""
import os

import pytest

from app.models.usuarios import (
    AVATAR_GENERICO,
    avatar_de_cargo,
    ruta_foto_o_avatar,
)

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CARPETA_AVATARES = os.path.join(RAIZ, 'app', 'static', 'img', 'perfiles')


class TestAvatarPorCargo:
    @pytest.mark.parametrize('cargo,esperado', [
        ('Aprendiz', 'img/perfiles/aprendiz.svg'),
        ('Instructor', 'img/perfiles/instructor.svg'),
        ('Celador', 'img/perfiles/celador.svg'),
        ('Administrador', 'img/perfiles/administrador.svg'),
        ('Administrativo', 'img/perfiles/administrativo.svg'),
    ])
    def test_cada_cargo_tiene_el_suyo(self, cargo, esperado):
        assert avatar_de_cargo(cargo) == esperado

    def test_no_distingue_mayusculas_ni_espacios(self):
        # `cargo` es texto libre y llega desde formularios y celdas de Excel.
        assert avatar_de_cargo('  aPrEnDiZ  ') == 'img/perfiles/aprendiz.svg'

    def test_porteria_comparte_avatar_con_celador(self):
        assert avatar_de_cargo('Portería') == avatar_de_cargo('Celador')

    @pytest.mark.parametrize('cargo', [None, '', 'Cargo Inventado', 'xyz'])
    def test_cargo_desconocido_cae_al_generico(self, cargo):
        assert avatar_de_cargo(cargo) == AVATAR_GENERICO

    def test_todos_los_archivos_existen(self):
        # Una ruta que apunte a un SVG inexistente deja la interfaz con imágenes
        # rotas, y el fallo solo se vería en el navegador.
        cargos = ['Aprendiz', 'Instructor', 'Celador', 'Administrador',
                  'Administrativo', 'Visitante', 'Vehiculo', 'ObjetoExterno', None]
        for cargo in cargos:
            ruta = avatar_de_cargo(cargo)
            archivo = os.path.join(RAIZ, 'app', 'static', ruta.replace('/', os.sep))
            assert os.path.isfile(archivo), f"falta el archivo {ruta}"

    def test_los_svg_no_traen_scripts(self):
        # Un SVG admite <script>; estos se sirven desde el propio dominio, así
        # que deben ser puramente gráficos.
        for nombre in os.listdir(CARPETA_AVATARES):
            contenido = open(os.path.join(CARPETA_AVATARES, nombre),
                             encoding='utf-8').read().lower()
            assert '<script' not in contenido
            assert 'onload' not in contenido
            assert 'href' not in contenido


class TestRutaFotoOAvatar:
    def test_sin_foto_devuelve_el_avatar_del_cargo(self):
        assert ruta_foto_o_avatar(None, 'Instructor') == 'img/perfiles/instructor.svg'

    def test_foto_inexistente_cae_al_avatar(self, tmp_path):
        # La columna `foto` puede apuntar a una imagen ya borrada del disco;
        # servir esa ruta dejaría un enlace roto en el escáner.
        resultado = ruta_foto_o_avatar('no_existe.jpg', 'Aprendiz', str(tmp_path))
        assert resultado == 'img/perfiles/aprendiz.svg'

    def test_foto_existente_se_usa(self, tmp_path):
        (tmp_path / 'user_7.jpg').write_bytes(b'contenido')
        resultado = ruta_foto_o_avatar('user_7.jpg', 'Aprendiz', str(tmp_path))
        assert resultado == 'uploads/profiles/user_7.jpg'


class TestSinServiciosExternos:
    def test_ninguna_plantilla_llama_a_ui_avatars(self):
        # Enviaba el nombre real del usuario a un tercero en cada carga de
        # página: datos personales fuera del sistema sin ninguna necesidad.
        plantillas = os.path.join(RAIZ, 'app', 'templates')
        culpables = []
        for carpeta, _, archivos in os.walk(plantillas):
            for archivo in archivos:
                ruta = os.path.join(carpeta, archivo)
                if 'ui-avatars' in open(ruta, encoding='utf-8').read():
                    culpables.append(os.path.relpath(ruta, RAIZ))
        assert culpables == [], f"todavía usan ui-avatars.com: {culpables}"

    def test_el_csp_no_permite_ui_avatars(self, client):
        csp = client.get('/auth/login').headers.get('Content-Security-Policy', '')
        assert 'ui-avatars' not in csp
