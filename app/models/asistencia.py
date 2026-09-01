from app.utils import get_colombia_time
from .. import db

class AsistenciaClase(db.Model):
    __tablename__ = 'asistencia_clases'
    id = db.Column(db.Integer, primary_key=True)
    # Nullable a proposito: la asistencia documenta al aprendiz, no al
    # instructor. Si la cuenta del instructor se borra, el registro sobrevive
    # con instructor_id en NULL en vez de bloquear el borrado.
    # index=True en ambas claves: PostgreSQL no indexa claves ajenas solo.
    instructor_id = db.Column(db.Integer,
                              db.ForeignKey('usuarios.id', ondelete='SET NULL'),
                              nullable=True, index=True)
    aprendiz_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'),
                            nullable=False, index=True)
    ficha = db.Column(db.String(20), nullable=False)
    fecha = db.Column(db.DateTime, default=get_colombia_time)
    presente = db.Column(db.Boolean, default=False)
    evaluacion = db.Column(db.String(255), nullable=True) # Optional note or reason

    # La asistencia es un dato del aprendiz: al borrar su cuenta se borra con
    # el (antes el borrado reventaba con error 500 por la clave ajena).
    aprendiz = db.relationship(
        'Usuario', foreign_keys=[aprendiz_id],
        backref=db.backref('asistencias', lazy=True,
                           cascade='all, delete-orphan'))
    instructor = db.relationship(
        'Usuario', foreign_keys=[instructor_id],
        backref=db.backref('clases_dictadas', lazy=True))
