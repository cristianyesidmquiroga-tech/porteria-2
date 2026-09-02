"""Historial de ingresos por persona.

Responde a una necesidad concreta de porteria e instructores: saber cuando
entro y cuando salio alguien, que equipos traia, que dias asistio y que dias
falto. La misma vista sirve para una sola persona o para un grupo (una ficha
completa, o todos los de un cargo).

Las tres cifras que la institucion usa para decidir sobre una persona
(porcentaje de asistencia, total de faltas y dia que mas falta) se calculan
aqui, asi que el modulo es explicito sobre que cuenta y que no:

- El periodo exigible es POR PERSONA, no el rango que se tecleo en el
  formulario: nadie falta antes de estar vinculado ni despues de terminar su
  ficha (ver `ventana_exigible`).
- Un dia con marca de entrada O de salida es un dia asistido. El turno
  nocturno sale de madrugada y ese dia no puede figurar como falta.
- El numerador del porcentaje se limita a los mismos dias que el
  denominador; si no, asistir en fin de semana producia 140%.

Nota de zona horaria: las fechas se guardan ya en hora de Colombia y sin
tzinfo (ver app/utils/get_colombia_time). Aqui NO se convierte nada desde UTC;
hacerlo desfasaria todos los reportes cinco horas.
"""
from datetime import datetime, time, timedelta
from fractions import Fraction

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

# Amplitud maxima del rango consultable. El contenedor tiene 1 GB y un solo
# proceso: 300 personas por un anio son ~300 MB y 18 s, que lo bloquean y
# pueden matarlo. El rango se recorta y se avisa, en vez de arriesgar la caida.
MAXIMO_DIAS_RANGO = 120

# Tope de personas por consulta. Sin el, filtrar por un cargo masivo (todos
# los aprendices) traeria miles de accesos a memoria en una sola peticion.
MAXIMO_PERSONAS = 300

# Segundo tope, sobre el volumen real y no sobre el numero de personas: 300
# personas de un dia no pesan lo mismo que 300 de cuatro meses. Se cuentan los
# accesos antes de traerlos y se dejan fuera las personas que no caben, en vez
# de traerlas a medias (una persona con la mitad de sus accesos saldria con
# faltas inventadas).
MAXIMO_ACCESOS = 20000

# Tope de movimientos que se muestran en la tabla detallada. Los resumenes
# (dias asistidos, faltas) se calculan sobre TODOS los movimientos del
# periodo, no solo sobre los que se alcanzan a listar.
MAXIMO_MOVIMIENTOS_LISTADOS = 500

# Se consultan accesos un dia antes y un dia despues del rango pedido para
# poder emparejar entrada y salida, y solo despues se recorta. Sin este
# margen, el filtro cortaba por marca de tiempo y no por pareja: la entrada
# del ultimo dia aparecia como "movimiento sin salida registrada", una
# anomalia de la persona que en realidad la fabricaba el filtro.
MARGEN_EMPAREJADO = timedelta(days=1)

# El cierre automatico de medianoche (app/utils/tareas.py) inserta salidas a
# las 23:59:59 SIN operador. Una salida real a esa hora si lo tiene, porque la
# registra un celador identificado; por eso no basta con mirar la hora.
HORA_CIERRE_AUTOMATICO = time(23, 59, 59)

