from app.utils import get_colombia_time
from .. import db


class Ficha(db.Model):
    """Ficha de formacion: numero, programa y fecha de finalizacion.

    Existe para que el programa y la fecha de finalizacion se registren UNA
    sola vez por ficha, en lugar de que cada aprendiz los teclee en su perfil.
    Antes cada quien escribia su propia fecha y su propio nombre de programa,
    asi que dos aprendices de la misma ficha podian salir con datos distintos
    en el carnet y no habia forma de saber cual era el bueno.
    """

    __tablename__ = 'fichas'

    id = db.Column(db.Integer, primary_key=True)
    # El numero de ficha del SENA es numerico, pero se guarda como texto: la
    # columna `ficha` de usuarios ya era texto y hay que poder emparejarlas.
    numero = db.Column(db.String(20), unique=True, nullable=False)
    programa = db.Column(db.String(150), nullable=False)
    # Fecha, no DateTime: en el carnet solo se imprime el dia.
    fecha_finalizacion = db.Column(db.Date, nullable=True)
    # Una ficha que ya termino no se borra (sus aprendices siguen apuntando a
    # ella y su historial de accesos debe seguir teniendo sentido); se archiva
    # para que deje de aparecer en el selector del perfil.
    activa = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=get_colombia_time)

    aprendices = db.relationship('Usuario', backref='ficha_ref', lazy=True)

    @staticmethod
    def enlazar_por_numero(usuario, numero):
        """Enlaza al usuario con la ficha cuyo numero coincide, si existe.

        Sirve para las altas que hace el administrador y para la importacion
        masiva desde Excel, donde la ficha llega como texto. Si ese numero ya
        esta registrado, el aprendiz hereda ademas programa y fecha; si no,
        se queda el texto suelto y el carnet sale sin fecha hasta que alguien
        registre la ficha. Nunca crea fichas por su cuenta: inventar un
        programa a partir de una casilla de Excel seria peor que dejarlo vacio.
        """
        numero = (numero or '').strip()
        if not numero:
            return None
        ficha = Ficha.query.filter_by(numero=numero).first()
        if ficha:
            usuario.ficha_id = ficha.id
            usuario.programa = ficha.programa
        return ficha

    @property
    def etiqueta(self):
        """Texto para el selector: numero y programa juntos."""
        return f"{self.numero} - {self.programa}"

    @property
    def fecha_finalizacion_texto(self):
        """Fecha en el formato que se imprime en el carnet (dd/mm/aaaa)."""
        if not self.fecha_finalizacion:
            return ''
        return self.fecha_finalizacion.strftime('%d/%m/%Y')
