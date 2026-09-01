"""Pruebas del envio de correo (app/utils/email.py).

Este modulo falla en silencio: todo ocurre en un hilo aparte, asi que un error
no rompe ninguna peticion, solo hace que alguien no reciba su codigo y no pueda
entrar al centro. Por eso lo que se comprueba aqui no es "que envie", sino que
no haga las tres cosas que ya han costado caro:

  1. reintentar un fallo que nunca va a salir bien (una direccion inexistente,
     unas credenciales mal puestas), que es el patron por el que Gmail suspende
     la cuenta;
  2. abrir la conexion sin cifrar por un valor mal escrito en MAIL_CIFRADO, con
     la contrasena SMTP viajando en claro;
  3. escribir direcciones completas en el registro (Ley 1581 de 2012).

El servidor SMTP se simula: no se abre ni un socket. La simulacion registra el
estado real del canal en cada orden, para poder afirmar que la clave nunca sale
por una conexion sin cifrar.
"""
import logging
import smtplib
import time
from email.mime.text import MIMEText

import pytest
from flask import Flask

from app.utils import email as correo


REGISTRO = 'app.utils.email'


# --------------------------------------------------------------------------
# Servidor SMTP simulado
# --------------------------------------------------------------------------

class ConexionSimulada:
    """Doble de smtplib.SMTP / SMTP_SSL que anota lo que se le pide.

    Guarda el estado del cifrado en el momento de cada orden: asi una prueba
    puede afirmar que el login NO ocurrio sobre un canal en claro.
    """

    def __init__(self, registro, host, puerto, cifrado_inicial,
                 fallo_login=None, fallo_envio=None):
        self.registro = registro
        self.host = host
        self.puerto = puerto
        self.cifrado = cifrado_inicial
        self.fallo_login = fallo_login
        self.fallo_envio = fallo_envio
        self.ordenes = []
        self.mensajes = []
        self.cerrada = False
        registro.conexiones.append(self)

    def ehlo(self):
        self.ordenes.append('ehlo')

    def has_extn(self, nombre):
        return True

    def starttls(self, context=None):
        if self.cifrado == 'ssl':
            raise smtplib.SMTPNotSupportedError(
                'STARTTLS sobre un canal ya cifrado')
        self.ordenes.append('starttls')
        self.cifrado = 'starttls'

    def login(self, usuario, clave):
        self.ordenes.append('login')
        self.registro.cifrado_al_autenticar.append(self.cifrado)
        if self.fallo_login is not None:
            raise self.fallo_login

    def send_message(self, mensaje):
        self.ordenes.append('send_message')
        self.registro.cifrado_al_enviar.append(self.cifrado)
        if self.fallo_envio is not None:
            raise self.fallo_envio
        self.mensajes.append(mensaje)

    def quit(self):
        self.ordenes.append('quit')
        self.cerrada = True


class RegistroSMTP:
    def __init__(self):
        self.conexiones = []
        self.cifrado_al_autenticar = []
        self.cifrado_al_enviar = []

    @property
    def ultima(self):
        return self.conexiones[-1]


def simular_smtp(monkeypatch, fallo_login=None, fallo_envio=None,
                 fallo_conexion=None):
    """Sustituye smtplib.SMTP y SMTP_SSL por el doble y devuelve el registro."""
    registro = RegistroSMTP()

    def fabrica(cifrado_inicial):
        def crear(host, puerto, timeout=None, context=None, **extras):
            if fallo_conexion is not None:
                raise fallo_conexion
            return ConexionSimulada(registro, host, puerto, cifrado_inicial,
                                    fallo_login, fallo_envio)
        return crear

    monkeypatch.setattr(smtplib, 'SMTP', fabrica('ninguno'))
    monkeypatch.setattr(smtplib, 'SMTP_SSL', fabrica('ssl'))
    return registro


# --------------------------------------------------------------------------
# Utilidades comunes
# --------------------------------------------------------------------------

DESTINO = 'aprendiz.identificable@sena.edu.co'
REMITENTE = 'remitente.identificable@sena.edu.co'


@pytest.fixture
def aplicacion():
    """App minima: _enviar solo necesita un contexto, no la base de datos."""
    return Flask('pruebas-correo')


