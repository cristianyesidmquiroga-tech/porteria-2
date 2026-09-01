import os

from app.utils import get_colombia_time
from .. import db

# Avatares vectoriales por cargo. No son fotografias de nadie: pesan menos de
# 1 KB, viven en el repositorio sin problema y sustituyen al servicio externo
# ui-avatars.com, al que antes se le enviaba el nombre real de cada usuario en
# la URL en cada carga de pagina.
AVATARES_POR_CARGO = {
    'aprendiz': 'img/perfiles/aprendiz.svg',
    'instructor': 'img/perfiles/instructor.svg',
    'celador': 'img/perfiles/celador.svg',
    'porteria': 'img/perfiles/celador.svg',
    'portería': 'img/perfiles/celador.svg',
    'administrador': 'img/perfiles/administrador.svg',
    'administrativo': 'img/perfiles/administrativo.svg',
    'visitante': 'img/perfiles/visitante.svg',
    'vehiculo': 'img/perfiles/vehiculo.svg',
    'objetoexterno': 'img/perfiles/objeto.svg',
}
AVATAR_GENERICO = 'img/perfiles/generico.svg'

# Estados por los que pasa la foto de perfil.
# Cargos que el sistema reconoce. Es lista blanca: cualquier otro valor que
# llegue (por ejemplo desde una importacion de Excel) se descarta, porque el
# cargo gobierna permisos.
CARGOS_VALIDOS = ('Aprendiz', 'Instructor', 'Administrativo', 'Celador',
                  'Administrador')

# Roles que se pueden asignar en una importacion masiva. 'Admin' queda fuera a
# proposito: da acceso total y solo debe concederse desde el panel, uno a uno.
ROLES_IMPORTABLES = ('usuario', 'trabajador')

# Cargos que atienden el centro de ayuda y la cola de fotos, ademas del rol
# Admin. Es el unico sitio donde se define quien asesora.
CARGOS_ASESORES = ('Administrador', 'Administrativo')

ESTADO_SIN_FOTO = 'sin_foto'
ESTADO_PENDIENTE = 'pendiente'
ESTADO_APROBADA = 'aprobada'
ESTADO_RECHAZADA = 'rechazada'

ETIQUETAS_ESTADO_FOTO = {
    ESTADO_SIN_FOTO: 'Sin foto',
    ESTADO_PENDIENTE: 'Pendiente de revision',
    ESTADO_APROBADA: 'Aprobada',
    ESTADO_RECHAZADA: 'Rechazada',
}


def avatar_de_cargo(cargo):
    """Ruta estatica del avatar que corresponde a un cargo."""
    if not cargo:
        return AVATAR_GENERICO
    return AVATARES_POR_CARGO.get(str(cargo).strip().lower(), AVATAR_GENERICO)


