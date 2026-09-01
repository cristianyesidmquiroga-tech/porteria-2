from app.utils import get_colombia_time
from .. import db



class MovimientoVisitante(db.Model):
    __tablename__ = 'movimientos_visitantes'
    id = db.Column(db.Integer, primary_key=True)
    # index=True: PostgreSQL no indexa las claves ajenas por si solo, y estas
    # se consultan al listar y borrar los movimientos de una entidad.
    visitante_id = db.Column(
        db.Integer,
        db.ForeignKey('visitantes.id'),
        nullable=False,
        index=True)
    punto_id = db.Column(
        db.Integer,
        db.ForeignKey('puntos_acceso.id'),
        nullable=False)
    fecha = db.Column(db.DateTime, default=get_colombia_time)
    tipo = db.Column(db.String(50), nullable=False)


class MovimientoVehiculo(db.Model):
    __tablename__ = 'movimientos_vehiculos'
    id = db.Column(db.Integer, primary_key=True)
    # index=True: PostgreSQL no indexa las claves ajenas por si solo, y estas
    # se consultan al listar y borrar los movimientos de una entidad.
    vehiculo_id = db.Column(
        db.Integer,
        db.ForeignKey('vehiculos.id'),
        nullable=False,
        index=True)
    punto_id = db.Column(
        db.Integer,
        db.ForeignKey('puntos_acceso.id'),
        nullable=False)
    fecha = db.Column(db.DateTime, default=get_colombia_time)
    tipo = db.Column(db.String(50), nullable=False)


class MovimientoEquipo(db.Model):
    __tablename__ = 'movimientos_equipos'
    id = db.Column(db.Integer, primary_key=True)
    # index=True: PostgreSQL no indexa las claves ajenas por si solo, y estas
    # se consultan al listar y borrar los movimientos de una entidad.
    equipo_id = db.Column(
        db.Integer,
        db.ForeignKey('equipos.id'),
        nullable=False,
        index=True)
    punto_id = db.Column(
        db.Integer,
        db.ForeignKey('puntos_acceso.id'),
        nullable=False)
    fecha = db.Column(db.DateTime, default=get_colombia_time)
    tipo = db.Column(db.String(50), nullable=False)


class MovimientoObjeto(db.Model):
    __tablename__ = 'movimientos_objetos'
    id = db.Column(db.Integer, primary_key=True)
    # index=True: PostgreSQL no indexa las claves ajenas por si solo, y estas
    # se consultan al listar y borrar los movimientos de una entidad.
    objeto_id = db.Column(
        db.Integer,
        db.ForeignKey('objetos_externos.id'),
        nullable=False,
        index=True)
    punto_id = db.Column(
        db.Integer,
        db.ForeignKey('puntos_acceso.id'),
        nullable=False)
    fecha = db.Column(db.DateTime, default=get_colombia_time)
    tipo = db.Column(db.String(50), nullable=False)

