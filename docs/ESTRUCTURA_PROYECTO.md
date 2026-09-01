# Estructura del Proyecto — Sistema de Gestión de Acceso SENA

Descripción de cómo está organizado el repositorio. Verificada contra el
contenido real del repo. Para despliegue, variables de entorno y tareas
programadas, ver `docs/DESPLIEGUE_Y_OPERACION.md`.

## Árbol de directorios

```
porteria-2/
├── app/                              # Aplicación Flask
│   ├── __init__.py                   # create_app(): config, seguridad, blueprints, tareas
│   ├── models/                       # Modelos SQLAlchemy
│   │   ├── usuarios.py               # Usuario, Rol, Carnet, TurnoCelador, avatares
│   │   ├── entidades.py              # Visitante, Vehiculo, Equipo, ObjetoExterno
│   │   ├── accesos.py                # PuntoAcceso, Acceso, Auditoria
│   │   ├── asistencia.py             # AsistenciaClase
│   │   ├── fichas.py                 # Ficha de formación
│   │   ├── mensajes.py               # Mensajería usuario <-> administradores
│   │   └── movimientos.py            # Movimientos por tipo de entidad
│   ├── routes/                       # Blueprints
│   │   ├── auth/                     # login, registro, verificación, recuperación,
│   │   │                             #   logout, desafío anti-bot
│   │   ├── main/                     # raíz, /salud, política de privacidad
│   │   ├── usuarios/                 # perfil, fotos, admin de usuarios, asistencia,
│   │   │                             #   fichas, mensajes, ayuda, tutorial, revisión de fotos
│   │   ├── porteria/                 # dashboard, escáner, pases, reportes,
│   │   │                             #   historial por persona, historial de clases
│   │   └── equipos/                  # registro/eliminación de equipos propios
│   ├── static/
│   │   ├── css/                      # dividido por módulo (compartido/, layout/, vistas/)
│   │   ├── js/                       # un archivo por vista + librerías fijadas por versión
│   │   ├── img/                      # avatares SVG por cargo, imágenes
│   │   ├── modelos/                  # modelos ONNX (detección facial YuNet, segmentación)
│   │   ├── fonts/, webfonts/
│   │   └── uploads/                  # ubicación ANTIGUA de fotos (se migran al arrancar)
│   ├── templates/                    # Jinja2: auth/, main/, usuarios/, porteria/,
│   │                                 #   partials/ (_sidebar, _header, _captcha), errores/
│   ├── utils/
│   │   ├── barras.py                 # código de barras Code128 en SVG (sin dependencias)
│   │   ├── captcha.py                # desafío anti-bot autoalojado (prueba de trabajo)
│   │   ├── carnet.py                 # perfiles del carnet impreso, partición de nombre
│   │   ├── documentos.py             # tipos de documento y validación por tipo
│   │   ├── email.py                  # envío SMTP con cola, reintentos y modo directo
│   │   ├── fotos.py                  # almacenamiento/servicio de fotos con permisos
│   │   ├── imagenes.py               # procesado y validación facial de la foto
│   │   ├── limitador.py              # catálogo completo de límites de peticiones
│   │   ├── perfiles.py               # regla de "perfil completo"
│   │   ├── respaldos.py              # respaldo mensual (exporta a Excel y BORRA)
│   │   ├── security.py               # sesión única, validación de contraseña, sanitizado
│   │   └── tareas.py                 # cierre automático de medianoche
│   └── respaldos_mensuales/          # destino de los .xlsx mensuales (volumen en Docker)
├── config/
│   ├── .env                          # variables reales (NO se commitea)
│   ├── .env.example                  # referencia comentada de TODAS las variables
│   └── config.py                     # clase Config (exige SECRET_KEY y DATABASE_URL)
├── docker/
│   ├── Dockerfile                    # python:3.12-slim, usuario no root, TZ Bogotá
│   ├── docker-compose.yml            # UN solo servicio (web); la BD es externa
│   └── entrypoint.sh                 # create_admin.py + gunicorn con 1 worker
├── docs/
│   ├── DESPLIEGUE_Y_OPERACION.md     # operación: tareas, respaldos, correo, volúmenes
│   ├── ESTRUCTURA_PROYECTO.md        # este archivo
│   ├── ESTADO_AUDITORIA.md
│   └── manuales/                     # manuales de usuario (ver su README.md)
├── scripts/
│   ├── create_admin.py               # corre en CADA despliegue (roles, punto, superadmin)
│   ├── probar_correo.py              # prueba la configuración SMTP (--puerto-25)
│   ├── limpiar_fotos_huerfanas.py    # borra fotos sin usuario asociado
│   └── generar_pdfs_*.py             # convierten los manuales a PDF (3 variantes)
├── tests/                            # pytest (SQLite en memoria, ver conftest.py)
│   ├── conftest.py
│   ├── fixtures/
│   └── test_*.py                     # autenticación, portería, carnet, correo, fotos,
│                                     #   fichas, mensajes, límites, importación Excel...
├── instance/                         # datos de instancia local
│   ├── fotos_perfil/                 # ubicación ACTUAL de las fotos de perfil
│   └── local_dev.sqlite              # base local de desarrollo
├── .venv/                            # entorno virtual local (no versionado)
├── requirements.txt                  # dependencias de producción
├── requirements-dev.txt              # dependencias de desarrollo/pruebas
└── run.py                            # punto de entrada
```

