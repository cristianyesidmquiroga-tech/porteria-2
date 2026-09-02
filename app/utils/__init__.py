from datetime import datetime, timezone, timedelta

ZONA_COLOMBIA = timezone(timedelta(hours=-5))

_FORMATOS_FECHA = ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S')


def get_colombia_time():
    """Fecha y hora actual en Colombia (UTC-5) como objeto naive.

    Toda la aplicacion guarda las fechas con esta funcion, es decir en hora
    local de Colombia y sin zona horaria. Por lo tanto, al mostrarlas NO hay
    que convertirlas: ya estan en la hora correcta.
    """
    return datetime.now(ZONA_COLOMBIA).replace(tzinfo=None)


def parsear_fecha_bd(valor):
    """Normaliza una fecha leida de la base a datetime naive en hora Colombia.

    SQLite puede devolver cadenas donde PostgreSQL devuelve datetime, por eso
    se acepta cualquiera de los dos. Devuelve None si no se puede interpretar.
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        # Si viniera con zona horaria, se pasa a hora de Colombia y se
        # descarta el tzinfo para que sea comparable con el resto.
        if valor.tzinfo is not None:
            return valor.astimezone(ZONA_COLOMBIA).replace(tzinfo=None)
        return valor
    for formato in _FORMATOS_FECHA:
        try:
            return datetime.strptime(str(valor), formato)
        except ValueError:
            continue
    return None