def ruta_foto_o_avatar(nombre_foto, cargo, carpeta_uploads=None):
    """Ruta estatica de la foto de un usuario, o su avatar si no la tiene.

    Comprueba que el archivo exista de verdad: la columna `foto` puede apuntar
    a una imagen que ya se borro del disco, y en ese caso hay que caer al
    avatar en lugar de servir un enlace roto.
    """
    if nombre_foto:
        if carpeta_uploads is None:
            return f'uploads/profiles/{nombre_foto}'
        if os.path.isfile(os.path.join(carpeta_uploads, nombre_foto)):
            return f'uploads/profiles/{nombre_foto}'
    return avatar_de_cargo(cargo)
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
    # El carnet oficial imprime nombres y apellidos en dos lineas separadas,
    # pero `nombre` viene de una sola casilla y lleva anos de datos dentro.
    # Partirlo automaticamente obligaria a adivinar donde acaba el nombre en
    # apellidos compuestos ("De La Cruz", "Van Der Berg") y dejaria el dato
    # corrupto para siempre. Asi que `nombre` se queda intacto como fuente de
    # verdad y estas dos columnas se rellenan solo cuando la persona las
    # declara. Si estan vacias, el carnet parte `nombre` unicamente para
    # pintarlo (ver app/utils/carnet.partir_nombre): equivocarse ahi cuesta
    # un salto de linea feo, no un dato perdido.
    nombres = db.Column(db.String(100), nullable=True)
    apellidos = db.Column(db.String(100), nullable=True)
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
    # Contador propio para los codigos enviados por correo. Debe ser distinto
    # de intentos_fallidos: si compartieran contador, pedir un codigo de
    # recuperacion (endpoint publico) reiniciaria el bloqueo del login y la
    # fuerza bruta de contrasenas quedaria sin limite.
    intentos_codigo = db.Column(db.Integer, default=0)

    # Campos detallados del perfil del usuario (SENA)
    # El tipo condiciona cuantos digitos debe tener el numero: una tarjeta de
    # identidad y una cedula de extranjeria no se validan igual.
    tipo_documento = db.Column(db.String(5), default='CC')
    documento = db.Column(db.String(20), unique=True, nullable=True)
    programa = db.Column(db.String(100), nullable=True)
    ficha = db.Column(db.String(20), nullable=True)
    # El aprendiz elige su ficha y hereda de ella programa y fecha de
    # finalizacion. Las columnas de texto `programa` y `ficha` se conservan:
    # guardan lo que ya escribieron los usuarios existentes y las siguen
    # usando instructores (a quienes `programa` les sirve de area) y los
    # reportes. Cuando hay ficha enlazada, ella manda.
    ficha_id = db.Column(db.Integer, db.ForeignKey('fichas.id'), nullable=True)
    horario = db.Column(db.String(20), nullable=True)
    tipo_sangre = db.Column(db.String(5), nullable=True)
    foto = db.Column(
        db.String(255),
        nullable=True,
        default=None)

    session_token = db.Column(db.String(100), nullable=True)

    # El recorrido guiado de bienvenida se muestra una sola vez: en cuanto la
    # persona lo termina (o lo salta a proposito) queda marcado aqui y no
    # vuelve a interrumpirla en cada inicio de sesion.
    tutorial_visto = db.Column(db.Boolean, default=False)

    # --- Revision de la foto de perfil ---
    # El sistema comprueba automaticamente que la foto sea utilizable (un solo
    # rostro, nitida, con luz), pero NO puede comprobar que la persona de la
    # foto sea quien dice ser. Eso lo aprueba un administrador antes de que el
    # carnet digital quede activo.
    foto_estado = db.Column(db.String(20), default=ESTADO_SIN_FOTO)
    foto_motivo = db.Column(db.Text, nullable=True)          # por que se rechazo
    foto_revisada_por = db.Column(db.Integer, nullable=True)  # id del admin
    foto_fecha_revision = db.Column(db.DateTime, nullable=True)
    foto_fecha_subida = db.Column(db.DateTime, nullable=True)

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
    def puede_asesorar(self):
        """Puede responder el centro de ayuda y revisar perfiles ajenos.

        No se limita al rol Admin a proposito: en el centro hay personal
        administrativo que atiende a los aprendices a diario y es quien de
        verdad resuelve estos casos. Restringirlo solo al administrador
        convertiria una sola persona en cuello de botella, y quien se queda
        sin carnet no puede entrar hasta que le respondan.

        Para cambiar quien asesora, basta editar CARGOS_ASESORES.
        """
        if self.es_admin:
            return True
        return (self.rol and self.rol.nombre == 'Usuario'
                and self.cargo in CARGOS_ASESORES)

    @property
    def puede_gestionar_asistencia(self):
        return self.es_admin or self.es_instructor_cargo

    @property
    def puede_registrar_equipos(self):
        if self.es_admin: return True
        return self.rol and self.rol.nombre == 'Usuario' and not self.es_celador_cargo

    # --- Datos que se imprimen en el carnet institucional ---
    @property
    def perfil_carnet(self):
        """Perfil del formato oficial (APRENDIZ, INSTRUCTOR, ...).

        No se deduce del rol ni se guarda en la base: se traduce desde `cargo`
        en app/utils/carnet.py, que es el unico sitio donde vive el mapeo.
        """
        from app.utils.carnet import perfil_de_cargo
        return perfil_de_cargo(self.cargo)

    @property
    def es_perfil_aprendiz(self):
        """El carnet de aprendiz es el unico con disposicion propia."""
        from app.utils.carnet import PERFIL_APRENDIZ
        return self.perfil_carnet == PERFIL_APRENDIZ

    @property
    def nombres_carnet(self):
        from app.utils.carnet import partir_nombre
        return partir_nombre(self.nombre, self.nombres, self.apellidos)[0]

    @property
    def apellidos_carnet(self):
        from app.utils.carnet import partir_nombre
        return partir_nombre(self.nombre, self.nombres, self.apellidos)[1]

    @property
    def documento_carnet(self):
        """Documento tal como se imprime: abreviatura del tipo y numero."""
        from app.utils.carnet import abreviatura_documento
        if not self.documento:
            return ''
        return f"{abreviatura_documento(self.tipo_documento)} {self.documento}"

    @property
    def ficha_numero(self):
        """Numero de ficha: el de la ficha enlazada, o el texto historico."""
        if self.ficha_ref:
            return self.ficha_ref.numero
        return self.ficha

    @property
    def programa_carnet(self):
        """Programa heredado de la ficha; si no hay ficha, el texto propio."""
        if self.ficha_ref:
            return self.ficha_ref.programa
        return self.programa

    @property
    def fecha_finalizacion_carnet(self):
        """Fecha de finalizacion, siempre heredada de la ficha.

        No hay campo propio a proposito: si cada aprendiz pudiera escribirla,
        volveria el problema de tener varias fechas para una misma ficha.
        """
        if self.ficha_ref:
            return self.ficha_ref.fecha_finalizacion_texto
        return ''

    @property
    def foto_aprobada(self):
        """La foto pasó la revisión de un administrador."""
        return self.foto_estado == ESTADO_APROBADA

    @property
    def foto_pendiente(self):
        return self.foto_estado == ESTADO_PENDIENTE

    @property
    def etiqueta_estado_foto(self):
        return ETIQUETAS_ESTADO_FOTO.get(self.foto_estado or ESTADO_SIN_FOTO,
                                         'Sin foto')

    @property
    def ruta_foto(self):
        """Ruta estatica para url_for('static', filename=...).

        Devuelve la foto del usuario si la tiene, o el avatar de su cargo.
        """
        from flask import current_app
        carpeta = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
        return ruta_foto_o_avatar(self.foto, self.cargo, carpeta)

    @property
    def avatar_cargo(self):
        """Avatar del cargo, para usarlo como respaldo si la foto no carga."""
        return avatar_de_cargo(self.cargo)

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
