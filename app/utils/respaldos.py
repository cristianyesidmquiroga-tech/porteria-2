import os
import logging
from datetime import datetime, timedelta, timezone
from openpyxl import Workbook
from flask import current_app
from .. import db
from ..models.accesos import Acceso
from ..models.usuarios import Usuario, Rol
from ..models.asistencia import AsistenciaClase
from . import get_colombia_time

logger = logging.getLogger(__name__)

def ejecutar_respaldo_mensual():
    """Exporta los datos del mes anterior a Excel y los elimina de la BD."""
    try:
        # Fechas naive en hora de Colombia, igual que las columnas de la base.
        # Comparar aware contra naive desfasaba la ventana de borrado 5 horas
        # (PostgreSQL) o lanzaba TypeError que el except se tragaba (SQLite).
        now_col = get_colombia_time()
        
        # Calcular el inicio y fin del mes anterior
        primer_dia_mes_actual = now_col.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
        primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        fecha_inicio = primer_dia_mes_anterior
        fecha_fin = primer_dia_mes_actual
        
        # Nombre del archivo indicará de qué mes es el respaldo (ej: Respaldo_2026-03)
        nombre_mes_anterior = ultimo_dia_mes_anterior.strftime('%Y-%m')
        
        # Crear directorio si no existe
        respaldos_dir = os.path.join(current_app.root_path, 'respaldos_mensuales')
        if not os.path.exists(respaldos_dir):
            os.makedirs(respaldos_dir)
            
        nombre_archivo = f"Respaldo_Sistema_{nombre_mes_anterior}.xlsx"
        ruta_archivo = os.path.join(respaldos_dir, nombre_archivo)
        
        # Crear el libro de Excel (Workbook)
        wb = Workbook()
        
        # --- HOJA 1: ACCESOS ---
        ws_accesos = wb.active
        ws_accesos.title = "Historial Accesos"
        ws_accesos.append(['ID', 'Documento', 'Nombre', 'Cargo', 'Ficha', 'Tipo', 'Equipos', 'Fecha'])
        
        accesos_antiguos = db.session.query(Acceso, Usuario, Rol).join(
            Usuario, Acceso.referencia_id == Usuario.id
        ).join(
            Rol, Usuario.rol_id == Rol.id
        ).filter(
            # SIN este filtro, referencia_id (que es polimorfico) unia el acceso
            # del visitante 7 con el usuario 7: el respaldo guardaba el nombre y
            # la cedula de la persona equivocada y luego borraba el registro.
            Acceso.tipo_referencia == 'Usuario',
            Acceso.fecha >= fecha_inicio,
            Acceso.fecha < fecha_fin
        ).all()
        
        ids_accesos_borrar = []
        for acceso, usuario, rol in accesos_antiguos:
            fecha_str = acceso.fecha.strftime('%Y-%m-%d %H:%M:%S') if isinstance(acceso.fecha, datetime) else str(acceso.fecha)
            cargo_txt = usuario.cargo if usuario.cargo else rol.nombre
            ws_accesos.append([
                acceso.id,
                usuario.documento,
                usuario.nombre,
                cargo_txt,
                usuario.ficha or 'N/A',
                acceso.tipo,
                acceso.equipos_str or 'Ninguno',
                fecha_str
            ])
            ids_accesos_borrar.append(acceso.id)
            
        # --- HOJA 2: ACCESOS DE VISITANTES, VEHICULOS Y OBJETOS ---
        # Antes quedaban fuera del respaldo y nunca se purgaban, acumulando
        # datos de terceros indefinidamente (art. 4 lit. d, Ley 1581).
        ws_otros = wb.create_sheet(title="Accesos No Usuarios")
        ws_otros.append(['ID', 'Tipo de entidad', 'Referencia', 'Tipo', 'Fecha'])

        accesos_otros = Acceso.query.filter(
            Acceso.tipo_referencia != 'Usuario',
            Acceso.fecha >= fecha_inicio,
            Acceso.fecha < fecha_fin
        ).all()
        for acc in accesos_otros:
            fecha_txt = (acc.fecha.strftime('%Y-%m-%d %H:%M:%S')
                         if isinstance(acc.fecha, datetime) else str(acc.fecha))
            ws_otros.append([acc.id, acc.tipo_referencia, acc.referencia_id,
                             acc.tipo, fecha_txt])
            ids_accesos_borrar.append(acc.id)

        # --- HOJA 3: ASISTENCIAS ---
        ws_asistencias = wb.create_sheet(title="Asistencias Clases")
        ws_asistencias.append(['ID', 'Ficha', 'Instructor', 'Aprendiz Documento', 'Aprendiz Nombre', 'Presente', 'Fecha'])
        
        asistencias_antiguas = AsistenciaClase.query.filter(
            AsistenciaClase.fecha >= fecha_inicio,
            AsistenciaClase.fecha < fecha_fin
        ).all()
        ids_asistencias_borrar = []
        for asis in asistencias_antiguas:
            fecha_str = asis.fecha.strftime('%Y-%m-%d %H:%M:%S') if isinstance(asis.fecha, datetime) else str(asis.fecha)
            instructor = Usuario.query.get(asis.instructor_id)
            aprendiz = Usuario.query.get(asis.aprendiz_id)
            
            ws_asistencias.append([
                asis.id,
                asis.ficha,
                instructor.nombre if instructor else 'Desconocido',
                aprendiz.documento if aprendiz else 'N/A',
                aprendiz.nombre if aprendiz else 'Desconocido',
                "SI" if asis.presente else "NO",
                fecha_str
            ])
            ids_asistencias_borrar.append(asis.id)
            
        # Solo guardar el archivo en el servidor si realmente se encontraron datos
        if ids_accesos_borrar or ids_asistencias_borrar:
            wb.save(ruta_archivo)
            
            # Borrar datos respaldados
            if ids_accesos_borrar:
                Acceso.query.filter(Acceso.id.in_(ids_accesos_borrar)).delete(synchronize_session=False)
            if ids_asistencias_borrar:
                AsistenciaClase.query.filter(AsistenciaClase.id.in_(ids_asistencias_borrar)).delete(synchronize_session=False)
            
            db.session.commit()
            logger.info("Respaldo generado: %s", nombre_archivo)
        else:
            logger.info("No hay datos antiguos para respaldar este mes.")
            
    except Exception as e:
        db.session.rollback()
        logger.exception("Error generando el respaldo mensual")
