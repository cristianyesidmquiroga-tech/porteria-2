"""Comprueba la configuración de correo sin molestar a nadie.

Uso:
    python scripts/probar_correo.py                    # prueba la conexión SMTP
    python scripts/probar_correo.py --puerto-25        # ¿está abierto el 25 de salida?
    python scripts/probar_correo.py --enviar tu@correo.com   # envía uno de prueba

Ejecútalo EN EL SERVIDOR, no en tu computador: lo que importa es lo que puede
hacer la máquina donde corre la aplicación.
"""
import os
import socket
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def probar_puerto_25():
    """Comprueba si el servidor puede abrir conexiones salientes al puerto 25.

    Es LA pregunta que decide si el modo 'directo' puede funcionar: la mayoría
    de proveedores de VPS lo bloquean, y en ese caso no hay nada que programar.
    """
    destinos = [('gmail-smtp-in.l.google.com', 'Gmail'),
                ('outlook-com.olc.protection.outlook.com', 'Outlook')]
    print("Comprobando el puerto 25 de SALIDA desde este servidor...\n")
    alguno = False
    for host, nombre in destinos:
        sock = socket.socket()
        sock.settimeout(8)
        try:
            sock.connect((host, 25))
            print(f"  {nombre:9} ABIERTO")
            alguno = True
        except Exception as error:
            print(f"  {nombre:9} BLOQUEADO ({type(error).__name__})")
        finally:
            sock.close()

    print()
    if alguno:
        print("El puerto 25 está abierto: el modo 'directo' es técnicamente posible.")
        print("Aun así hace falta configurar SPF, DKIM, DMARC y DNS inverso (PTR)")
        print("o los correos acabarán en spam.")
    else:
        print("El puerto 25 está bloqueado. El modo 'directo' NO puede funcionar")
        print("desde este servidor. Opciones:")
        print("  1. Pedirle al proveedor del VPS que lo abra (suelen exigir justificación).")
        print("  2. Usar MAIL_MODO=rele con el servidor de correo de la institución.")
    return alguno


def main():
    from app import create_app
    from app.utils.email import configuracion_smtp, enviar_correo, probar_conexion

    if '--puerto-25' in sys.argv:
        probar_puerto_25()
        return

    app = create_app()
    with app.app_context():
        cfg = configuracion_smtp()
        print("Configuración actual:")
        print(f"  modo      : {cfg['modo']}")
        print(f"  servidor  : {cfg['servidor'] or '(sin configurar)'}")
        print(f"  puerto    : {cfg['puerto']}")
        print(f"  cifrado   : {cfg['cifrado']}")
        print(f"  usuario   : {cfg['usuario'] or '(sin configurar)'}")
        print(f"  remitente : {cfg['remitente'] or '(sin configurar)'}")
        print(f"  contraseña: {'configurada' if cfg['clave'] else 'SIN CONFIGURAR'}")
        print()

        ok, mensaje = probar_conexion()
        print(("CONEXIÓN CORRECTA: " if ok else "FALLO: ") + mensaje)

        if '--enviar' in sys.argv:
            destino = sys.argv[sys.argv.index('--enviar') + 1]
            print(f"\nEnviando un correo de prueba a {destino}...")
            enviar_correo(destino, 'Prueba del Sistema de Acceso SENA',
                          '<p>Si lees esto, el envío de correo funciona.</p>')
            import time
            time.sleep(6)
            print("Revisa la bandeja (y la carpeta de spam) y el log de arriba.")


if __name__ == '__main__':
    main()
