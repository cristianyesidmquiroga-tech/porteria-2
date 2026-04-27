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

    # Buscar si existe el correo
    email = "admin@sena.edu.co"
    admin = Usuario.query.filter_by(correo=email).first()
    
    if admin:
        # Actualizar para quitar todas las restricciones
        admin.perfil_completo = True
        admin.correo_verificado = True
        admin.debe_cambiar_contrasena = False
        admin.intentos_fallidos = 0
        admin.bloqueado_hasta = None
        admin.tipo_sangre = 'O+'
        admin.foto = 'default_profile.png'
        admin.set_password('SenaAdmin2026*')
        db.session.commit()
        print(f"Admin actualizado SIN restricciones: {email}")
        print(f"Contraseña: SenaAdmin2026*")
    else:
        admin = Usuario(
            nombre="Super Administrador",
            correo=email,
            documento="999999999",
            rol_id=rol_admin.id,
            cargo="Administrador",
            perfil_completo=True,
            correo_verificado=True,
            debe_cambiar_contrasena=False,
            intentos_fallidos=0,
            bloqueado_hasta=None,
            tipo_sangre='O+',
            foto='default_profile.png'
        )
        admin.set_password('SenaAdmin2026*')
        db.session.add(admin)
        db.session.commit()
        print(f"========================================")
        print(f"  SUPER ADMIN CREADO SIN RESTRICCIONES")
        print(f"========================================")
        print(f"  Correo:     {email}")
        print(f"  Contraseña: SenaAdmin2026*")
        print(f"  Rol:        Admin (acceso total)")
        print(f"========================================")
