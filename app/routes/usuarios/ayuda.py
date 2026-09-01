"""Centro de ayuda: preguntas frecuentes y puente con un asesor.

La mayoría de las dudas se repiten (cómo activar el carnet, por qué rechazaron
la foto, qué hacer si la ficha está mal). Resolverlas por escrito descarga a
quien asesora y le da respuesta inmediata a quien pregunta a las 10 de la noche.

Para lo que no está en la lista, el mismo centro abre la conversación con un
asesor sin que la persona tenga que buscar a nadie en portería.
"""
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ... import db
from ...models.mensajes import registrar_mensaje
from .mensajes import _texto_valido
from ...utils.security import sanitize_html
from . import bp

# Cada bloque es una pregunta con su respuesta. El orden es el de frecuencia
# esperada: primero lo que bloquea a la persona para poder entrar al centro.
PREGUNTAS_FRECUENTES = [
    {
        'categoria': 'Carnet digital',
        'pregunta': '¿Por qué no me aparece el código de barras?',
        'respuesta': (
            'El código de barras aparece solo cuando tu perfil está completo Y tu foto fue '
            'aprobada por un asesor. Revisa en "Mi Perfil" que tengas: documento, '
            'tipo de sangre, foto, y si eres aprendiz también tu ficha de formación '
            '(el programa y la fecha de finalización se heredan de ella). '
            'Si ya lo tienes todo, tu foto puede estar todavía en revisión.'),
    },
    {
        'categoria': 'Carnet digital',
        'pregunta': '¿Cuánto tarda en revisarse mi foto?',
        'respuesta': (
            'La revisa un asesor manualmente, así que depende de la carga del día. '
            'Mientras tanto puedes entrar al centro presentando tu documento físico '
            'en portería. Si llevas varios días esperando, escríbenos.'),
    },
    {
        'categoria': 'Foto de perfil',
        'pregunta': '¿Cómo debe ser mi foto?',
        'respuesta': (
            'Debe salir solo tu rostro, de frente y de cerca, tipo foto de documento. '
            'Con buena luz, sin contraluz y sin flash directo. Sin gorra, capucha, '
            'mascarilla ni bufanda que te tape la cara. Puedes usar gafas o lentes '
            'si los llevas normalmente. Puedes tomarla en el momento o subir una de '
            'tu galería, pero tiene que ser una foto real tuya.'),
    },
    {
        'categoria': 'Foto de perfil',
        'pregunta': 'El sistema me rechaza la foto, ¿qué hago?',
        'respuesta': (
            'El mensaje de error te dice qué corregir. Los casos más comunes son: '
            'la foto está movida (apoya el celular y enfoca), está muy oscura '
            '(busca un lugar claro y ponte de frente a la luz), sale más de una '
            'persona, o el rostro se ve muy pequeño (acércate más). Si no logras '
            'que la acepte, escríbenos y te ayudamos.'),
    },
    {
        'categoria': 'Foto de perfil',
        'pregunta': 'Un asesor rechazó mi foto, ¿por qué?',
        'respuesta': (
            'El motivo te llega por correo y también queda en tus Mensajes dentro '
            'del sistema. Ahí mismo puedes responder si no entiendes qué corregir. '
            'La foto rechazada se borra, así que tienes que subir una nueva.'),
    },
    {
        'categoria': 'Mis datos',
        'pregunta': 'Mi ficha o mi programa están mal, ¿cómo los corrijo?',
        'respuesta': (
            'Puedes editarlos tú desde "Mi Perfil" → "Información". Si el sistema '
            'no te deja porque dice que hay una inconsistencia con la ficha, '
            'escríbenos por Mensajes: eso significa que otro aprendiz de tu misma '
            'ficha tiene un programa u horario distinto y hay que revisarlo.'),
    },
    {
        'categoria': 'Mis datos',
        'pregunta': '¿Qué número de documento debo poner?',
        'respuesta': (
            'El de tu documento de identidad, sin puntos ni espacios, y elige el '
            'tipo que corresponda: cédula de ciudadanía, tarjeta de identidad si '
            'eres menor de edad, cédula de extranjería, PPT o pasaporte. El sistema '
            'valida que la cantidad de dígitos sea la correcta para ese tipo.'),
    },
    {
        'categoria': 'Equipos',
        'pregunta': '¿Tengo que registrar mi computador?',
        'respuesta': (
            'Sí, si vas a entrar con un portátil, tablet u otro equipo tecnológico, '
            'regístralo antes en "Mi Perfil" → "Añadir Equipos". En portería el '
            'celador marca cuáles traes contigo al entrar y al salir. Puedes '
            'registrar hasta 5 equipos.'),
    },
    {
        'categoria': 'Acceso',
        'pregunta': 'No puedo iniciar sesión, dice que estoy bloqueado',
        'respuesta': (
            'Tras 5 intentos fallidos la cuenta se bloquea 10 minutos por seguridad. '
            'Espera ese tiempo y vuelve a intentar. Si no recuerdas tu contraseña, '
            'usa "¿Olvidaste tu contraseña?" en la pantalla de ingreso.'),
    },
    {
        'categoria': 'Acceso',
        'pregunta': 'No me llega el correo de verificación',
        'respuesta': (
            'Revisa la carpeta de spam o correo no deseado. Desde la pantalla de '
            'verificación puedes pedir que te reenvíen el código. Si tu correo '
            'quedó mal escrito al registrarte, escríbenos para corregirlo.'),
    },
    {
        'categoria': 'Privacidad',
        'pregunta': '¿Qué hacen con mi foto y mis datos?',
        'respuesta': (
            'Se usan únicamente para controlar el ingreso a la sede y para que el '
            'celador confirme tu identidad en portería. No se comparten con '
            'terceros. Puedes consultar el detalle en la Política de Tratamiento '
            'de Datos Personales, enlazada al final de cualquier página.'),
    },
]

