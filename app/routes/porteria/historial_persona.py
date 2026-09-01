"""Historial de ingresos por persona.

Responde a una necesidad concreta de porteria e instructores: saber cuando
entro y cuando salio alguien, que equipos traia, que dias asistio y que dias
falto. La misma vista sirve para una sola persona o para un grupo (una ficha
completa, o todos los de un cargo).

Nota de zona horaria: las fechas se guardan ya en hora de Colombia y sin
tzinfo (ver app/utils/get_colombia_time). Aqui NO se convierte nada desde UTC;
hacerlo desfasaria todos los reportes cinco horas.
"""
from datetime import datetime, time, timedelta

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import porteria_bp as bp
from ... import db
from ...models.accesos import Acceso
from ...models.entidades import Equipo
from ...models.usuarios import Usuario
from ...utils import get_colombia_time, parsear_fecha_bd

# Ventana por defecto cuando el usuario no elige fechas.
DIAS_POR_DEFECTO = 30

# Tope de personas por consulta. Sin el, filtrar por un cargo masivo (todos
# los aprendices) traeria miles de accesos a memoria en una sola peticion.
MAXIMO_PERSONAS = 300

# Tope de movimientos que se muestran en la tabla detallada. Los resumenes
# (dias asistidos, faltas) se calculan sobre TODOS los movimientos del
# periodo, no solo sobre los que se alcanzan a listar.
MAXIMO_MOVIMIENTOS_LISTADOS = 500

# El cierre automatico de medianoche (app/utils/tareas.py) inserta salidas a
# las 23:59:59. Se marcan aparte porque no son una salida real de la persona.
HORA_CIERRE_AUTOMATICO = time(23, 59, 59)

DIAS_SEMANA = ('Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes',
               'Sabado', 'Domingo')


# --------------------------------------------------------------------------
# Permisos
# --------------------------------------------------------------------------
def puede_consultar_a_terceros(usuario):
    """Quien puede pedir el historial de otras personas.

    Porteria y administracion ya ven estos movimientos en el panel en vivo, e
    instructores necesitan el ausentismo de su ficha. El resto solo puede
    consultarse a si mismo.
    """
    return bool(usuario.puede_operar_porteria or usuario.puede_gestionar_asistencia)


def _sin_permiso(mensaje, es_json):
    if es_json:
        return jsonify({'estado': 'error', 'mensaje': mensaje}), 403
    flash(mensaje, 'danger')
    return redirect(url_for('usuarios.profile'))


# --------------------------------------------------------------------------
# Lectura de filtros
# --------------------------------------------------------------------------
def _leer_fecha(texto, por_defecto):
    if not texto:
        return por_defecto
    try:
        return datetime.strptime(texto.strip(), '%Y-%m-%d').date()
    except ValueError:
        return por_defecto


def _leer_filtros(argumentos):
    """Normaliza los parametros de la peticion a un diccionario de filtros."""
    hoy = get_colombia_time().date()
    fecha_fin = _leer_fecha(argumentos.get('fecha_fin'), hoy)
    fecha_inicio = _leer_fecha(argumentos.get('fecha_inicio'),
                               fecha_fin - timedelta(days=DIAS_POR_DEFECTO - 1))
    # Un rango invertido no es un error del usuario que valga la pena
    # rechazar: se endereza y se sigue.
    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    identificadores = []
    for crudo in argumentos.getlist('usuario_id'):
        for parte in str(crudo).split(','):
            parte = parte.strip()
            if parte.isdigit():
                identificadores.append(int(parte))

    return {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'usuario_ids': sorted(set(identificadores)),
        'ficha': (argumentos.get('ficha') or '').strip(),
        'cargo': (argumentos.get('cargo') or '').strip(),
        'busqueda': (argumentos.get('busqueda') or '').strip(),
        'solo_habiles': argumentos.get('solo_habiles', '1') != '0',
    }


