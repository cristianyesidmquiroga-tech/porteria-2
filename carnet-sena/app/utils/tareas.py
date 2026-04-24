from .. import db
from ..models.usuarios import TurnoCelador, Usuario
from ..models.entidades import Visitante, Vehiculo, Equipo
from ..models.accesos import Acceso, Auditoria
from . import get_colombia_time
from datetime import datetime

def auto_exit_all():
    """
    Cierra automáticamente todos los turnos, accesos y estados de entidades 
    que quedaron abiertos al final del día.
    """
    # Necesitamos el contexto de la aplicación para interactuar con la DB si se llama desde el scheduler
    from flask import current_app
    with current_app.app_context():
        ahora = get_colombia_time()
        print(f"[{ahora}] Iniciando proceso de salida automática de medianoche...")
        
        # 1. Cerrar Turnos de Celadores
        turnos_activos = TurnoCelador.query.filter_by(estado='Activo').all()
        for turno in turnos_activos:
            turno.estado = 'Finalizado'
            turno.fecha_salida = ahora
            # Registrar en historial general de accesos
            db.session.add(Acceso(punto_id=1, referencia_id=turno.celador_id, tipo_referencia='Usuario', tipo='Salida', fecha=ahora))
            print(f" - Turno finalizado y salida registrada para celador ID: {turno.celador_id}")

        # 2. Desactivar Visitantes
        visitantes_dentro = Visitante.query.filter_by(activo=True).all()
        for v in visitantes_dentro:
            v.activo = False
            # Registrar salida en Accesos
            db.session.add(Acceso(punto_id=1, referencia_id=v.id, tipo_referencia='Visitante', tipo='Salida', fecha=ahora))
            print(f" - Salida automática registrada para visitante: {v.nombre}")

        # 3. Desactivar Vehículos
        vehiculos_dentro = Vehiculo.query.filter_by(activo=True).all()
        for veh in vehiculos_dentro:
            veh.activo = False
            db.session.add(Acceso(punto_id=1, referencia_id=veh.id, tipo_referencia='Vehiculo', tipo='Salida', fecha=ahora))
            print(f" - Salida automática registrada para vehículo: {veh.placa}")

        # 4. Actualizar Equipos
        equipos_adentro = Equipo.query.filter_by(estado='Adentro').all()
        for eq in equipos_adentro:
            eq.estado = 'Afuera'
            print(f" - Equipo {eq.nombre} marcado como fuera del campus.")

        # 5. Usuarios Genéricos (Aprendices, Instructores, etc. que no son Celadores en turno)
        # Obtenemos el último acceso de cada usuario en el sistema para ver quién quedó "Adentro"
        subquery = db.session.query(
            Acceso.referencia_id, 
            db.func.max(Acceso.fecha).label('max_fecha')
        ).filter(
            Acceso.tipo_referencia == 'Usuario'
        ).group_by(Acceso.referencia_id).subquery()

        usuarios_dentro = db.session.query(Acceso).join(
            subquery, 
            (Acceso.referencia_id == subquery.c.referencia_id) & (Acceso.fecha == subquery.c.max_fecha)
        ).filter(Acceso.tipo == 'Entrada').all()

        # Para que el reporte de ayer quede cerrado correctamente, usamos las 23:59:59 de ayer
        ayer_final = (ahora - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0) if ahora.hour < 1 else ahora

        for acceso in usuarios_dentro:
            # Crear registro de salida automática
            db.session.add(Acceso(
                punto_id=1, 
                referencia_id=acceso.referencia_id, 
                tipo_referencia='Usuario', 
                tipo='Salida', 
                fecha=ayer_final
            ))
            print(f" - Salida automática de Usuario ID: {acceso.referencia_id} registrada a las {ayer_final}")

        # 6. Registrar en Auditoría
        db.session.add(Auditoria(
            usuario_id=1, # Admin o Sistema
            nombre_usuario="SISTEMA",
            tabla_afectada="VARIAS (Limpieza Nocturna)",
            registro_id=0,
            accion="Cierre automático de todos los ingresos a medianoche.",
            fecha=ahora
        ))

        db.session.commit()
        print(f"[{ahora}] Proceso de limpieza completado con éxito.")
