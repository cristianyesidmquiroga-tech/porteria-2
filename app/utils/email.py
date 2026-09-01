"""Envío de correo por SMTP.

El sistema manda códigos de verificación, recuperación de contraseña y avisos
de revisión de foto. Si el correo no llega, la persona no puede activar su
cuenta ni entrar al centro, así que aquí importa más la fiabilidad que la
elegancia: se registra con detalle qué falló y por qué.

Se conecta a un servidor SMTP (el de la propia institución, idealmente) y le
pide que entregue el mensaje. No entrega directamente a los servidores de
destino: hacerlo desde el VPS haría que los correos acabaran en spam o
rechazados, porque una IP nueva no tiene reputación y muchos proveedores
bloquean el puerto 25 de salida.
"""
import atexit
import logging
import os
import queue
import re
import smtplib
import ssl
import threading
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr

from flask import current_app

logger = logging.getLogger(__name__)

# Segundos de espera antes de darse por vencido con el servidor SMTP. Sin tope,
# un servidor que no responde deja el hilo colgado indefinidamente.
TIEMPO_ESPERA = 20

# Pausa entre correos consecutivos. Antes se lanzaba un hilo y una conexion SMTP
# por cada correo: una importacion de Excel de 300 aprendices abria 300
# conexiones simultaneas contra Gmail, que lo interpreta como abuso y puede
# suspender la cuenta. Con la cola sale uno detras de otro, a ritmo humano.
PAUSA_ENTRE_CORREOS = float(os.environ.get('MAIL_PAUSA_SEGUNDOS', '1.2'))

# Reintentos ante fallos pasajeros (el servidor ocupado, un corte de red).
MAX_REINTENTOS = 2

# Base de la espera creciente entre reintentos: 5 s y luego 20 s.
ESPERA_REINTENTO_BASE = 5

# Únicos valores admitidos en MAIL_CIFRADO.
MODOS_CIFRADO = {'ssl', 'starttls', 'ninguno'}

# Resultados de _enviar: entregado, fallo pasajero (se reintenta) y fallo
# definitivo (insistir solo empeora las cosas: una dirección que no existe no
# va a existir en 20 segundos, y repetir un login rechazado por Gmail es el
# patrón que acaba bloqueando la cuenta).
ENTREGADO = 'entregado'
FALLO_PASAJERO = 'pasajero'
FALLO_DEFINITIVO = 'definitivo'

# Cola de salida y su unico hilo enviador.
_cola = queue.Queue()
_enviador = None
_candado = threading.Lock()

# Reintentos ya programados que todavia no han vuelto a la cola. Se cuentan
# aparte porque durante la espera no estan en _cola: sin esto, el apagado del
# proceso los daria por salidos y se perderian.
_reintentos_en_espera = 0
_candado_reintentos = threading.Lock()


def _modo_cifrado(puerto, configurado):
    """Decide cómo cifrar la conexión.

    Se puede forzar con MAIL_CIFRADO; si no, se deduce del puerto, que es la
    convención universal:
      - 465: TLS implícito, el canal va cifrado desde el primer byte (SMTP_SSL)
      - 587: STARTTLS, se abre en claro y se cifra con el comando STARTTLS
      - 25: sin cifrado (solo aceptable contra un relé local)
      - cualquier otro: STARTTLS
    Antes se llamaba a starttls() siempre, así que un servidor en el 465 (muy
    común en correo institucional) fallaba con "STARTTLS extension not
    supported".

    MAIL_CIFRADO solo se acepta si es uno de los tres valores conocidos: un
    valor mal escrito (`tls`, `TLS`) caía antes en la rama sin cifrar y la
    contraseña SMTP salía en claro por la red.
    """
    if configurado:
        elegido = configurado.strip().lower()
        if elegido in MODOS_CIFRADO:
            return elegido
        logger.error("MAIL_CIFRADO=%r no es válido (admitidos: %s). Se deduce "
                     "del puerto para no dejar la conexión sin cifrar.",
                     configurado, ', '.join(sorted(MODOS_CIFRADO)))
    if puerto == 465:
        return 'ssl'
    if puerto == 25:
        return 'ninguno'
    return 'starttls'