# Cuantas veces tiene que haber ocurrido un dia de la semana antes de afirmar
# que es "el dia que mas falta". Con dos lunes en el periodo, faltar a uno no
# es un patron de conducta.
MINIMO_OPORTUNIDADES_DIA = 3

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

    rango_recortado = False
    if (fecha_fin - fecha_inicio).days + 1 > MAXIMO_DIAS_RANGO:
        fecha_inicio = fecha_fin - timedelta(days=MAXIMO_DIAS_RANGO - 1)
        rango_recortado = True

    identificadores = []
    for crudo in argumentos.getlist('usuario_id'):
        for parte in str(crudo).split(','):
            parte = parte.strip()
            if parte.isdigit():
                identificadores.append(int(parte))

    return {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'rango_recortado': rango_recortado,
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


def _es_cierre_automatico(acceso, momento):
    """Distingue el cierre de medianoche de una salida real a esa hora.

    La hora sola no alcanza: un celador puede registrar una salida legitima a
    las 23:59:59 y quedaba marcada como automatica. El cierre lo inserta una
    tarea programada, sin usuario que lo respalde, asi que la ausencia de
    operador es lo que de verdad lo identifica.
    """
    if momento is None or momento.time() != HORA_CIERRE_AUTOMATICO:
        return False
    return getattr(acceso, 'operador_id', None) is None


def _dias_con_marca(entrada, salida):
    """Dias con presencia comprobada de un movimiento.

    Cuenta el dia de la entrada y el de la salida. Quien entra el lunes a las
    22:00 y sale el martes a las 06:00 estuvo dentro de la sede los dos dias;
    fechar el movimiento solo por la entrada le anotaba una falta al martes
    por cada noche trabajada.

    Los dias intermedios de un movimiento larguisimo NO se cuentan: si entre
    la entrada y la salida hay una semana, lo que falta son registros, y dar
    por asistidos dias sin ninguna marca seria inventar presencia.
    """
    dias = set()
    if entrada is not None:
        dias.add(entrada.date())
    if salida is not None:
        dias.add(salida.date())
    return dias


def _emparejar(accesos, catalogo_equipos, hoy):
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
                # La entrada existe: si falta algo, es la salida.
                'entrada_fuera_de_ventana': False,
            }
        elif acceso.tipo == 'Salida':
            if pendiente is None:
                # Salida huerfana: la entrada quedo fuera de la ventana leida.
                movimientos.append({
                    'fecha': momento.date(),
                    'entrada': None,
                    'salida': momento,
                    'equipos': equipos,
                    'cierre_automatico': _es_cierre_automatico(acceso, momento),
                    'entrada_fuera_de_ventana': True,
                })
                continue
            pendiente['salida'] = momento
            pendiente['cierre_automatico'] = _es_cierre_automatico(acceso, momento)
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
        entrada, salida = movimiento['entrada'], movimiento['salida']
        movimiento['permanencia_minutos'] = (
            int((salida - entrada).total_seconds() // 60)
            if entrada and salida else None)
        movimiento['dias'] = sorted(_dias_con_marca(entrada, salida))
        movimiento['abierto'] = False

    # Una entrada de hoy sin salida es alguien que sigue adentro, no un
    # registro incompleto. Solo puede estarlo el ULTIMO movimiento: una
    # entrada seguida de otra entrada si es una anomalia real, aunque sea de
    # hoy, porque la persona volvio a entrar sin haber salido.
    if movimientos:
        ultimo = movimientos[-1]
        ultimo['abierto'] = (ultimo['salida'] is None
                             and ultimo['entrada'] is not None
                             and ultimo['entrada'].date() >= hoy)
    return movimientos


def _recortar_al_rango(movimientos, fecha_inicio, fecha_fin):
    """Deja solo los movimientos que tocan el rango pedido.

    Se ejecuta DESPUES de emparejar (ver MARGEN_EMPAREJADO): primero se arma
    la pareja completa con el margen, y solo entonces se descarta lo que
    quedo fuera. Al reves, el corte partia parejas por la mitad.
    """
    dentro = []
    for movimiento in movimientos:
        if not any(fecha_inicio <= dia <= fecha_fin
                   for dia in movimiento['dias']):
            continue
        entrada, salida = movimiento['entrada'], movimiento['salida']
        movimiento['entrada_previa_al_rango'] = (
            entrada is not None and entrada.date() < fecha_inicio)
        movimiento['salida_posterior_al_rango'] = (
            salida is not None and salida.date() > fecha_fin)
        dentro.append(movimiento)
    return dentro


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


def ventana_exigible(persona, fecha_inicio, fecha_fin, primer_acceso, hoy):
    """Recorta el rango pedido al periodo en que la persona SI debia asistir.

    El rango del formulario es una pregunta, no un contrato: un aprendiz
    matriculado hace un mes, consultado desde enero, salia con 8,7% de
    asistencia y 157 faltas por dias en los que ni siquiera pertenecia al
    centro. Un egresado seguia acumulando faltas despues de terminar.

    No existe columna de fecha de vinculacion (ver el reporte): se usa como
    aproximacion la fecha del primer acceso registrado de la persona, y la
    fecha de finalizacion de su ficha para el otro extremo. Devuelve
    (inicio, fin, motivos) donde `motivos` explica en la interfaz por que el
    periodo evaluado no es el que se pidio.
    """
    motivos = []
    inicio, fin = fecha_inicio, fecha_fin

    if primer_acceso is not None and primer_acceso > inicio:
        inicio = primer_acceso
        motivos.append('vinculacion')

    ficha = getattr(persona, 'ficha_ref', None)
    finalizacion = getattr(ficha, 'fecha_finalizacion', None) if ficha else None
    if finalizacion is not None and finalizacion < fin:
        fin = finalizacion
        motivos.append('fin_de_ficha')

    if hoy < fin:
        fin = hoy

    return inicio, fin, motivos


def _dia_mas_faltado(esperados, faltados):
    """Dia de la semana con mayor TASA de inasistencia, o None.

    Comparar conteos brutos medía el calendario, no la conducta: en 30 dias
    hay cinco lunes y cuatro miercoles, asi que quien no asiste nunca salia
    siempre con "Lunes". Se divide entre las veces que ese dia ocurrio, se
    exige un minimo de oportunidades antes de afirmar un patron, y un empate
    se declara empate en vez de devolver el primero de la lista.

    Se usa Fraction y no float para que 2/4 y 3/6 empaten de verdad; con
    coma flotante el empate se decidiria por error de redondeo.
    """
    oportunidades = {}
    for dia in esperados:
        etiqueta = DIAS_SEMANA[dia.weekday()]
        oportunidades[etiqueta] = oportunidades.get(etiqueta, 0) + 1

    faltas = {}
    for dia in faltados:
        etiqueta = DIAS_SEMANA[dia.weekday()]
        faltas[etiqueta] = faltas.get(etiqueta, 0) + 1

    detalle = {etiqueta: {
        'faltas': faltas.get(etiqueta, 0),
        'oportunidades': total,
        'tasa': round(faltas.get(etiqueta, 0) * 100 / total, 1),
    } for etiqueta, total in oportunidades.items()}

    tasas = {etiqueta: Fraction(faltas.get(etiqueta, 0), total)
             for etiqueta, total in oportunidades.items()
             if total >= MINIMO_OPORTUNIDADES_DIA}

    if not tasas:
        return None, [], 'datos_insuficientes', detalle

    mayor = max(tasas.values())
    if mayor == 0:
        return None, [], 'sin_faltas', detalle

    empatados = sorted((etiqueta for etiqueta, tasa in tasas.items()
                        if tasa == mayor),
                       key=DIAS_SEMANA.index)
    if len(empatados) > 1:
        return None, empatados, 'empate', detalle
    return empatados[0], [], None, detalle


def _resumir(movimientos, esperados, motivos_ventana):
    """Resumen de asistencia de una persona sobre el periodo exigible."""
    conjunto_esperados = set(esperados)

    con_marca = set()
    for movimiento in movimientos:
        con_marca.update(movimiento['dias'])

    asistidos = sorted(d for d in con_marca if d in conjunto_esperados)
    # Asistencias reales que caen fuera del calendario evaluado (tipicamente
    # fin de semana con `solo_habiles`). No entran al porcentaje --sumarlas
    # solo al numerador daba 140% de asistencia-- pero tampoco se ocultan.
    fuera_de_computo = sorted(d for d in con_marca if d not in conjunto_esperados)
    faltados = [d for d in esperados if d not in con_marca]

    dia_peor, empate, motivo, detalle = _dia_mas_faltado(esperados, faltados)

    minutos = [m['permanencia_minutos'] for m in movimientos
               if m['permanencia_minutos'] is not None]

    # Solo es anomalia de la persona la entrada sin salida que ya no puede
    # cerrarse: ni la que sigue abierta hoy, ni la salida cuya entrada quedo
    # fuera de la ventana leida.
    sin_salida = sum(1 for m in movimientos
                     if m['salida'] is None and not m['abierto'])

    return {
        'dias_asistidos': asistidos,
        'total_dias_asistidos': len(asistidos),
        'dias_fuera_de_computo': fuera_de_computo,
        'total_dias_fuera_de_computo': len(fuera_de_computo),
        'dias_faltados': faltados,
        'total_dias_faltados': len(faltados),
        'total_dias_esperados': len(esperados),
        # None, no 0.0: sin dias exigibles no hay porcentaje que mostrar, y
        # un "0%" se lee como inasistencia total.
        'porcentaje_asistencia': (round(len(asistidos) * 100 / len(esperados), 1)
                                  if esperados else None),
        'periodo_evaluado_inicio': esperados[0] if esperados else None,
        'periodo_evaluado_fin': esperados[-1] if esperados else None,
        'motivos_ventana': motivos_ventana,
        'faltas_por_dia_semana': {e: d['faltas'] for e, d in detalle.items()
                                  if d['faltas']},
        'detalle_dias_semana': detalle,
        'dia_mas_faltado': dia_peor,
        'dias_mas_faltados_empatados': empate,
        'motivo_sin_dia_mas_faltado': motivo,
        'total_movimientos': len(movimientos),
        'sin_salida': sin_salida,
        'abiertos': sum(1 for m in movimientos if m['abierto']),
        'entradas_fuera_de_ventana': sum(1 for m in movimientos
                                         if m['entrada_fuera_de_ventana']),
        'promedio_permanencia_minutos': (round(sum(minutos) / len(minutos))
                                         if minutos else None),
    }


def _primer_acceso_por_persona(identificadores):
    """Fecha del primer acceso de cada persona, sin filtrar por el rango.

    Es la mejor aproximacion disponible a la fecha de vinculacion mientras no
    exista esa columna. Es un agregado: no trae los accesos a memoria.
    """
    if not identificadores:
        return {}
    filas = (db.session.query(Acceso.referencia_id, db.func.min(Acceso.fecha))
             .filter(Acceso.referencia_id.in_(identificadores),
                     Acceso.tipo_referencia == 'Usuario')
             .group_by(Acceso.referencia_id).all())
    resultado = {}
    for identificador, minimo in filas:
        momento = parsear_fecha_bd(minimo)
        if momento is not None:
            resultado[identificador] = momento.date()
    return resultado


def _personas_que_caben(personas, inicio, fin):
    """Separa las personas cuyos accesos caben en MAXIMO_ACCESOS.

    Se cuenta con un agregado antes de traer nada. Es preferible dejar fuera
    a las ultimas personas --y decirlo-- que traer a todas con la mitad de
    sus accesos: eso les inventaria faltas.
    """
    identificadores = [p.id for p in personas]
    conteos = dict(db.session.query(Acceso.referencia_id,
                                    db.func.count(Acceso.id))
                   .filter(Acceso.referencia_id.in_(identificadores),
                           Acceso.tipo_referencia == 'Usuario',
                           Acceso.fecha >= inicio,
                           Acceso.fecha <= fin)
                   .group_by(Acceso.referencia_id).all())

    analizadas, omitidas, acumulado = [], [], 0
    for persona in personas:
        cuantos = conteos.get(persona.id, 0)
        if analizadas and acumulado + cuantos > MAXIMO_ACCESOS:
            omitidas.append(persona)
            continue
        acumulado += cuantos
        analizadas.append(persona)
    return analizadas, omitidas


def construir_historial(personas, fecha_inicio, fecha_fin, solo_habiles=True,
                        hoy=None):
    """Historial y resumen de asistencia de varias personas.

    Devuelve {'bloques': [...], 'omitidas': [...], 'truncado': bool}. Hace
    consultas agregadas y DOS lecturas de detalle (accesos + equipos), no una
    por persona: el caso real es una ficha completa de 30 personas o mas.
    """
    if not personas:
        return {'bloques': [], 'omitidas': [], 'truncado': False}

    hoy = hoy or get_colombia_time().date()
    # Se lee un dia mas por cada lado para poder cerrar las parejas que cruzan
    # el borde del rango; el recorte real ocurre despues de emparejar.
    inicio = datetime.combine(fecha_inicio - MARGEN_EMPAREJADO, time.min)
    fin = datetime.combine(fecha_fin + MARGEN_EMPAREJADO, time.max)

    personas, omitidas = _personas_que_caben(personas, inicio, fin)
    identificadores = [p.id for p in personas]

    primer_acceso = _primer_acceso_por_persona(identificadores)

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

    bloques = []
    for persona in personas:
        movimientos = _emparejar(por_persona[persona.id], catalogo_equipos, hoy)
        movimientos = _recortar_al_rango(movimientos, fecha_inicio, fecha_fin)

        exigible_inicio, exigible_fin, motivos = ventana_exigible(
            persona, fecha_inicio, fecha_fin,
            primer_acceso.get(persona.id), hoy)
        if primer_acceso.get(persona.id) is None:
            motivos = motivos + ['sin_referencia_de_vinculacion']

        esperados = (dias_esperados(exigible_inicio, exigible_fin,
                                    solo_habiles, hoy)
                     if exigible_inicio <= exigible_fin else [])

        bloques.append({
            'persona': persona,
            'movimientos': movimientos,
            'movimientos_listados': movimientos[-MAXIMO_MOVIMIENTOS_LISTADOS:],
            'resumen': _resumir(movimientos, esperados, motivos),
        })
    return {'bloques': bloques, 'omitidas': omitidas,
            'truncado': bool(omitidas)}


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------
def _resolver_consulta(argumentos, es_json):
    """Aplica permisos y filtros. Devuelve (historial, filtros, respuesta)."""
    filtros = _leer_filtros(argumentos)
    vacio = {'bloques': [], 'omitidas': [], 'truncado': False}

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
        return vacio, filtros, None

    personas = _buscar_personas(filtros)
    historial = construir_historial(personas, filtros['fecha_inicio'],
                                    filtros['fecha_fin'], filtros['solo_habiles'])
    return historial, filtros, None


@bp.route('/historial-persona')
@login_required
def historial_persona():
    """Pagina de consulta del historial de ingresos."""
    historial, filtros, error = _resolver_consulta(request.args, es_json=False)
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
        datos=historial['bloques'],
        omitidas=historial['omitidas'],
        truncado=historial['truncado'],
        filtros=filtros,
        cargos=cargos,
        puede_consultar_terceros=puede_terceros,
        hubo_busqueda=bool(filtros['usuario_ids'] or filtros['ficha']
                           or filtros['cargo'] or filtros['busqueda']),
        maximo_personas=MAXIMO_PERSONAS,
        maximo_dias_rango=MAXIMO_DIAS_RANGO,
    )