@pytest.fixture(autouse=True)
def cola_limpia():
    """Deja la cola y el contador de reintentos como estaban.

    La cola es un objeto unico de modulo: un correo olvidado por una prueba se
    lo encontraria la siguiente.
    """
    _vaciar_cola()
    correo._reintentos_en_espera = 0
    yield
    _vaciar_cola()
    correo._reintentos_en_espera = 0


def _vaciar_cola():
    while True:
        try:
            correo._cola.get_nowait()
        except Exception:
            break


def enviar(aplicacion, cifrado='starttls', puerto=587, usuario=REMITENTE,
           clave='secreta', servidor='smtp.sena.edu.co', modo='rele',
           respaldo_rele=True):
    mensaje = MIMEText('hola', 'html', 'utf-8')
    return correo._enviar(aplicacion, mensaje, DESTINO, servidor, puerto,
                          usuario, clave, cifrado, modo, respaldo_rele,
                          REMITENTE)


def config(**cambios):
    base = {
        'servidor': 'smtp.sena.edu.co', 'puerto': 587, 'usuario': REMITENTE,
        'clave': 'secreta', 'cifrado': 'starttls', 'modo': 'rele',
        'respaldo_rele': True,
    }
    base.update(cambios)
    return base


# --------------------------------------------------------------------------
# 1. Fallos definitivos frente a fallos pasajeros
# --------------------------------------------------------------------------

def test_envio_correcto_devuelve_entregado(aplicacion, monkeypatch):
    registro = simular_smtp(monkeypatch)
    assert enviar(aplicacion) == correo.ENTREGADO
    assert len(registro.ultima.mensajes) == 1


def test_credenciales_rechazadas_es_fallo_definitivo(aplicacion, monkeypatch):
    """Unas credenciales mal puestas no mejoran reintentando: serian 3 logins
    rechazados por correo, y con 300 aprendices eso bloquea la cuenta."""
    simular_smtp(monkeypatch, fallo_login=smtplib.SMTPAuthenticationError(
        535, b'Bad credentials'))
    assert enviar(aplicacion) == correo.FALLO_DEFINITIVO


def test_destinatario_inexistente_es_fallo_definitivo(aplicacion, monkeypatch):
    fallo = smtplib.SMTPRecipientsRefused({DESTINO: (550, b'No such user')})
    simular_smtp(monkeypatch, fallo_envio=fallo)
    assert enviar(aplicacion) == correo.FALLO_DEFINITIVO


def test_remitente_rechazado_es_fallo_definitivo(aplicacion, monkeypatch):
    fallo = smtplib.SMTPSenderRefused(553, b'Sender not allowed', REMITENTE)
    simular_smtp(monkeypatch, fallo_envio=fallo)
    assert enviar(aplicacion) == correo.FALLO_DEFINITIVO


def test_rechazo_5xx_es_fallo_definitivo(aplicacion, monkeypatch):
    simular_smtp(monkeypatch,
                 fallo_envio=smtplib.SMTPDataError(552, b'Message too large'))
    assert enviar(aplicacion) == correo.FALLO_DEFINITIVO


def test_rechazo_4xx_es_fallo_pasajero(aplicacion, monkeypatch):
    """4xx es 'ahora no, prueba luego': eso si merece reintentarse."""
    simular_smtp(monkeypatch,
                 fallo_envio=smtplib.SMTPDataError(451, b'Try again later'))
    assert enviar(aplicacion) == correo.FALLO_PASAJERO


def test_corte_de_red_es_fallo_pasajero(aplicacion, monkeypatch):
    simular_smtp(monkeypatch, fallo_conexion=OSError('conexion rechazada'))
    assert enviar(aplicacion) == correo.FALLO_PASAJERO


def test_servidor_que_cuelga_es_fallo_pasajero(aplicacion, monkeypatch):
    simular_smtp(monkeypatch,
                 fallo_envio=smtplib.SMTPServerDisconnected('cerro'))
    assert enviar(aplicacion) == correo.FALLO_PASAJERO


# --------------------------------------------------------------------------
# 2. La cola: que se reintenta y que no
# --------------------------------------------------------------------------