def _remitente_valido(direccion, nombre=None):
    """Compone la cabecera From evitando inyección de cabeceras.

    Un salto de línea dentro de la dirección permitiría añadir cabeceras
    arbitrarias al mensaje (por ejemplo un Bcc), así que se descartan.
    """
    limpia = re.sub(r'[\r\n]', '', (direccion or '')).strip()
    if not limpia:
        return ''
    if nombre:
        return formataddr((re.sub(r'[\r\n]', '', nombre).strip(), limpia))
    return limpia


def _enviar(app, msg, destinatario, servidor, puerto, usuario, clave, cifrado,
            modo='rele', respaldo_rele=True, remitente=''):
    """Entrega el mensaje. Corre en un hilo aparte para no bloquear la petición."""
    with app.app_context():
        if modo == 'directo':
            if _entregar_directo(msg, destinatario, remitente):
                return ENTREGADO
            if not respaldo_rele or not servidor:
                return FALLO_PASAJERO
            logger.warning("Entrega directa fallida, reintentando por el relé.")

        conexion = None
        try:
            if cifrado == 'ssl':
                contexto = ssl.create_default_context()
                conexion = smtplib.SMTP_SSL(servidor, puerto, timeout=TIEMPO_ESPERA,
                                            context=contexto)
            else:
                conexion = smtplib.SMTP(servidor, puerto, timeout=TIEMPO_ESPERA)
                if cifrado == 'starttls':
                    conexion.starttls(context=ssl.create_default_context())

            # Un relé local de confianza puede no pedir autenticación.
            if usuario and clave:
                conexion.login(usuario, clave)

            conexion.send_message(msg)
            logger.info("Correo entregado al servidor SMTP para %s",
                        _ofuscar(destinatario))
            return ENTREGADO
        except smtplib.SMTPAuthenticationError:
            # El fallo más habitual con Gmail: hace falta una contraseña de
            # aplicación, no la del correo. Reintentar no arregla nada y, en una
            # importación de cientos de personas, son cientos de logins
            # rechazados seguidos: justo lo que hace que Gmail bloquee la cuenta.
            logger.error("SMTP rechazó las credenciales de %s. Si es Gmail, hay "
                         "que usar una contraseña de aplicación, no la normal.",
                         _ofuscar(usuario))
            return FALLO_DEFINITIVO
        except smtplib.SMTPRecipientsRefused:
            logger.error("El servidor rechazó al destinatario %s. La dirección "
                         "no existe o no admite correo: se descarta.",
                         _ofuscar(destinatario))
            return FALLO_DEFINITIVO
        except smtplib.SMTPSenderRefused:
            logger.error("El servidor rechazó al remitente %s. Revisa "
                         "MAIL_DEFAULT_SENDER: insistir no lo arregla.",
                         _ofuscar(usuario or remitente))
            return FALLO_DEFINITIVO
        except smtplib.SMTPNotSupportedError as error:
            logger.error("El servidor no admite algo que exige la configuración "
                         "(%s:%s, cifrado=%s): %s", servidor, puerto, cifrado, error)
            return FALLO_DEFINITIVO
        except smtplib.SMTPResponseException as error:
            # 5xx es un rechazo permanente segun la norma SMTP; 4xx es "ahora
            # no, prueba luego". Solo el segundo merece reintentarse.
            if 500 <= (error.smtp_code or 0) < 600:
                logger.error("Rechazo permanente (%s) enviando a %s: se descarta "
                             "sin reintentar.", error.smtp_code,
                             _ofuscar(destinatario))
                return FALLO_DEFINITIVO
            logger.error("Rechazo temporal (%s) enviando a %s: %s",
                         error.smtp_code, _ofuscar(destinatario), error)
            return FALLO_PASAJERO
        except (smtplib.SMTPException, OSError, ssl.SSLError) as error:
            logger.error("Error enviando correo a %s (%s:%s, cifrado=%s): %s",
                         _ofuscar(destinatario), servidor, puerto, cifrado, error)
            return FALLO_PASAJERO
        finally:
            if conexion is not None:
                try:
                    conexion.quit()
                except Exception:
                    pass


def _ofuscar(direccion):
    """Deja el correo reconocible en el log sin escribirlo entero.

    Los logs los puede leer más gente de la que debería ver los correos de los
    aprendices (minimización, Ley 1581).
    """
    if not direccion or '@' not in direccion:
        return '(sin destinatario)'
    usuario, dominio = direccion.rsplit('@', 1)
    visible = usuario[:2] if len(usuario) > 3 else usuario[:1]
    return f"{visible}***@{dominio}"


