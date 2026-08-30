from .. import db
from ..models.usuarios import TurnoCelador, Usuario
from ..models.entidades import Visitante, Vehiculo, Equipo
from ..models.accesos import Acceso, Auditoria
from . import get_colombia_time
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def auto_exit_all():
    """Cierra turnos, accesos y estados de entidades que quedaron abiertos.

    Se ejecuta a las 00:00:05. Todo el trabajo va en una sola transaccion: si
    algo falla se revierte completo, para no dejar la mitad de las salidas
    registradas y la otra mitad no.
    """
    from flask import current_app

    with current_app.app_context():
        ahora = get_colombia_time()
        logger.info("Iniciando cierre automatico de medianoche (%s)", ahora)

        # El job corre pasada la medianoche, asi que las salidas pendientes
        # pertenecen al dia anterior y se fechan a las 23:59:59 de ese dia.
        if ahora.hour < 1:
            cierre = (ahora - timedelta(days=1)).replace(
                hour=23, minute=59, second=59, microsecond=0)
        else:
            cierre = ahora

        try:
            turnos_cerrados = 0
            for turno in TurnoCelador.query.filter_by(estado='Activo').all():
                turno.estado = 'Finalizado'
                turno.fecha_salida = cierre
                turnos_cerrados += 1

            visitantes_cerrados = 0
            for visitante in Visitante.query.filter_by(activo=True).all():
                visitante.activo = False
                visitantes_cerrados += 1

            vehiculos_cerrados = 0
            for vehiculo in Vehiculo.query.filter_by(activo=True).all():
                vehiculo.activo = False
                vehiculos_cerrados += 1

            equipos_cerrados = Equipo.query.filter_by(estado='Adentro').update(
                {Equipo.estado: 'Afuera'}, synchronize_session=False)

            # Toda entidad cuyo ultimo movimiento fue 'Entrada' sigue figurando
            # adentro y necesita una salida automatica.
            ultimo_movimiento = db.session.query(
                Acceso.referencia_id,
                Acceso.tipo_referencia,
                db.func.max(Acceso.fecha).label('max_fecha'),
            ).group_by(Acceso.referencia_id, Acceso.tipo_referencia).subquery()

            adentro = db.session.query(Acceso).join(
                ultimo_movimiento,
                (Acceso.referencia_id == ultimo_movimiento.c.referencia_id)
                & (Acceso.tipo_referencia == ultimo_movimiento.c.tipo_referencia)
                & (Acceso.fecha == ultimo_movimiento.c.max_fecha),
            ).filter(Acceso.tipo == 'Entrada').all()

            for acceso in adentro:
                db.session.add(Acceso(
                    punto_id=acceso.punto_id or 1,
                    referencia_id=acceso.referencia_id,
                    tipo_referencia=acceso.tipo_referencia,
                    tipo='Salida',
                    fecha=cierre,
                ))

            # La auditoria referencia un usuario real; usar un id fijo revienta
            # la clave foranea si esa cuenta fue eliminada.
            admin = Usuario.query.join(Usuario.rol).filter_by(nombre='Admin').first()
            if admin:
                db.session.add(Auditoria(
                    usuario_id=admin.id,
                    nombre_usuario="SISTEMA",
                    tabla_afectada="VARIAS (cierre nocturno)",
                    registro_id=0,
                    accion="Cierre automatico de ingresos a medianoche",
                    detalles=(f"Turnos: {turnos_cerrados}, visitantes: {visitantes_cerrados}, "
                              f"vehiculos: {vehiculos_cerrados}, equipos: {equipos_cerrados}, "
                              f"salidas registradas: {len(adentro)}"),
                    fecha=cierre,
                ))

            db.session.commit()
            logger.info(
                "Cierre nocturno completado: %s turnos, %s visitantes, %s vehiculos, "
                "%s equipos, %s salidas registradas",
                turnos_cerrados, visitantes_cerrados, vehiculos_cerrados,
                equipos_cerrados, len(adentro),
            )
        except Exception:
            db.session.rollback()
            logger.exception("Fallo el cierre automatico de medianoche")
            raise