def test_fallo_definitivo_no_se_reintenta(aplicacion, monkeypatch, caplog):
    monkeypatch.setattr(correo, '_enviar',
                        lambda *a, **k: correo.FALLO_DEFINITIVO)
    caplog.set_level(logging.INFO, logger=REGISTRO)

    correo._procesar_uno(aplicacion, MIMEText('x'), DESTINO, config(),
                         REMITENTE, 0)

    time.sleep(0.2)  # margen por si se hubiera programado un temporizador
    assert correo.correos_pendientes() == 0, 'un fallo definitivo se reencolo'
    assert 'descartado sin reintentos' in caplog.text


def test_fallo_pasajero_si_se_reintenta(aplicacion, monkeypatch):
    monkeypatch.setattr(correo, '_enviar',
                        lambda *a, **k: correo.FALLO_PASAJERO)
    monkeypatch.setattr(correo, 'ESPERA_REINTENTO_BASE', 0)
    monkeypatch.setattr(correo, '_asegurar_enviador', lambda: None)

    correo._procesar_uno(aplicacion, MIMEText('x'), DESTINO, config(),
                         REMITENTE, 0)

    reencolado = correo._cola.get(timeout=5)
    assert reencolado[2] == DESTINO
    assert reencolado[5] == 1, 'el contador de intentos no avanzo'


def test_no_se_reintenta_indefinidamente(aplicacion, monkeypatch, caplog):
    monkeypatch.setattr(correo, '_enviar',
                        lambda *a, **k: correo.FALLO_PASAJERO)
    monkeypatch.setattr(correo, 'ESPERA_REINTENTO_BASE', 0)
    caplog.set_level(logging.INFO, logger=REGISTRO)

    correo._procesar_uno(aplicacion, MIMEText('x'), DESTINO, config(),
                         REMITENTE, correo.MAX_REINTENTOS)

    time.sleep(0.2)
    assert correo.correos_pendientes() == 0
    assert 'abandonado' in caplog.text


def test_la_espera_del_reintento_no_bloquea_al_resto(aplicacion, monkeypatch):
    """La espera de 5 s / 20 s no puede ocurrir dentro del hilo enviador: si
    ocurriera, un solo correo problematico dejaria parados hasta 25 s a todos
    los que vienen detras en la cola."""
    monkeypatch.setattr(correo, '_enviar',
                        lambda *a, **k: correo.FALLO_PASAJERO)
    monkeypatch.setattr(correo, 'ESPERA_REINTENTO_BASE', 30)

    inicio = time.monotonic()
    correo._procesar_uno(aplicacion, MIMEText('x'), DESTINO, config(),
                         REMITENTE, 0)
    transcurrido = time.monotonic() - inicio

    assert transcurrido < 1, 'el enviador se quedo bloqueado esperando'
    # El correo sigue contando como pendiente aunque no este en la cola.
    assert correo.correos_pendientes() == 1


def test_el_temporizador_del_reintento_es_demonio(aplicacion, monkeypatch):
    """Un reintento pendiente no puede impedir que el proceso se apague."""
    monkeypatch.setattr(correo, 'ESPERA_REINTENTO_BASE', 30)
    temporizador = correo._programar_reintento(
        aplicacion, MIMEText('x'), DESTINO, config(), REMITENTE, 0)
    try:
        assert temporizador.daemon is True
    finally:
        temporizador.cancel()
        correo._reintentos_en_espera = 0


# --------------------------------------------------------------------------
# 3. Cifrado
# --------------------------------------------------------------------------

@pytest.mark.parametrize('puerto, esperado', [
    (465, 'ssl'),        # TLS implicito: cifrado desde el primer byte
    (587, 'starttls'),   # se abre en claro y se cifra con STARTTLS
    (25, 'ninguno'),     # solo aceptable contra un rele local
    (2525, 'starttls'),  # cualquier otro puerto: cifrar por defecto
])
def test_cada_puerto_elige_su_cifrado(puerto, esperado):
    assert correo._modo_cifrado(puerto, None) == esperado


@pytest.mark.parametrize('valor', ['ssl', 'STARTTLS', ' ninguno '])
def test_un_valor_valido_de_mail_cifrado_se_respeta(valor):
    assert correo._modo_cifrado(587, valor) == valor.strip().lower()