## Decisiones de estructura que conviene conocer

- **Las fotos de perfil NO viven en `static/`.** Están en
  `instance/fotos_perfil/` (o en `CARPETA_FOTOS` si se configura) y se sirven
  por la vista `/foto/<id>`, que comprueba sesión y permiso. `static/uploads/`
  es la ubicación antigua: lo que quede ahí se migra automáticamente al
  arrancar.
- **Los límites de peticiones están centralizados** en
  `app/utils/limitador.py` (catálogo `LIMITES` + lista `EXENTOS`), no como
  decoradores repartidos por las vistas.
- **Los modelos de IA viajan en el repo** (`app/static/modelos/`) porque el
  contenedor de producción no tiene internet garantizado en ejecución.
- **Las librerías JS están fijadas por versión en el nombre del archivo**
  (`html5-qrcode-2.3.8.min.js`, `chart-4.5.1.umd.min.js`...) y se sirven
  desde `static/`, no desde CDN sin versión.
- `docker-compose.yml` **no** define servicios `postgres` ni `backup`: la base
  es externa (Coolify/VPS) y el "respaldo" es la tarea mensual interna
  documentada en `docs/DESPLIEGUE_Y_OPERACION.md`.

## Dependencias principales

Ver `requirements.txt` (versiones fijadas). Núcleo: Flask 3, Flask-SQLAlchemy,
Flask-Login, Flask-WTF (CSRF), Flask-Limiter, Flask-APScheduler, gunicorn,
psycopg2, pandas + openpyxl (importación/respaldo Excel), Pillow +
opencv-python-headless (procesado y validación facial de fotos), dnspython
(modo directo de correo).

## Ejecución

- **Desarrollo local:** ver `docs/DESPLIEGUE_Y_OPERACION.md` §7 (entorno
  `.venv`, `config/.env`, `python run.py`, `python -m pytest tests/`).
- **Producción:** contenedor Docker desplegado vía Coolify; la configuración
  vive en las variables de entorno de la plataforma.

## Convenciones

- Código y comentarios en español; commits cortos `tipo: descripción`.
- Python `snake_case.py`; CSS/JS divididos por módulo con nombre descriptivo.
- Rutas de datos con prefijo `/api/`; páginas sin prefijo.
- Ningún secreto, contraseña ni IP del servidor se escribe en el repositorio
  (incluida esta carpeta `docs/`).