def _buscar_personas(filtros):
    """Devuelve las personas que cumplen los filtros, en una sola consulta."""
    consulta = Usuario.query
    if filtros['usuario_ids']:
        consulta = consulta.filter(Usuario.id.in_(filtros['usuario_ids']))
    if filtros['ficha']:
        consulta = consulta.filter(Usuario.ficha == filtros['ficha'])
    if filtros['cargo']:
        consulta = consulta.filter(Usuario.cargo == filtros['cargo'])
    if filtros['busqueda']:
        # `%` y `_` son comodines de SQL: sin escaparlos, buscar "%" devolvía
        # el centro entero (nombre, documento, ficha y patrón horario de todo
        # el mundo, incluidos administradores) a cualquiera con permiso de
        # consulta. Con el escape, un `%` escrito por el usuario se busca como
        # el carácter literal que es.
        termino = (filtros['busqueda']
                   .replace('\\', '\\\\')
                   .replace('%', '\\%')
                   .replace('_', '\\_'))
        patron = f"%{termino}%"
        consulta = consulta.filter(db.or_(
            Usuario.nombre.ilike(patron, escape='\\'),
            Usuario.documento.ilike(patron, escape='\\')))
    return consulta.order_by(Usuario.nombre).limit(MAXIMO_PERSONAS).all()


# --------------------------------------------------------------------------
# Construccion del historial
# --------------------------------------------------------------------------
def _nombres_de_equipos(accesos):
    """Traduce los ids de equipos_str a nombres, en UNA sola consulta.

    equipos_str guarda ids separados por coma (ver scanner.register_movement).
    Resolverlos uno a uno por movimiento seria el clasico N+1 que ya sufre el
    panel, asi que se recogen todos los ids primero.
    """
    ids = set()
    for acceso in accesos:
        for parte in (acceso.equipos_str or '').split(','):
            parte = parte.strip()
            if parte.isdigit():
                ids.add(int(parte))
    if not ids:
        return {}
    return {e.id: e.nombre
            for e in Equipo.query.filter(Equipo.id.in_(ids)).all()}


def _equipos_de(acceso, catalogo):
    """Nombres de los equipos de un movimiento.

    Un equipo pudo borrarse despues de registrarse el ingreso; en ese caso se
    conserva el rastro con el id en lugar de ocultar el dato.
    """
    nombres = []
    for parte in (acceso.equipos_str or '').split(','):
        parte = parte.strip()
        if not parte.isdigit():
            continue
        identificador = int(parte)
        nombres.append(catalogo.get(identificador,
                                    f'Equipo eliminado (#{identificador})'))
    return nombres


def _es_cierre_automatico(momento):
    return momento is not None and momento.time() == HORA_CIERRE_AUTOMATICO