def _servidores_de_destino(dominio):
    """Devuelve los servidores de correo (MX) de un dominio, por prioridad.

    Solo se usa en el modo directo. Si no hay registros MX, la norma dice que
    se intente contra el propio dominio (registro A).
    """
    try:
        import dns.resolver
    except ImportError:
        logger.error("El modo directo necesita dnspython. Instala: pip install dnspython")
        return []

    try:
        respuestas = dns.resolver.resolve(dominio, 'MX')
        registros = sorted(respuestas, key=lambda r: r.preference)
        return [str(r.exchange).rstrip('.') for r in registros]
    except Exception as error:
        logger.warning("No se pudieron resolver los MX de %s: %s", dominio, error)
        return [dominio]


def _entregar_directo(msg, destinatario, remitente):
    """Entrega el correo directamente al servidor del destinatario.

    Es lo que hace un servidor de correo de verdad: resolver el MX del dominio
    de destino y hablar con el, sin intermediarios.

    AVISO IMPORTANTE, documentado aqui porque es la causa numero uno de que
    esto "no funcione" sin que el codigo tenga ningun fallo:
      1. La mayoria de proveedores de VPS BLOQUEAN el puerto 25 de salida por
         defecto. Si esta bloqueado, no sale ni un correo y no hay nada que
         programar: hay que pedirle al proveedor que lo abra.
      2. Aunque este abierto, una IP sin reputacion, sin SPF, sin DKIM, sin
         DMARC y sin DNS inverso (PTR) acaba en spam o es rechazada de plano
         por Gmail y Outlook.
    En este sistema eso significa que no llegan los codigos de verificacion ni
    de recuperacion, y esa persona no puede activar su cuenta ni entrar al
    centro. Por eso el modo por defecto sigue siendo el rele.
    """
    dominio = destinatario.rsplit('@', 1)[1]
    servidores = _servidores_de_destino(dominio)
    if not servidores:
        logger.error("Sin servidores de destino para %s", dominio)
        return False

    ultimo_error = None
    for servidor in servidores:
        try:
            conexion = smtplib.SMTP(servidor, 25, timeout=TIEMPO_ESPERA)
            conexion.ehlo()
            # Se cifra si el servidor de destino lo admite (casi todos hoy).
            if conexion.has_extn('starttls'):
                conexion.starttls(context=ssl.create_default_context())
                conexion.ehlo()
            conexion.send_message(msg)
            conexion.quit()
            logger.info("Correo entregado directamente a %s via %s",
                        _ofuscar(destinatario), servidor)
            return True
        except Exception as error:
            ultimo_error = error
            logger.warning("Fallo la entrega directa via %s: %s", servidor, error)

    logger.error("No se pudo entregar directamente a %s. Ultimo error: %s. "
                 "Comprueba que el puerto 25 de SALIDA no este bloqueado en el "
                 "servidor.", _ofuscar(destinatario), ultimo_error)
    return False


def configuracion_smtp():
    """Lee la configuración SMTP del entorno. Devuelve un diccionario."""
    puerto = int(os.environ.get('MAIL_PORT', 587))
    usuario = os.environ.get('MAIL_USERNAME')
    return {
        'servidor': os.environ.get('MAIL_SERVER', ''),
        'puerto': puerto,
        'usuario': usuario,
        'clave': os.environ.get('MAIL_PASSWORD'),
        'remitente': os.environ.get('MAIL_DEFAULT_SENDER') or usuario,
        'nombre_remitente': os.environ.get('MAIL_NOMBRE_REMITENTE',
                                           'Sistema de Acceso SENA'),
        'cifrado': _modo_cifrado(puerto, os.environ.get('MAIL_CIFRADO')),
        # 'rele' (por defecto): se le pide a un servidor de correo que entregue.
        # 'directo': la propia aplicacion entrega al servidor del destinatario.
        'modo': os.environ.get('MAIL_MODO', 'rele').strip().lower(),
        # Si la entrega directa falla, reintentar por el rele configurado.
        'respaldo_rele': os.environ.get('MAIL_RESPALDO_RELE', 'true').lower() != 'false',
    }