# Serializacion del resumen: se declara que se publica en vez de repetir la
# misma linea por campo. Es una lista blanca a proposito --un campo nuevo no
# se filtra al JSON sin que alguien lo agregue aqui-- y evita que el
# diccionario de respuesta crezca mas que el calculo que lo alimenta.
CAMPOS_RESUMEN = (
    'total_dias_asistidos', 'total_dias_faltados', 'total_dias_esperados',
    'total_dias_fuera_de_computo', 'porcentaje_asistencia', 'motivos_ventana',
    'dia_mas_faltado', 'dias_mas_faltados_empatados',
    'motivo_sin_dia_mas_faltado', 'faltas_por_dia_semana',
    'detalle_dias_semana', 'promedio_permanencia_minutos', 'sin_salida',
    'abiertos',
)
CAMPOS_RESUMEN_LISTA_DE_FECHAS = ('dias_asistidos', 'dias_faltados',
                                  'dias_fuera_de_computo')
CAMPOS_RESUMEN_FECHA = ('periodo_evaluado_inicio', 'periodo_evaluado_fin')

CAMPOS_MOVIMIENTO = ('permanencia_minutos', 'equipos', 'cierre_automatico',
                     'abierto', 'entrada_fuera_de_ventana')


def _resumen_json(resumen):
    salida = {clave: resumen[clave] for clave in CAMPOS_RESUMEN}
    salida.update({clave: [d.isoformat() for d in resumen[clave]]
                   for clave in CAMPOS_RESUMEN_LISTA_DE_FECHAS})
    salida.update({clave: resumen[clave].isoformat() if resumen[clave] else None
                   for clave in CAMPOS_RESUMEN_FECHA})
    return salida


