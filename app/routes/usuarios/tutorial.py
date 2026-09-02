"""Tutorial de primer ingreso: recorrido guiado y version en texto.

Quien entra por primera vez no sabe que el código de barras no se activa solo: hay que
completar el perfil, subir una foto que cumpla requisitos y esperar la
aprobacion de un asesor. Explicarlo de entrada evita que la persona llegue a
porteria con el carnet bloqueado sin saber por que.

El recorrido interactivo vive en static/js/tutorial.js; aqui va la version en
texto (consultable las veces que haga falta) y el endpoint que deja constancia
de que la persona ya vio el recorrido, para no repetirselo en cada ingreso.
"""
from flask import jsonify, render_template
from flask_login import current_user, login_required

from ... import db
from . import bp

# Version en texto del mismo flujo que recorre el tutorial interactivo.
# Cada paso lleva un ejemplo concreto: decir "completa tu perfil" no ayuda
# tanto como mostrar que un documento se escribe "1098765432" y no "1.098.765.432".
PASOS_TUTORIAL = [
    {
        'titulo': 'Completa tu información personal',
        'icono': 'fa-user-edit',
        'descripcion': (
            'En "Mi Perfil", presiona el botón "Información" y diligencia todos '
            'los campos: tipo y número de documento, tipo de sangre, y si eres '
            'aprendiz también tu programa de formación y número de ficha. '
            'Sin estos datos el carnet digital no se puede activar.'),
        'ejemplo': (
            'Documento: elige "Cédula de ciudadanía" y escribe el número sin '
            'puntos ni espacios, por ejemplo 1098765432 (no 1.098.765.432). '
            'Ficha: el número que aparece en tu carta de aceptación, por '
            'ejemplo 2758291.'),
    },
    {
        'titulo': 'Sube tu foto de perfil',
        'icono': 'fa-camera',
        'descripcion': (
            'En el mismo formulario de "Información" sube una foto tuya. En '
            'portería el celador la compara contigo para dejarte entrar, así '
            'que debe cumplir los requisitos: solo tú en la imagen, rostro '
            'despejado y bien visible, con buena luz, de frente y de cerca.'),
        'ejemplo': (
            'Sirve: una foto tipo documento, tomada de frente en un lugar '
            'iluminado, con gafas si las usas normalmente. No sirve: una foto '
            'con gorra o mascarilla, a contraluz, movida, o donde aparezca '
            'alguien más aunque sea de fondo.'),
    },
    {
        'titulo': 'Espera la aprobación de un asesor',
        'icono': 'fa-user-check',
        'descripcion': (
            'Un asesor revisa tu foto manualmente. Hasta que la apruebe, tu '
            'carnet digital y tu código de barras permanecen bloqueados. Si la '
            'rechaza, el motivo te llega por correo y a tus Mensajes, y debes '
            'subir una nueva.'),
        'ejemplo': (
            'Mientras esperas puedes entrar al centro presentando tu documento '
            'físico en portería. Si llevas varios días sin respuesta, escribe '
            'por "Mensajes" y un asesor te atiende.'),
    },
    {
        'titulo': 'Registra tus equipos',
        'icono': 'fa-laptop',
        'descripcion': (
            'Si vas a entrar con portátil, tablet u otro equipo tecnológico, '
            'regístralo antes en "Mi Perfil" → "Añadir Equipos". El celador '
            'marca cuáles traes al entrar y al salir. Puedes registrar hasta 5.'),
        'ejemplo': (
            'Serial: el código que está en la etiqueta de la parte de abajo '
            'del portátil, por ejemplo 5CD1234XYZ. Nombre: algo que lo '
            'identifique, como "Portátil HP negro".'),
    },
    {
        'titulo': 'Usa tu código de barras en portería',
        'icono': 'fa-qrcode',
        'descripcion': (
            'Cuando tu perfil esté completo y tu foto aprobada, el código de barras aparece '
            'en tu carnet digital, en "Mi Perfil". Preséntalo al escáner de '
            'portería al entrar y al salir del centro.'),
        'ejemplo': (
            'Toca el código de barras de tu carnet para agrandarlo y acércalo al lector con '
            'la pantalla con buen brillo. También puedes descargar el carnet '
            'como imagen con el botón "Descargar Carnet Institucional".'),
    },
    {
        'titulo': '¿Algo falla? Tienes ayuda dentro del sistema',
        'icono': 'fa-circle-question',
        'descripcion': (
            'En el "Centro de Ayuda" del menú están las respuestas a las dudas '
            'más comunes (foto rechazada, código de barras que no aparece, ficha mal '
            'escrita). Y en "Mensajes" puedes hablar directamente con un '
            'asesor sin tener que buscar a nadie en portería.'),
        'ejemplo': (
            'Ejemplo: si el sistema rechaza tu foto y no entiendes el motivo, '
            'abre "Centro de Ayuda", elige el asunto "Problema con mi foto de '
            'perfil" y cuenta qué te sale. La respuesta llega a "Mensajes".'),
    },
]


@bp.route('/tutorial')
@login_required
def tutorial_texto():
    """Version en texto del tutorial, con ejemplos de como hacer cada paso."""
    return render_template('usuarios/tutorial.html', pasos=PASOS_TUTORIAL)


@bp.route('/tutorial/completar', methods=['POST'])
@login_required
def tutorial_completar():
    """Deja constancia de que la persona ya vio el recorrido guiado.

    Opera siempre sobre current_user y no acepta parametros: no existe forma
    de marcar el tutorial de otra persona, ni siquiera enviando un id ajeno
    en el cuerpo de la peticion.
    """
    if not current_user.tutorial_visto:
        current_user.tutorial_visto = True
        db.session.commit()
    return jsonify({'status': 'success'})