def enviar_correo(destinatario, asunto, cuerpo_html):
    """Envía un correo en segundo plano. Devuelve True si se pudo encolar.

    Devolver True no garantiza la entrega: el envío ocurre en otro hilo y el
    resultado real queda en el log. Se hace así para que la persona no espere
    varios segundos mirando una pantalla en blanco mientras responde el
    servidor de correo.
    """
    cfg = configuracion_smtp()

    if not cfg['servidor'] and cfg['modo'] != 'directo':
        logger.warning("MAIL_SERVER no configurado: no se envió el correo a %s",
                       _ofuscar(destinatario))
        return False

    remitente = _remitente_valido(cfg['remitente'], cfg['nombre_remitente'])
    if not remitente:
        logger.warning("MAIL_DEFAULT_SENDER no configurado: no se envió el correo.")
        return False

    # Una dirección con saltos de línea permitiría inyectar cabeceras.
    destino = re.sub(r'[\r\n]', '', destinatario or '').strip()
    if '@' not in parseaddr(destino)[1]:
        logger.warning("Destinatario no válido, no se envió el correo.")
        return False

    mensaje = MIMEMultipart('alternative')
    mensaje['Subject'] = re.sub(r'[\r\n]', ' ', asunto or '')
    mensaje['From'] = remitente
    mensaje['To'] = destino
    mensaje.attach(MIMEText(cuerpo_html, 'html', 'utf-8'))

    if cfg['modo'] == 'directo':
        _avisar_riesgo_directo()

    aplicacion = current_app._get_current_object()
    _asegurar_enviador()
    _cola.put((aplicacion, mensaje, destino, cfg, remitente, 0))
    return True


_aviso_directo_dado = False


def _avisar_riesgo_directo():
    """Deja constancia en el log, una sola vez, de lo que implica el modo directo.

    Se conserva a peticion del usuario, pero activarlo sin haber preparado el
    DNS hace que los codigos de verificacion no lleguen, y entonces esa persona
    no puede activar su cuenta ni entrar al centro. El aviso existe para que,
    si eso pasa, la causa este escrita en el log y no haya que adivinarla.
    """
    global _aviso_directo_dado
    if _aviso_directo_dado:
        return
    _aviso_directo_dado = True
    logger.warning(
        "MAIL_MODO=directo activo. Este modo entrega sin pasar por un servidor "
        "de correo y NO firma DKIM ni controla el HELO. Si no estan configurados "
        "SPF, DKIM, DMARC y DNS inverso para el dominio del remitente, los "
        "correos acabaran en spam o seran rechazados, y nadie podra activar su "
        "cuenta. Comprueba antes: python scripts/probar_correo.py --puerto-25")


def _asegurar_enviador():
    """Arranca el hilo enviador la primera vez que se necesita."""
    global _enviador
    with _candado:
        if _enviador is None or not _enviador.is_alive():
            _enviador = threading.Thread(target=_procesar_cola, daemon=True,
                                         name='enviador-correo')
            _enviador.start()


def _procesar_cola():
    """Saca correos de la cola y los envia de uno en uno.

    Un solo hilo para todo el proceso: asi el servidor de correo ve un flujo
    ordenado en vez de una avalancha, que es lo que dispara los bloqueos por
    abuso en Gmail y similares.
    """
    while True:
        try:
            aplicacion, mensaje, destino, cfg, remitente, intentos = _cola.get()
        except Exception:
            # Si get() fallara, morir aqui dejaria la cola parada sin que nadie
            # lo note: los correos ya encolados no saldrian nunca.
            logger.exception("Fallo sacando un correo de la cola")
            time.sleep(1)
            continue
        try:
            _procesar_uno(aplicacion, mensaje, destino, cfg, remitente, intentos)
        except Exception:
            logger.exception("Fallo inesperado enviando un correo de la cola")
        finally:
            _cola.task_done()
        time.sleep(PAUSA_ENTRE_CORREOS)


