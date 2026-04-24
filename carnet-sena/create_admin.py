from app import create_app, db
from app.models.usuarios import Usuario, Rol

app = create_app()

with app.app_context():
    # Buscar el rol Admin
    rol_admin = Rol.query.filter_by(nombre='Admin').first()
    if not rol_admin:
        rol_admin = Rol(nombre='Admin')
        db.session.add(rol_admin)
        db.session.commit()
        print("Rol Admin creado.")

    # Buscar si existe el correo
    email = "admin2@sena.edu.co"
    admin = Usuario.query.filter_by(correo=email).first()
    
    if admin:
        print(f"El admin ya existe: {email} / Contraseña: (la que se haya configurado)")
    else:
        admin = Usuario(
            nombre="Administrador Principal",
            correo=email,
            documento="999999999",
            rol_id=rol_admin.id,
            cargo="Administrador",
            perfil_completo=True,
            correo_verificado=True
        )
        admin.set_password('SenaAdmin2026*')
        db.session.add(admin)
        db.session.commit()
        print(f"NUEVO ADMIN CREADO EXITOSAMENTE:")
        print(f"Correo: {email}")
        print(f"Contraseña: SenaAdmin2026*")
