"""Mensajes entre un administrador y una persona del sistema.

Cuando a alguien le rechazan la foto o le falta un dato, el correo automático
no siempre alcanza: la persona no sabe qué corregir, o tiene un caso particular
(cambió de documento, no tiene cómo tomarse la foto, su ficha está mal). Sin un
canal dentro del sistema, esa persona se queda bloqueada sin carnet y sin poder
entrar, y termina buscando a alguien en portería.

El modelo es deliberadamente simple: un hilo por persona. Todos los
administradores ven y responden el mismo hilo, porque quien atiende hoy puede no
ser quien atienda mañana.
"""
from .. import db
from ..utils import get_colombia_time


class Mensaje(db.Model):
    __tablename__ = 'mensajes'

    id = db.Column(db.Integer, primary_key=True)

    # Dueño del hilo: la persona sobre la que trata la conversación. Todos los
    # mensajes con el mismo `usuario_id` forman una sola conversación.
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'),
                           nullable=False, index=True)

    # Quién escribió este mensaje en concreto (puede ser la misma persona o
    # cualquier administrador).
    # Nullable a proposito: el mensaje puede sobrevivir a la cuenta de quien
    # lo escribio (el nombre queda en autor_nombre); al borrar al autor esta
    # referencia pasa a NULL en lugar de impedir el borrado.
    autor_id = db.Column(db.Integer,
                         db.ForeignKey('usuarios.id', ondelete='SET NULL'),
                         nullable=True)

    # Se guarda en el mensaje para que el historial siga siendo legible aunque
    # la cuenta del autor se elimine después.
    autor_nombre = db.Column(db.String(100), nullable=False)
    autor_es_admin = db.Column(db.Boolean, default=False, nullable=False)

    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=get_colombia_time, index=True)

    # `leido` marca si lo vio la otra parte, para poder mostrar un contador.
    leido = db.Column(db.Boolean, default=False, nullable=False)

    # Marca los mensajes que genera el propio sistema (por ejemplo, al rechazar
    # una foto), para distinguirlos de lo que escribe una persona.
    automatico = db.Column(db.Boolean, default=False, nullable=False)

    # El hilo es personal, no institucional: si la persona se borra, sus
    # mensajes se van con ella (cascade). Antes esto reventaba el borrado de
    # cualquiera con una foto rechazada, porque el rechazo genera un mensaje.
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id],
                              backref=db.backref('mensajes', lazy='dynamic',
                                                 cascade='all, delete-orphan'))
    # El backref existe para que el ORM anule autor_id al borrar al autor.
    autor = db.relationship('Usuario', foreign_keys=[autor_id],
                            backref=db.backref('mensajes_escritos', lazy=True))


def registrar_mensaje(usuario_id, autor, texto, automatico=False):
    """Añade un mensaje al hilo de una persona.

    `autor` es el objeto Usuario que escribe. No hace commit: lo decide quien
    llama, para poder agrupar el mensaje con el resto de la operación en una
    sola transacción.
    """
    mensaje = Mensaje(
        usuario_id=usuario_id,
        autor_id=autor.id,
        autor_nombre=autor.nombre,
        autor_es_admin=bool(autor.puede_asesorar),
        texto=texto,
        automatico=automatico,
    )
    db.session.add(mensaje)
    return mensaje


def sin_leer_para_usuario(usuario):
    """Mensajes que la persona todavía no ha visto (escritos por un admin)."""
    return Mensaje.query.filter(
        Mensaje.usuario_id == usuario.id,
        Mensaje.autor_id != usuario.id,
        Mensaje.leido.is_(False)).count()


def hilos_con_respuesta_pendiente():
    """Cuántas personas escribieron algo que ningún administrador ha leído."""
    return db.session.query(Mensaje.usuario_id).filter(
        Mensaje.autor_id == Mensaje.usuario_id,
        Mensaje.leido.is_(False)).distinct().count()