def _procesar_uno(aplicacion, mensaje, destino, cfg, remitente, intentos):
    """Intenta un correo y decide si se reintenta, se descarta o ya esta.

    Va aparte del bucle para poder probarlo sin arrancar el hilo enviador.
    """
    resultado = _enviar(aplicacion, mensaje, destino, cfg['servidor'],
                        cfg['puerto'], cfg['usuario'], cfg['clave'],
                        cfg['cifrado'], cfg['modo'],
                        cfg['respaldo_rele'], remitente)
    if resultado == FALLO_DEFINITIVO:
        logger.error("Correo a %s descartado sin reintentos: el fallo no se "
                     "arregla insistiendo.", _ofuscar(destino))
        return resultado
    if resultado == FALLO_PASAJERO and intentos < MAX_REINTENTOS:
        _programar_reintento(aplicacion, mensaje, destino, cfg, remitente,
                             intentos)
    elif resultado == FALLO_PASAJERO:
        logger.error("Correo a %s abandonado tras %s intentos.",
                     _ofuscar(destino), MAX_REINTENTOS + 1)
    return resultado


def _programar_reintento(aplicacion, mensaje, destino, cfg, remitente, intentos):
    """Devuelve el correo a la cola tras una espera, sin bloquear al enviador.

    Espera creciente: 5 s y luego 20 s. Si el servidor esta saturado, insistir
    de inmediato solo empeora las cosas. La espera ocurre en un temporizador
    aparte y no en el hilo enviador: si durmiera alli, un solo correo
    problematico dejaria parados hasta 25 s a todos los que vienen detras.
    """
    espera = ESPERA_REINTENTO_BASE * (4 ** intentos)
    logger.info("Reintentando el correo a %s en %ss (intento %s de %s)",
                _ofuscar(destino), espera, intentos + 2, MAX_REINTENTOS + 1)

    global _reintentos_en_espera
    with _candado_reintentos:
        _reintentos_en_espera += 1

    def _reencolar():
        global _reintentos_en_espera
        try:
            _asegurar_enviador()
            _cola.put((aplicacion, mensaje, destino, cfg, remitente, intentos + 1))
        finally:
            with _candado_reintentos:
                _reintentos_en_espera -= 1

    # Demonio: un reintento pendiente no debe impedir que el proceso se apague.
    temporizador = threading.Timer(espera, _reencolar)
    temporizador.daemon = True
    temporizador.start()
    return temporizador


def correos_pendientes():
    """Cuantos correos quedan por salir. Util para diagnosticar.

    Incluye los reintentos que estan esperando su turno: durante la espera no
    estan en la cola, pero siguen sin entregarse.
    """
    return _cola.qsize() + _reintentos_en_espera


@atexit.register
def _vaciar_cola_al_salir():
    """Da un margen para que salgan los correos encolados al apagar el proceso.

    Sin esto, un reinicio del contenedor en mitad de una importacion perderia
    los correos que aun no habian salido, y esas personas se quedarian sin sus
    credenciales sin que nadie se entere.
    """
    if not correos_pendientes():
        return
    logger.info("Esperando a que salgan %s correos pendientes...",
                correos_pendientes())
    fin = time.time() + 30
    while correos_pendientes() and time.time() < fin:
        time.sleep(0.5)
    if correos_pendientes():
        logger.warning("Quedaron %s correos sin enviar al apagar.",
                       correos_pendientes())


def probar_conexion():
    """Comprueba la configuración SMTP sin enviar nada.

    Devuelve (ok, mensaje). Sirve para verificar las credenciales al desplegar,
    en vez de descubrir que no funcionan cuando alguien no recibe su código.
    """
    cfg = configuracion_smtp()
    if not cfg['servidor']:
        return False, 'Falta MAIL_SERVER.'

    try:
        if cfg['cifrado'] == 'ssl':
            conexion = smtplib.SMTP_SSL(cfg['servidor'], cfg['puerto'],
                                        timeout=TIEMPO_ESPERA,
                                        context=ssl.create_default_context())
        else:
            conexion = smtplib.SMTP(cfg['servidor'], cfg['puerto'],
                                    timeout=TIEMPO_ESPERA)
            if cfg['cifrado'] == 'starttls':
                conexion.starttls(context=ssl.create_default_context())

        if cfg['usuario'] and cfg['clave']:
            conexion.login(cfg['usuario'], cfg['clave'])
        conexion.quit()
        return True, (f"Conexión correcta con {cfg['servidor']}:{cfg['puerto']} "
                      f"(cifrado: {cfg['cifrado']}).")
    except smtplib.SMTPAuthenticationError:
        return False, ('El servidor rechazó las credenciales. Si es Gmail, hay '
                       'que generar una contraseña de aplicación.')
    except Exception as error:
        return False, f"No se pudo conectar: {error}"
