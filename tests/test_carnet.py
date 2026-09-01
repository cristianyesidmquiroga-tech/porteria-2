"""Pruebas del carnet institucional: perfiles, nombres, generalidades y barras.

El carnet es lo que el celador mira para dejar entrar a alguien. Un dato mal
puesto aquí no da error: simplemente imprime algo falso y nadie lo nota.
"""
from datetime import date

import pytest

from app.models.fichas import Ficha
from app.utils.barras import (DatoNoCodificable, codigo128_svg, modulos_code128,
                              valores_code128, _PATRONES)
from app.utils.carnet import (PERFIL_APRENDIZ, PERFIL_CONTRATISTA,
                              PERFIL_FUNCIONARIO, PERFIL_INSTRUCTOR,
                              PERFILES_VALIDOS, abreviatura_documento,
                              partir_nombre, perfil_de_cargo)


def _entrar(client, usuario, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': usuario.correo, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


class TestMapeoDePerfiles:
    """Los cargos del sistema y los perfiles del carnet no coinciden uno a uno.
    La traducción vive en un solo sitio y NO debe tocar los cargos, porque el
    cargo gobierna permisos."""

    @pytest.mark.parametrize('cargo,perfil', [
        ('Aprendiz', PERFIL_APRENDIZ),
        ('Instructor', PERFIL_INSTRUCTOR),
        ('Celador', PERFIL_CONTRATISTA),
        ('Portería', PERFIL_CONTRATISTA),
        ('Administrativo', PERFIL_FUNCIONARIO),
        ('Administrador', PERFIL_FUNCIONARIO),
    ])
    def test_cada_cargo_actual_tiene_perfil(self, cargo, perfil):
        assert perfil_de_cargo(cargo) == perfil

    def test_un_cargo_desconocido_no_revienta(self):
        assert perfil_de_cargo('Cargo Que No Existe') in PERFILES_VALIDOS
        assert perfil_de_cargo(None) in PERFILES_VALIDOS
        assert perfil_de_cargo('') in PERFILES_VALIDOS

    def test_no_distingue_mayusculas(self):
        assert perfil_de_cargo('APRENDIZ') == PERFIL_APRENDIZ
        assert perfil_de_cargo('  instructor ') == PERFIL_INSTRUCTOR

    def test_se_puede_reasignar_por_variable_de_entorno(self, monkeypatch):
        """Otro centro debe poder recolocar sus cargos sin tocar el código."""
        monkeypatch.setenv('CARNET_PERFILES', 'Celador:FUNCIONARIO')
        assert perfil_de_cargo('Celador') == PERFIL_FUNCIONARIO

    def test_un_valor_mal_escrito_se_ignora(self, monkeypatch):
        """Un error de tipeo en el .env no puede dejar a nadie sin carnet."""
        monkeypatch.setenv('CARNET_PERFILES', 'Celador:INVENTADO,basura,:')
        assert perfil_de_cargo('Celador') == PERFIL_CONTRATISTA

    def test_el_perfil_no_cambia_los_permisos(self, crear_usuario):
        """Cambiar el mapeo del carnet no puede darle permisos a nadie."""
        celador = crear_usuario(cargo='Celador', documento='500')
        assert celador.perfil_carnet == PERFIL_CONTRATISTA
        assert celador.puede_operar_porteria is True
        assert celador.puede_asesorar is False


class TestParticionDelNombre:
    def test_si_los_declaro_se_usan_tal_cual(self):
        assert partir_nombre('Cualquier Cosa', 'María José', 'De La Cruz') == (
            'María José', 'De La Cruz')

    def test_cuatro_palabras_se_parten_por_la_mitad(self):
        assert partir_nombre('Juan Carlos Pérez Gómez') == (
            'Juan Carlos', 'Pérez Gómez')

    def test_tres_palabras_van_uno_y_dos(self):
        """En Colombia lo habitual es un nombre y dos apellidos."""
        assert partir_nombre('Juan Pérez Gómez') == ('Juan', 'Pérez Gómez')

    def test_dos_palabras(self):
        assert partir_nombre('Ana Torres') == ('Ana', 'Torres')

    def test_una_sola_palabra_no_inventa_apellido(self):
        assert partir_nombre('Cher') == ('Cher', '')

    def test_cinco_palabras_dejan_lo_sobrante_en_apellidos(self):
        assert partir_nombre('Ana María Del Río Vargas') == (
            'Ana María', 'Del Río Vargas')

    def test_vacio_no_revienta(self):
        assert partir_nombre('') == ('', '')
        assert partir_nombre(None) == ('', '')

    def test_los_campos_declarados_mandan_sobre_el_reparto(self, crear_usuario):
        persona = crear_usuario(nombre='Juan Carlos Pérez Gómez', documento='1')
        assert persona.nombres_carnet == 'Juan Carlos'
        persona.nombres = 'Juan'
        persona.apellidos = 'Carlos Pérez Gómez'
        assert persona.nombres_carnet == 'Juan'
        assert persona.apellidos_carnet == 'Carlos Pérez Gómez'


class TestDocumentoImpreso:
    def test_abreviaturas(self):
        assert abreviatura_documento('CC') == 'C.C.'
        assert abreviatura_documento('TI') == 'T.I.'
        assert abreviatura_documento(None) == 'C.C.'

    def test_el_carnet_muestra_tipo_y_numero(self, crear_usuario):
        persona = crear_usuario(documento='1098765432', tipo_documento='TI')
        assert persona.documento_carnet == 'T.I. 1098765432'

    def test_sin_documento_no_inventa_nada(self, crear_usuario):
        persona = crear_usuario(documento=None)
        assert persona.documento_carnet == ''


class TestCodigoDeBarras:
    """El símbolo Code128 se genera aquí, así que hay que comprobar que la
    tabla de patrones no se corrompió: un solo dígito mal y el lector no lee.
    La verificación de que ZXing (el decodificador que usa html5-qrcode) lo lee
    de vuelta se hizo en el navegador; esto vigila la estructura."""

    def test_la_tabla_de_patrones_es_valida(self):
        assert len(_PATRONES) == 107
        assert len(set(_PATRONES)) == 107, 'hay patrones duplicados'
        for valor, patron in enumerate(_PATRONES[:106]):
            assert len(patron) == 6, valor
            assert sum(int(c) for c in patron) == 11, valor
            # Propiedad del Code128: los tres anchos de barra suman par.
            assert (int(patron[0]) + int(patron[2]) + int(patron[4])) % 2 == 0, valor
        assert _PATRONES[106] == '2331112', 'el patrón de parada cambió'

    def test_el_digito_de_control_es_el_esperado(self):
        """Vector conocido: "12345" en Code128-B lleva control 90."""
        valores = valores_code128('12345')
        assert valores[0] == 104, 'debe empezar con Start B'
        assert valores[1:6] == [17, 18, 19, 20, 21]
        assert valores[-2] == 90
        assert valores[-1] == 106, 'debe terminar con Stop'

    @pytest.mark.parametrize('dato', [
        '1098765432',
        'SENA-VISIT:1098765432',
        'SENA-VEH-S:ABC123',
        'SENA-VEH-E:ABC123',
        'SENA-OBJ:SN-1756512345',
    ])
    def test_codifica_los_codigos_reales_del_sistema(self, dato):
        """Los pases llevan letras, dígitos y dos puntos: solo Code128 los toma."""
        svg = codigo128_svg(dato)
        assert svg.startswith('<svg')
        assert 'fill="#000"' in svg
        # Empieza y acaba en blanco: es la zona muda que el lector necesita.
        assert 'fill="#fff"' in svg

    def test_el_svg_escala_al_ancho_del_contenedor(self):
        """Sin ancho fijo, para poder darle todo el ancho del carnet."""
        svg = codigo128_svg('123456')
        assert 'preserveAspectRatio="none"' in svg
        assert 'viewBox=' in svg
        assert 'width="' not in svg.split('<rect')[0], 'el <svg> no debe fijar ancho'

    def test_un_caracter_no_representable_se_rechaza(self):
        with pytest.raises(DatoNoCodificable):
            codigo128_svg('camión')   # la ó está fuera del ASCII imprimible
        with pytest.raises(DatoNoCodificable):
            codigo128_svg('')

    def test_el_simbolo_crece_11_modulos_por_caracter(self):
        base = len(modulos_code128('A'))
        assert len(modulos_code128('AB')) == base + 6


class TestElCarnetMuestraLoSuyoSegunElPerfil:
    def _preparar(self, crear_usuario, db, app, cargo, **extras):
        import os
        from app.models.usuarios import ESTADO_APROBADA
        persona = crear_usuario(cargo=cargo, documento='1098765432',
                                tipo_sangre='O+', perfil_completo=True,
                                nombres='María José', apellidos='De La Cruz',
                                **extras)
        carpeta = os.path.join(app.root_path, 'static', 'uploads', 'profiles')
        os.makedirs(carpeta, exist_ok=True)
        nombre = f'user_{persona.id}.jpg'
        with open(os.path.join(carpeta, nombre), 'wb') as f:
            f.write(b'\xff\xd8\xff\xdb')
        persona.foto = nombre
        persona.foto_estado = ESTADO_APROBADA
        db.session.commit()
        return persona, os.path.join(carpeta, nombre)

    def test_el_carnet_de_aprendiz_lleva_ficha_programa_fecha_y_poliza(
            self, client, crear_usuario, db, app):
        import os
        ficha = Ficha(numero='2847513', programa='Análisis y Desarrollo de Software',
                      fecha_finalizacion=date(2027, 6, 30))
        db.session.add(ficha)
        db.session.commit()
        persona, ruta = self._preparar(crear_usuario, db, app, 'Aprendiz')
        persona.ficha_id = ficha.id
        db.session.commit()
        try:
            _entrar(client, persona)
            pagina = client.get('/usuarios/profile').data.decode('utf-8')

            assert 'APRENDIZ' in pagina
            assert 'María José' in pagina
            assert 'De La Cruz' in pagina
            assert 'C.C. 1098765432' in pagina
            assert 'Ficha de Formación No.' in pagina
            assert '2847513' in pagina
            assert '30/06/2027' in pagina
            assert 'Análisis y Desarrollo de Software' in pagina
            # El bloque de la póliza es exclusivo del aprendiz.
            assert 'Aseguradora Aurora' in pagina
            assert 'Póliza No. 100603' in pagina
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    @pytest.mark.parametrize('cargo,perfil', [
        ('Instructor', 'INSTRUCTOR'),
        ('Celador', 'CONTRATISTA'),
        ('Administrativo', 'FUNCIONARIO'),
    ])
    def test_los_demas_perfiles_no_llevan_ficha_ni_poliza(
            self, client, crear_usuario, db, app, cargo, perfil):
        import os
        persona, ruta = self._preparar(crear_usuario, db, app, cargo)
        try:
            _entrar(client, persona)
            pagina = client.get('/usuarios/profile').data.decode('utf-8')

            assert perfil in pagina
            assert 'C.C. 1098765432' in pagina
            assert 'O+' in pagina
            assert 'Ficha de Formación No.' not in pagina
            assert 'Fecha de Finalización' not in pagina
            assert 'Aseguradora Aurora' not in pagina
            assert 'Póliza No.' not in pagina
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_todos_los_perfiles_llevan_codigo_de_barras(self, client,
                                                        crear_usuario, db, app):
        """Sin código de barras nadie puede entrar por portería."""
        import os
        persona, ruta = self._preparar(crear_usuario, db, app, 'Instructor')
        try:
            _entrar(client, persona)
            pagina = client.get('/usuarios/profile').data.decode('utf-8')
            assert 'carnet-of-barras-caja' in pagina
            assert '<svg' in pagina
            assert 'IDENTIDAD DIGITAL' not in pagina, 'quedó rastro del QR viejo'
        finally:
            if os.path.isfile(ruta):
                os.remove(ruta)

    def test_sin_perfil_completo_no_hay_codigo(self, client, crear_usuario):
        persona = crear_usuario(cargo='Aprendiz', documento='1010',
                                perfil_completo=False)
        _entrar(client, persona)
        pagina = client.get('/usuarios/profile').data.decode('utf-8')
        assert 'carnet-of-barras-caja' not in pagina
        assert 'Carnet bloqueado' in pagina


class TestGeneralidadesConfigurables:
    """Regional, centro, aseguradora, teléfono y póliza no pueden estar
    escritos dentro de las plantillas: el sistema debe poder instalarse en
    otro centro cambiando solo el .env."""

    def test_no_quedan_escritas_a_fuego_en_las_plantillas(self):
        import os
        raiz = os.path.join(os.path.dirname(__file__), '..', 'app')
        prohibidas = ('Regional Santander',
                      'Centro de Gestión Agroempresarial del Oriente',
                      'Aseguradora Aurora', '100603')
        encontradas = []
        for carpeta, _, archivos in os.walk(raiz):
            for archivo in archivos:
                if not archivo.endswith(('.html', '.py')):
                    continue
                ruta = os.path.join(carpeta, archivo)
                contenido = open(ruta, encoding='utf-8').read()
                for prohibida in prohibidas:
                    if prohibida in contenido:
                        encontradas.append(f'{archivo}: {prohibida}')
        assert not encontradas, (
            'estas generalidades siguen escritas dentro de app/: '
            + '; '.join(encontradas))

    def test_estan_disponibles_en_todas_las_plantillas(self, client,
                                                       crear_usuario):
        persona = crear_usuario(documento='1010')
        _entrar(client, persona)
        pagina = client.get('/usuarios/profile').data.decode('utf-8')
        assert 'Regional Santander' in pagina
        assert 'Centro de Gestión Agroempresarial del Oriente' in pagina

    def test_cambiarlas_cambia_lo_que_se_imprime(self, client, crear_usuario,
                                                 app):
        app.config['GENERALIDADES'] = dict(app.config['GENERALIDADES'],
                                           regional='Regional Antioquia',
                                           centro='Centro de Comercio')
        persona = crear_usuario(documento='1010')
        _entrar(client, persona)
        pagina = client.get('/usuarios/profile').data.decode('utf-8')
        assert 'Regional Antioquia' in pagina
        assert 'Regional Santander' not in pagina