@pytest.mark.parametrize('valor', ['tls', 'TLS', 'si', 'true', 'ssl/tls', '1'])
@pytest.mark.parametrize('puerto', [465, 587, 25])
def test_mail_cifrado_invalido_no_desactiva_el_cifrado(valor, puerto, caplog):
    """Un valor mal escrito no puede colarse tal cual: como el codigo solo
    compara con 'ssl' y 'starttls', 'tls' abriria la conexion en claro y la
    contrasena SMTP saldria en texto plano por la red."""
    caplog.set_level(logging.ERROR, logger=REGISTRO)

    resultado = correo._modo_cifrado(puerto, valor)

    assert resultado in correo.MODOS_CIFRADO
    assert resultado == correo._modo_cifrado(puerto, None), \
        'no se dedujo del puerto'
    assert 'MAIL_CIFRADO' in caplog.text, 'el valor invalido no quedo registrado'


def test_puerto_465_abre_el_canal_ya_cifrado(aplicacion, monkeypatch):
    registro = simular_smtp(monkeypatch)
    assert enviar(aplicacion, cifrado='ssl', puerto=465) == correo.ENTREGADO
    assert registro.cifrado_al_autenticar == ['ssl']
    assert 'starttls' not in registro.ultima.ordenes


def test_puerto_587_cifra_antes_de_autenticar(aplicacion, monkeypatch):
    registro = simular_smtp(monkeypatch)
    assert enviar(aplicacion, cifrado='starttls', puerto=587) == correo.ENTREGADO
    ordenes = registro.ultima.ordenes
    assert ordenes.index('starttls') < ordenes.index('login')
    assert registro.cifrado_al_autenticar == ['starttls']


def test_un_mail_cifrado_invalido_no_manda_la_clave_en_claro(aplicacion,
                                                             monkeypatch):
    """Prueba de extremo a extremo del fallo real: MAIL_CIFRADO=tls en el
    puerto 587 no puede acabar en un login sobre un canal sin cifrar."""
    monkeypatch.setenv('MAIL_SERVER', 'smtp.sena.edu.co')
    monkeypatch.setenv('MAIL_PORT', '587')
    monkeypatch.setenv('MAIL_CIFRADO', 'tls')
    monkeypatch.setenv('MAIL_USERNAME', REMITENTE)
    monkeypatch.setenv('MAIL_PASSWORD', 'secreta')
    registro = simular_smtp(monkeypatch)

    cfg = correo.configuracion_smtp()
    assert cfg['cifrado'] == 'starttls'

    assert enviar(aplicacion, cifrado=cfg['cifrado'],
                  puerto=cfg['puerto']) == correo.ENTREGADO
    assert 'ninguno' not in registro.cifrado_al_autenticar, \
        'la contrasena SMTP salio por un canal sin cifrar'
    assert 'ninguno' not in registro.cifrado_al_enviar


# --------------------------------------------------------------------------
# 4. Minimizacion de datos personales (Ley 1581 de 2012)
# --------------------------------------------------------------------------

def test_las_credenciales_rechazadas_no_escriben_el_remitente_entero(
        aplicacion, monkeypatch, caplog):
    simular_smtp(monkeypatch, fallo_login=smtplib.SMTPAuthenticationError(
        535, b'Bad credentials'))
    caplog.set_level(logging.DEBUG, logger=REGISTRO)

    enviar(aplicacion)

    assert REMITENTE not in caplog.text
    assert 're***@sena.edu.co' in caplog.text


@pytest.mark.parametrize('fallo', [
    None,
    smtplib.SMTPAuthenticationError(535, b'Bad credentials'),
])
def test_ninguna_direccion_completa_aparece_en_el_registro(aplicacion,
                                                           monkeypatch,
                                                           caplog, fallo):
    simular_smtp(monkeypatch, fallo_login=fallo)
    caplog.set_level(logging.DEBUG, logger=REGISTRO)

    enviar(aplicacion)

    assert DESTINO not in caplog.text
    assert REMITENTE not in caplog.text


