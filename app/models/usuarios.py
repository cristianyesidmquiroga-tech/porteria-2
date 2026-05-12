from app.utils import get_colombia_time
from .. import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Rol(db.Model):
    __tablename__ = 'roles'
    # Tabla que define los roles del sistema (ej: Admin, Usuario)
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    usuarios = db.relationship('Usuario', backref='rol', lazy=True)


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    cargo = db.Column(db.String(50), nullable=True) # Cargo específico: Celador, Instructor, Aprendiz, etc.
    perfil_completo = db.Column(db.Boolean, default=False)
    correo_verificado = db.Column(db.Boolean, default=False)
    codigo_verificacion = db.Column(db.String(6), nullable=True)
    codigo_expiracion = db.Column(db.DateTime, nullable=True)
    intentos_fallidos = db.Column(db.Integer, default=0)
    bloqueado_hasta = db.Column(db.DateTime, nullable=True)
    debe_cambiar_contrasena = db.Column(db.Boolean, default=False)
    
    # Sistema de Recuperación
    codigo_recuperacion = db.Column(db.String(6), nullable=True)
    recuperacion_expiracion = db.Column(db.DateTime, nullable=True)

    # Campos detallados del perfil del usuario (SENA)
    documento = db.Column(db.String(20), unique=True, nullable=True)
    programa = db.Column(db.String(100), nullable=True)
    ficha = db.Column(db.String(20), nullable=True)
    horario = db.Column(db.String(20), nullable=True)
    tipo_sangre = db.Column(db.String(5), nullable=True)
    foto = db.Column(
        db.String(255),
        nullable=True,
        default='default_profile.png')

    session_token = db.Column(db.String(100), nullable=True)

    carnet = db.relationship(
        'Carnet',
        backref='usuario',
        uselist=False,
        lazy=True)
    equipos = db.relationship('Equipo', backref='usuario', lazy=True)

    # --- SISTEMA DE PERMISOS CENTRALIZADO (RBAC) ---
    @property
    def es_admin(self):
        return self.rol and self.rol.nombre == 'Admin'

    @property
    def es_aprendiz_cargo(self):
        return self.cargo == 'Aprendiz'

    @property
    def es_instructor_cargo(self):
        return self.cargo == 'Instructor'

    @property
    def es_celador_cargo(self):
        return self.cargo in ['Celador', 'Portería']

    @property
    def puede_operar_porteria(self):
        if self.es_admin: return True
        return self.rol and self.rol.nombre == 'Usuario' and (self.es_celador_cargo or self.cargo == 'Administrador')
    
    @property
    def puede_gestionar_asistencia(self):
        return self.es_admin or self.es_instructor_cargo

    @property
    def puede_registrar_equipos(self):
        if self.es_admin: return True
        return self.rol and self.rol.nombre == 'Usuario' and not self.es_celador_cargo

    def set_password(self, password):
        self.contraseña = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contraseña, password)


class Carnet(db.Model):
    __tablename__ = 'carnets'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False)
    qr_codes = db.relationship('CodigoQR', backref='carnet', lazy=True)


class CodigoQR(db.Model):
    __tablename__ = 'codigos_qr'
    id = db.Column(db.Integer, primary_key=True)
    carnet_id = db.Column(
        db.Integer,
        db.ForeignKey('carnets.id'),
        nullable=False)
    codigo = db.Column(db.String(255), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, default=get_colombia_time)


class TurnoCelador(db.Model):
    __tablename__ = 'turnos_celador'
    id = db.Column(db.Integer, primary_key=True)
    celador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_ingreso = db.Column(db.DateTime, default=get_colombia_time)
    fecha_salida = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(20), default='Activo')  # 'Activo' o 'Finalizado'
    
    celador = db.relationship('Usuario', backref='turnos', lazy=True)
