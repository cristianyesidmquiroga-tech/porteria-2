from app.utils import get_colombia_time
from .. import db



class PuntoAcceso(db.Model):
    __tablename__ = 'puntos_acceso'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Por ejemplo: 'Entrada Principal', 'Salida Peatonal'
    tipo = db.Column(db.String(50), nullable=False)
    accesos = db.relationship('Acceso', backref='punto', lazy=True)


class Acceso(db.Model):
    __tablename__ = 'accesos'
    # La consulta mas caliente del sistema (cada escaneo de carnet) filtra por
    # (referencia_id, tipo_referencia) y ordena por fecha descendente: el
    # indice compuesto la resuelve sin recorrer la tabla. El indice suelto
    # sobre fecha lo usan el cierre nocturno, el historial y la purga mensual.
    __table_args__ = (
        db.Index('ix_accesos_referencia_tipo_fecha',
                 'referencia_id', 'tipo_referencia', 'fecha'),
        db.Index('ix_accesos_fecha', 'fecha'),
    )
    id = db.Column(db.Integer, primary_key=True)
    punto_id = db.Column(
        db.Integer,
        db.ForeignKey('puntos_acceso.id'),
        nullable=False,
        index=True)
    carnet_id = db.Column(
        db.Integer,
        db.ForeignKey('carnets.id'),
        nullable=True,  # Opcional para visitantes o pases manuales
        index=True)
    # ID de la entidad específica (Usuario, Visitante, etc.)
    referencia_id = db.Column(db.Integer, nullable=False)
    # Define si es 'Usuario', 'Visitante', etc.
    tipo_referencia = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'Entrada' o 'Salida'
    fecha = db.Column(db.DateTime, default=get_colombia_time)
    equipos_str = db.Column(db.String(255), nullable=True)
    # Sin este campo no habia forma de saber que celador registro un ingreso:
    # el historial de accesos no era atribuible a nadie.
    operador_id = db.Column(db.Integer,
                            db.ForeignKey('usuarios.id', ondelete='SET NULL'),
                            nullable=True, index=True)

    # El acceso tiene valor institucional y sobrevive al celador que lo
    # registro: al borrar al operador, la referencia queda en NULL en lugar
    # de reventar el borrado.
    operador = db.relationship(
        'Usuario',
        foreign_keys=[operador_id],
        backref=db.backref('accesos_operados', lazy=True))


class Auditoria(db.Model):
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True)
    # Nullable a proposito: la auditoria sobrevive a quien la genero (el
    # nombre queda en nombre_usuario); si la cuenta se borra, esto queda NULL.
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id', ondelete='SET NULL'),
        nullable=True,
        index=True)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    tabla_afectada = db.Column(db.String(100), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    accion = db.Column(db.String(255), nullable=False)
    # Nuevos campos solicitados
    autorizado_por = db.Column(db.String(100), nullable=True)
    motivo = db.Column(db.Text, nullable=True)
    detalles = db.Column(db.Text, nullable=True) # Para guardar qué cambió exactamente
    fecha = db.Column(db.DateTime, default=get_colombia_time, index=True)

    # Declarada para que el ORM sepa poner usuario_id en NULL al borrar la
    # cuenta, en vez de fallar por la clave ajena.
    usuario = db.relationship(
        'Usuario',
        foreign_keys=[usuario_id],
        backref=db.backref('auditorias_generadas', lazy=True))

