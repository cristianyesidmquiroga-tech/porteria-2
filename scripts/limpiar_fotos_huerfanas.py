"""Pone a NULL la columna `foto` de los usuarios cuyo archivo ya no existe.

La aplicación funciona igual sin ejecutarlo: `Usuario.ruta_foto` comprueba que
el archivo exista y cae al avatar del cargo si falta. Este script solo deja la
base coherente con el disco, para que no queden nombres de archivo apuntando a
imágenes borradas.

Uso:
    python scripts/limpiar_fotos_huerfanas.py            # muestra qué haría
    python scripts/limpiar_fotos_huerfanas.py --aplicar  # ejecuta los cambios
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db  # noqa: E402
from app.models.usuarios import Usuario  # noqa: E402

aplicar = '--aplicar' in sys.argv

app = create_app()

with app.app_context():
    carpeta = os.path.join(app.root_path, 'static', 'uploads', 'profiles')
    huerfanos = []

    for usuario in Usuario.query.filter(Usuario.foto.isnot(None)).all():
        if not os.path.isfile(os.path.join(carpeta, usuario.foto)):
            huerfanos.append(usuario)

    if not huerfanos:
        print("No hay referencias huérfanas: la base y el disco coinciden.")
        sys.exit(0)

    print(f"Usuarios cuya foto ya no existe en el disco: {len(huerfanos)}")
    for usuario in huerfanos:
        print(f"  id={usuario.id:<5} cargo={usuario.cargo or 'sin cargo':<16} "
              f"archivo={usuario.foto}")

    if not aplicar:
        print("\nSimulación. Vuelve a ejecutarlo con --aplicar para hacer los cambios.")
        sys.exit(0)

    for usuario in huerfanos:
        usuario.foto = None
        # Sin foto el perfil deja de estar completo, así que el sistema volverá
        # a pedirle al usuario que suba una.
        usuario.perfil_completo = False

    db.session.commit()
    print(f"\nListo: {len(huerfanos)} referencias limpiadas. "
          "Esos usuarios verán el avatar de su cargo hasta que suban una foto.")
