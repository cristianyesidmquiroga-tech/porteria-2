from app.utils import get_colombia_time
from .. import db

class AsistenciaClase(db.Model):
    __tablename__ = 'asistencia_clases'
    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    aprendiz_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    ficha = db.Column(db.String(20), nullable=False)
    fecha = db.Column(db.DateTime, default=get_colombia_time)
    presente = db.Column(db.Boolean, default=False)
    evaluacion = db.Column(db.String(255), nullable=True) # Optional note or reason
    
    aprendiz = db.relationship('Usuario', foreign_keys=[aprendiz_id], backref=db.backref('asistencias', lazy=True))
    instructor = db.relationship('Usuario', foreign_keys=[instructor_id], backref=db.backref('clases_dictadas', lazy=True))