# Asuntos con los que se puede abrir una conversación, para que el mensaje
# llegue ya encuadrado y el asesor no tenga que preguntar de qué se trata.
ASUNTOS = [
    'No puedo activar mi carnet',
    'Problema con mi foto de perfil',
    'Mis datos están mal (ficha, programa, documento)',
    'Problema para iniciar sesión',
    'Problema con el registro de un equipo',
    'Otro',
]


@bp.route('/ayuda')
@login_required
def centro_ayuda():
    categorias = []
    for item in PREGUNTAS_FRECUENTES:
        if not categorias or categorias[-1]['nombre'] != item['categoria']:
            categorias.append({'nombre': item['categoria'], 'preguntas': []})
        categorias[-1]['preguntas'].append(item)

    return render_template('usuarios/ayuda.html', categorias=categorias,
                           asuntos=ASUNTOS)


@bp.route('/ayuda/contactar', methods=['POST'])
@login_required
def contactar_asesor():
    """Abre la conversación con un asesor desde el centro de ayuda."""
    asunto = (sanitize_html(request.form.get('asunto')) or '').strip()

    # Se valida con la MISMA funcion que el envio normal de mensajes: escriben
    # en la misma tabla, y aqui no habia tope de longitud, asi que se podia
    # llenar la base con textos de megabytes.
    detalle, error = _texto_valido(request.form.get('detalle'))
    if error:
        flash(error, 'warning')
        return redirect(url_for('usuarios.centro_ayuda'))

    if asunto and asunto in ASUNTOS and asunto != 'Otro':
        texto = f'[{asunto}]\n\n{detalle}'
    else:
        texto = detalle

    registrar_mensaje(current_user.id, current_user, texto)
    db.session.commit()

    flash('Tu mensaje fue enviado. Un asesor te responderá en Mensajes.', 'success')
    return redirect(url_for('usuarios.mis_mensajes'))