def test_el_destinatario_rechazado_tampoco_se_escribe_entero(aplicacion,
                                                             monkeypatch,
                                                             caplog):
    fallo = smtplib.SMTPRecipientsRefused({DESTINO: (550, b'No such user')})
    simular_smtp(monkeypatch, fallo_envio=fallo)
    caplog.set_level(logging.DEBUG, logger=REGISTRO)

    correo._procesar_uno(aplicacion, MIMEText('x'), DESTINO, config(),
                         REMITENTE, 0)

    assert DESTINO not in caplog.text
    assert 'ap***@sena.edu.co' in caplog.text


def test_ofuscar_no_revela_el_usuario_completo():
    assert correo._ofuscar('juan.perez@sena.edu.co') == 'ju***@sena.edu.co'
    assert correo._ofuscar('ana@sena.edu.co') == 'a***@sena.edu.co'
    assert correo._ofuscar(None) == '(sin destinatario)'
    assert correo._ofuscar('sin-arroba') == '(sin destinatario)'


# --------------------------------------------------------------------------
# 5. El hilo enviador y el comportamiento externo
# --------------------------------------------------------------------------

def test_el_hilo_enviador_sobrevive_a_un_elemento_corrupto(monkeypatch):
    """Si el hilo muere, la cola se queda parada y nadie se entera: los correos
    encolados no salen, y solo se relanzaria cuando alguien encole otro."""
    monkeypatch.setattr(correo, 'PAUSA_ENTRE_CORREOS', 0)
    correo._asegurar_enviador()
    hilo = correo._enviador
    assert hilo.is_alive()

    correo._cola.put(('elemento', 'corrupto'))  # no se puede desempaquetar

    fin = time.time() + 5
    while not correo._cola.empty() and time.time() < fin:
        time.sleep(0.05)

    assert correo._cola.empty(), 'el hilo no llego a consumir el elemento'
    assert hilo.is_alive(), 'el hilo enviador murio y dejo la cola parada'


def test_enviar_correo_encola_y_vuelve_pronto(monkeypatch):
    """El comportamiento externo no cambia: la peticion web no espera al
    servidor de correo."""
    monkeypatch.setenv('MAIL_SERVER', 'smtp.sena.edu.co')
    monkeypatch.setenv('MAIL_DEFAULT_SENDER', REMITENTE)
    monkeypatch.setattr(correo, '_asegurar_enviador', lambda: None)
    app = Flask('pruebas-correo')

    with app.app_context():
        inicio = time.monotonic()
        assert correo.enviar_correo(DESTINO, 'Codigo', '<p>hola</p>') is True
        assert time.monotonic() - inicio < 1

    encolado = correo._cola.get_nowait()
    assert encolado[2] == DESTINO
    assert encolado[5] == 0


def test_enviar_correo_rechaza_un_destinatario_invalido(monkeypatch):
    monkeypatch.setenv('MAIL_SERVER', 'smtp.sena.edu.co')
    monkeypatch.setenv('MAIL_DEFAULT_SENDER', REMITENTE)
    monkeypatch.setattr(correo, '_asegurar_enviador', lambda: None)
    app = Flask('pruebas-correo')

    with app.app_context():
        assert correo.enviar_correo('esto-no-es-un-correo', 'x', 'y') is False
    assert correo._cola.empty()


def test_el_modo_directo_se_conserva(aplicacion, monkeypatch):
    """Se mantiene a peticion expresa del usuario, aunque no sea el
    recomendado."""
    llamadas = []

    def _directo(msg, dest, rem):
        llamadas.append(dest)
        return True

    monkeypatch.setattr(correo, '_entregar_directo', _directo)

    assert enviar(aplicacion, modo='directo') == correo.ENTREGADO
    assert llamadas == [DESTINO]


def test_el_modo_directo_cae_al_rele_si_falla(aplicacion, monkeypatch):
    monkeypatch.setattr(correo, '_entregar_directo', lambda *a: False)
    registro = simular_smtp(monkeypatch)

    assert enviar(aplicacion, modo='directo') == correo.ENTREGADO
    assert len(registro.ultima.mensajes) == 1


def test_el_modo_directo_sin_respaldo_es_pasajero(aplicacion, monkeypatch):
    monkeypatch.setattr(correo, '_entregar_directo', lambda *a: False)
    assert enviar(aplicacion, modo='directo',
                  respaldo_rele=False) == correo.FALLO_PASAJERO