def _movimiento_json(movimiento):
    salida = {clave: movimiento[clave] for clave in CAMPOS_MOVIMIENTO}
    salida['fecha'] = movimiento['fecha'].isoformat()
    salida['dias'] = [d.isoformat() for d in movimiento['dias']]
    for extremo in ('entrada', 'salida'):
        momento = movimiento[extremo]
        salida[extremo] = (momento.strftime('%Y-%m-%d %H:%M:%S')
                           if momento else None)
    return salida


@bp.route('/api/historial-persona')
@login_required
def api_historial_persona():
    """Misma consulta en JSON, para exportar o consumir desde el panel."""
    historial, filtros, error = _resolver_consulta(request.args, es_json=True)
    if error is not None:
        return error

    return jsonify({
        'estado': 'ok',
        'fecha_inicio': filtros['fecha_inicio'].isoformat(),
        'fecha_fin': filtros['fecha_fin'].isoformat(),
        'rango_recortado': filtros['rango_recortado'],
        'maximo_dias_rango': MAXIMO_DIAS_RANGO,
        'truncado': historial['truncado'],
        'personas_omitidas': [{'id': p.id, 'nombre': p.nombre}
                              for p in historial['omitidas']],
        'personas': [{
            'id': bloque['persona'].id,
            'nombre': bloque['persona'].nombre,
            'documento': bloque['persona'].documento,
            'cargo': bloque['persona'].cargo,
            'ficha': bloque['persona'].ficha,
            'programa': bloque['persona'].programa,
            'resumen': _resumen_json(bloque['resumen']),
            'movimientos': [_movimiento_json(m)
                            for m in bloque['movimientos_listados']],
        } for bloque in historial['bloques']],
    })
