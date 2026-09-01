"""Emisión del desafío anti-bot.

Vive en el blueprint de auth porque solo lo usan sus formularios públicos
(registro y recuperación de contraseña).
"""
from flask import jsonify

from ...utils.captcha import captcha_activo, crear_desafio
from . import bp


@bp.route('/captcha/desafio')
def captcha_desafio():
    # Si el desafío está apagado se responde igual (no 404): así el widget
    # sabe que debe apartarse en vez de quedarse en "verificando" para siempre.
    if not captcha_activo():
        return jsonify({'activo': False})
    return jsonify(crear_desafio())
