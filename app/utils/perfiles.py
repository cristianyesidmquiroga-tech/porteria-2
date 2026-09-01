"""Cuándo un perfil está lo bastante completo para emitir el carnet.

Esta regla vivía suelta dentro de la vista `usuarios.update_profile`, así que
solo se aplicaba cuando la propia persona guardaba su perfil. El panel de
administración cambia los mismos campos de los que depende —sobre todo el
cargo, que es lo que decide si se exige ficha— y no recalculaba nada: pasar a
alguien a "Aprendiz" dejaba `perfil_completo` en verdadero y se emitía un
carnet de aprendiz con la ficha y la fecha de finalización vacías.

Se extrae aquí para que ambos caminos lleguen a la misma conclusión. La vista
de perfil todavía lleva su propia copia en línea; al tocarla debe pasar a
llamar a `perfil_esta_completo` en lugar de repetir la comprobación.
"""

# Nombres de archivo que no son una foto real de la persona. Los antiguos
# siguen listados porque pueden persistir en la columna `foto` de una base
# creada antes de los avatares por cargo.
FOTOS_MARCADOR = (None, '', 'default-profile.png', 'default_profile.png')


def tiene_foto_propia(usuario):
    """La persona subió una foto suya (no el avatar genérico del cargo)."""
    return usuario.foto not in FOTOS_MARCADOR


def perfil_esta_completo(usuario):
    """Devuelve si el carnet de `usuario` puede activarse.

    El carnet solo se activa con la foto ya aprobada por un administrador: esa
    revisión es lo que le da valor a la verificación en portería.
    """
    from ..models.usuarios import ESTADO_APROBADA

    requeridos = [usuario.documento, usuario.tipo_sangre, usuario.foto]
    if usuario.es_aprendiz_cargo:
        # La ficha basta: de ella cuelgan el programa y la fecha. Se acepta
        # también la ficha en texto de quien ya la tenía antes de que
        # existiera la tabla, para no invalidarle un carnet que ya funcionaba.
        requeridos.append(usuario.ficha_id or usuario.ficha)

    return bool(all(requeridos)
                and tiene_foto_propia(usuario)
                and usuario.foto_estado == ESTADO_APROBADA)