def _emparejar(accesos, catalogo_equipos):
    """Empareja Entrada -> Salida en orden cronologico.

    Casos que hay que soportar porque ocurren de verdad:
    - entrada sin salida (la persona sigue adentro, o nunca se registro),
    - dos entradas seguidas (la primera queda sin salida),
    - una salida sin entrada previa dentro del periodo consultado.
    """
    movimientos = []
    pendiente = None

    for acceso in accesos:
        momento = parsear_fecha_bd(acceso.fecha)
        if momento is None:
            continue
        equipos = _equipos_de(acceso, catalogo_equipos)

        if acceso.tipo == 'Entrada':
            if pendiente is not None:
                movimientos.append(pendiente)
            pendiente = {
                'fecha': momento.date(),
                'entrada': momento,
                'salida': None,
                'equipos': equipos,
                'cierre_automatico': False,
            }
        elif acceso.tipo == 'Salida':
            if pendiente is None:
                # Salida huerfana: la entrada quedo fuera del rango pedido.
                movimientos.append({
                    'fecha': momento.date(),
                    'entrada': None,
                    'salida': momento,
                    'equipos': equipos,
                    'cierre_automatico': _es_cierre_automatico(momento),
                })
                continue
            pendiente['salida'] = momento
            pendiente['cierre_automatico'] = _es_cierre_automatico(momento)
            # Los equipos se registran en la entrada; si la salida trae otros,
            # se suman sin duplicar para no perder informacion.
            for nombre in equipos:
                if nombre not in pendiente['equipos']:
                    pendiente['equipos'].append(nombre)
            movimientos.append(pendiente)
            pendiente = None

    if pendiente is not None:
        movimientos.append(pendiente)

    for movimiento in movimientos:
        movimiento['permanencia_minutos'] = (
            int((movimiento['salida'] - movimiento['entrada']).total_seconds() // 60)
            if movimiento['entrada'] and movimiento['salida'] else None)
    return movimientos


def dias_esperados(fecha_inicio, fecha_fin, solo_habiles=True, hoy=None):
    """Dias del periodo en los que se esperaba asistencia.

    No se cuentan dias futuros: faltar a un dia que todavia no llega no es
    una falta. Por defecto solo lunes a viernes, que es cuando hay formacion.
    """
    limite = min(fecha_fin, hoy or get_colombia_time().date())
    dias = []
    actual = fecha_inicio
    while actual <= limite:
        if not solo_habiles or actual.weekday() < 5:
            dias.append(actual)
        actual += timedelta(days=1)
    return dias


def _resumir(movimientos, esperados):
    """Resumen de asistencia de una persona sobre el periodo consultado."""
    asistidos = sorted({m['fecha'] for m in movimientos})
    conjunto_asistidos = set(asistidos)
    faltados = [d for d in esperados if d not in conjunto_asistidos]

    faltas_por_dia_semana = {}
    for dia in faltados:
        etiqueta = DIAS_SEMANA[dia.weekday()]
        faltas_por_dia_semana[etiqueta] = faltas_por_dia_semana.get(etiqueta, 0) + 1
    dia_mas_faltado = None
    if faltas_por_dia_semana:
        dia_mas_faltado = max(faltas_por_dia_semana.items(),
                              key=lambda par: par[1])[0]

    minutos = [m['permanencia_minutos'] for m in movimientos
               if m['permanencia_minutos'] is not None]

    return {
        'dias_asistidos': asistidos,
        'total_dias_asistidos': len(asistidos),
        'dias_faltados': faltados,
        'total_dias_faltados': len(faltados),
        'total_dias_esperados': len(esperados),
        'porcentaje_asistencia': (round(len(asistidos) * 100 / len(esperados), 1)
                                  if esperados else 0.0),
        'faltas_por_dia_semana': faltas_por_dia_semana,
        'dia_mas_faltado': dia_mas_faltado,
        'total_movimientos': len(movimientos),
        'sin_salida': sum(1 for m in movimientos if m['salida'] is None),
        'promedio_permanencia_minutos': (round(sum(minutos) / len(minutos))
                                         if minutos else None),
    }


def construir_historial(personas, fecha_inicio, fecha_fin, solo_habiles=True):
    """Historial y resumen de asistencia de varias personas.

    Hace DOS consultas en total (accesos + equipos), no una por persona: el
    caso real es consultar una ficha completa de 30 personas o mas.
    """
    if not personas:
        return []

    identificadores = [p.id for p in personas]
    inicio = datetime.combine(fecha_inicio, time.min)
    fin = datetime.combine(fecha_fin, time.max)

    accesos = (Acceso.query
               .filter(Acceso.referencia_id.in_(identificadores),
                       # referencia_id es polimorfico: sin este filtro el
                       # visitante 7 se mezclaria con el usuario 7.
                       Acceso.tipo_referencia == 'Usuario',
                       Acceso.fecha >= inicio,
                       Acceso.fecha <= fin)
               .order_by(Acceso.referencia_id, Acceso.fecha, Acceso.id)
               .all())

    catalogo_equipos = _nombres_de_equipos(accesos)

    por_persona = {identificador: [] for identificador in identificadores}
    for acceso in accesos:
        por_persona[acceso.referencia_id].append(acceso)

    esperados = dias_esperados(fecha_inicio, fecha_fin, solo_habiles)

    resultado = []
    for persona in personas:
        movimientos = _emparejar(por_persona[persona.id], catalogo_equipos)
        resultado.append({
            'persona': persona,
            'movimientos': movimientos,
            'movimientos_listados': movimientos[-MAXIMO_MOVIMIENTOS_LISTADOS:],
            'resumen': _resumir(movimientos, esperados),
        })
    return resultado


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------
def _resolver_consulta(argumentos, es_json):
    """Aplica permisos y filtros. Devuelve (datos, filtros, respuesta_error)."""
    filtros = _leer_filtros(argumentos)

    if not puede_consultar_a_terceros(current_user):
        # Control de acceso a nivel de objeto: cualquiera puede ver su propio
        # historial, pero pedir el de otra persona es un 403, no un filtro
        # que se corrige en silencio.
        pedidos = set(filtros['usuario_ids'])
        if pedidos - {current_user.id}:
            return None, filtros, _sin_permiso(
                'Solo puedes consultar tu propio historial de ingresos.', es_json)
        # Los filtros por grupo tampoco aplican: se fuerza a si mismo.
        filtros['usuario_ids'] = [current_user.id]
        filtros['ficha'] = ''
        filtros['cargo'] = ''
        filtros['busqueda'] = ''

    if not (filtros['usuario_ids'] or filtros['ficha'] or filtros['cargo']
            or filtros['busqueda']):
        # Sin ningun filtro no se listan todas las personas del centro: se
        # devuelve la pantalla vacia con el formulario.
        return [], filtros, None

    personas = _buscar_personas(filtros)
    datos = construir_historial(personas, filtros['fecha_inicio'],
                                filtros['fecha_fin'], filtros['solo_habiles'])
    return datos, filtros, None


@bp.route('/historial-persona')
@login_required
def historial_persona():
    """Pagina de consulta del historial de ingresos."""
    datos, filtros, error = _resolver_consulta(request.args, es_json=False)
    if error is not None:
        return error

    puede_terceros = puede_consultar_a_terceros(current_user)
    cargos = []
    if puede_terceros:
        cargos = [fila[0] for fila in db.session.query(Usuario.cargo)
                  .filter(Usuario.cargo.isnot(None))
                  .distinct().order_by(Usuario.cargo).all() if fila[0]]

    return render_template(
        'porteria/historial_persona.html',
        datos=datos,
        filtros=filtros,
        cargos=cargos,
        puede_consultar_terceros=puede_terceros,
        hubo_busqueda=bool(filtros['usuario_ids'] or filtros['ficha']
                           or filtros['cargo'] or filtros['busqueda']),
        maximo_personas=MAXIMO_PERSONAS,
    )


@bp.route('/api/historial-persona')
@login_required
def api_historial_persona():
    """Misma consulta en JSON, para exportar o consumir desde el panel."""
    datos, filtros, error = _resolver_consulta(request.args, es_json=True)
    if error is not None:
        return error

    def formatear(momento):
        return momento.strftime('%Y-%m-%d %H:%M:%S') if momento else None

    return jsonify({
        'estado': 'ok',
        'fecha_inicio': filtros['fecha_inicio'].isoformat(),
        'fecha_fin': filtros['fecha_fin'].isoformat(),
        'personas': [{
            'id': bloque['persona'].id,
            'nombre': bloque['persona'].nombre,
            'documento': bloque['persona'].documento,
            'cargo': bloque['persona'].cargo,
            'ficha': bloque['persona'].ficha,
            'programa': bloque['persona'].programa,
            'resumen': {
                'dias_asistidos': [d.isoformat()
                                   for d in bloque['resumen']['dias_asistidos']],
                'dias_faltados': [d.isoformat()
                                  for d in bloque['resumen']['dias_faltados']],
                'total_dias_asistidos': bloque['resumen']['total_dias_asistidos'],
                'total_dias_faltados': bloque['resumen']['total_dias_faltados'],
                'total_dias_esperados': bloque['resumen']['total_dias_esperados'],
                'porcentaje_asistencia': bloque['resumen']['porcentaje_asistencia'],
                'dia_mas_faltado': bloque['resumen']['dia_mas_faltado'],
                'faltas_por_dia_semana': bloque['resumen']['faltas_por_dia_semana'],
                'promedio_permanencia_minutos':
                    bloque['resumen']['promedio_permanencia_minutos'],
                'sin_salida': bloque['resumen']['sin_salida'],
            },
            'movimientos': [{
                'fecha': m['fecha'].isoformat(),
                'entrada': formatear(m['entrada']),
                'salida': formatear(m['salida']),
                'permanencia_minutos': m['permanencia_minutos'],
                'equipos': m['equipos'],
                'cierre_automatico': m['cierre_automatico'],
            } for m in bloque['movimientos_listados']],
        } for bloque in datos],
    })
