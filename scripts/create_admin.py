import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.usuarios import Usuario, Rol

app = create_app()

with app.app_context():
    # Crear rol Admin si no existe
    rol_admin = Rol.query.filter_by(nombre='Admin').first()
    if not rol_admin:
        rol_admin = Rol(nombre='Admin')
        db.session.add(rol_admin)
        db.session.commit()
        print("Rol Admin creado.")

    # Crear rol Usuario si no existe
    rol_usuario = Rol.query.filter_by(nombre='Usuario').first()
    if not rol_usuario:
        rol_usuario = Rol(nombre='Usuario')
        db.session.add(rol_usuario)
        db.session.commit()
        print("Rol Usuario creado.")

    # Crear Punto de Acceso predeterminado si no existe
    from app.models.accesos import PuntoAcceso
    punto = PuntoAcceso.query.get(1)
    if not punto:
        punto = PuntoAcceso(id=1, nombre='Portería Principal', tipo='General')
        db.session.add(punto)
        db.session.commit()
        print("Punto de Acceso 'Portería Principal' (ID: 1) creado.")

    # Credenciales del super admin: obligatorias, sin valor por defecto.
    email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')

    if not email:
        raise SystemExit(
            "ERROR: falta ADMIN_EMAIL. Configuralo antes de arrancar el sistema."
        )

    admin = Usuario.query.filter_by(correo=email).first()

    if admin:
        # NUNCA se resetea la contrasena de un admin existente: este script
        # corre en cada arranque del contenedor y hacerlo revertiria la clave
        # del administrador en cada despliegue.
        print(f"Admin ya existe, no se modifica: {email}")
    else:
        if not admin_password:
            raise SystemExit(
                "ERROR: no existe el admin y falta ADMIN_PASSWORD para crearlo. "
                "Configura una contrasena fuerte en las variables de entorno."
            )
        if len(admin_password) < 12:
            raise SystemExit(
                "ERROR: ADMIN_PASSWORD debe tener al menos 12 caracteres."
            )

        admin = Usuario(
            nombre="Super Administrador",
            correo=email,
            documento=os.environ.get('ADMIN_DOCUMENTO', '999999999'),
            rol_id=rol_admin.id,
            cargo="Administrador",
            perfil_completo=True,
            correo_verificado=True,
            debe_cambiar_contrasena=True,
            intentos_fallidos=0,
            bloqueado_hasta=None,
            tipo_sangre='O+',
            foto=None
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print("========================================")
        print("  SUPER ADMIN CREADO")
        print(f"  Correo: {email}")
        print("  Debe cambiar la contrasena en el primer ingreso.")
        print("========================================")
