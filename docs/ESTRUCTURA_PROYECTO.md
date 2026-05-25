# Estructura del Proyecto - Sistema de Gestión de Acceso SENA

## Descripción General
Este documento describe la estructura organizada del proyecto del Sistema de Gestión de Acceso del SENA - Centro de Gestión Agroempresarial del Oriente.

## Estructura de Directorios

```
porteria-2/
├── app/                          # Aplicación principal Flask
│   ├── __init__.py              # Inicialización de la aplicación
│   ├── models/                  # Modelos de base de datos
│   ├── routes/                  # Rutas y blueprints
│   ├── static/                  # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/               # Plantillas HTML
│   └── utils/                   # Utilidades y helpers
├── config/                      # Archivos de configuración
│   ├── .env                     # Variables de entorno (no en git)
│   ├── .env.example             # Ejemplo de variables de entorno
│   └── config.py                # Configuración de la aplicación
├── scripts/                     # Scripts de utilidad
│   └── create_admin.py          # Script para crear administrador
├── docker/                      # Archivos Docker
│   ├── Dockerfile               # Configuración de imagen Docker
│   ├── docker-compose.yml       # Configuración de servicios Docker
│   └── entrypoint.sh            # Script de entrada para contenedor
├── docs/                        # Documentación
│   └── manuales/                # Manuales de usuario
│       ├── README.md            # Índice de manuales
│       ├── manual_gestion_perfil.md
│       ├── manual_gestion_equipos.md
│       ├── manual_control_acceso.md
│       ├── manual_gestion_usuarios.md
│       └── manual_sistema_asistencia.md
├── instance/                    # Datos de instancia (base de datos local)
├── venv/                        # Entorno virtual Python (no en git)
├── .gitattributes              # Atributos Git
├── .gitignore                  # Archivos ignorados por Git
├── requirements.txt            # Dependencias Python
└── run.py                      # Punto de entrada de la aplicación
```

## Descripción de Directorios

### app/
Contiene toda la aplicación Flask:
- **models/**: Modelos SQLAlchemy para la base de datos
- **routes/**: Blueprints y rutas de la aplicación (auth, usuarios, porteria, equipos, main)
- **static/**: Archivos estáticos organizados por tipo (CSS, JS, imágenes)
- **templates/**: Plantillas HTML organizadas por módulo
- **utils/**: Funciones de utilidad (email, tareas, respaldos)

### config/
Archivos de configuración del sistema:
- **.env**: Variables de entorno reales (no versionado en Git)
- **.env.example**: Plantilla de variables de entorno (versionado)
- **config.py**: Clase Config con configuración de la aplicación

### scripts/
Scripts de utilidad y mantenimiento:
- **create_admin.py**: Script para crear/actualizar el usuario administrador

### docker/
Archivos para contenedorización:
- **Dockerfile**: Definición de la imagen Docker
- **docker-compose.yml**: Orquestación de servicios (web, postgres, backup)
- **entrypoint.sh**: Script de inicialización del contenedor

### docs/
Documentación del proyecto:
- **manuales/**: Manuales de usuario para cada módulo del sistema

### Archivos en Raíz
- **.gitignore**: Archivos ignorados por Git
- **.gitattributes**: Configuración de atributos Git
- **requirements.txt**: Dependencias Python del proyecto
- **run.py**: Punto de entrada para ejecutar la aplicación localmente

## Cambios Realizados

### Reorganización de Archivos
Los siguientes archivos fueron movidos para mejor organización:

| Archivo Original | Nueva Ubicación | Razón |
|-----------------|----------------|--------|
| .env | config/.env | Archivos de configuración |
| .env.example | config/.env.example | Archivos de configuración |
| config.py | config/config.py | Archivos de configuración |
| create_admin.py | scripts/create_admin.py | Scripts de utilidad |
| Dockerfile | docker/Dockerfile | Archivos Docker |
| docker-compose.yml | docker/docker-compose.yml | Archivos Docker |
| entrypoint.sh | docker/entrypoint.sh | Archivos Docker |
| manuales/ | docs/manuales/ | Documentación |

### Actualizaciones de Referencias
Se actualizaron las siguientes referencias en el código:

1. **app/__init__.py**: 
   - Cambiado: `app.config.from_object('config.Config')`
   - A: `app.config.from_object('config.config.Config')`

2. **docker/Dockerfile**:
   - Actualizado: `RUN chmod +x docker/entrypoint.sh`
   - Actualizado: `ENTRYPOINT ["./docker/entrypoint.sh"]`

3. **docker/docker-compose.yml**:
   - Actualizado: `build: context: .., dockerfile: docker/Dockerfile`
   - Actualizado: `env_file: - ../config/.env` (todos los servicios)

4. **docker/entrypoint.sh**:
   - Actualizado: `python scripts/create_admin.py`

5. **.gitignore**:
   - Actualizado: `config/.env` (en lugar de `.env`)

6. **scripts/create_admin.py**:
   - Agregado: `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))` para manejar la nueva ubicación

## Ejecución del Proyecto

### Desarrollo Local
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp config/.env.example config/.env
# Editar config/.env con tus valores

# Crear administrador
python scripts/create_admin.py

# Ejecutar aplicación
python run.py
```

### Docker
```bash
# Desde el directorio docker/
cd docker

# Configurar variables de entorno
cp ../config/.env.example ../config/.env
# Editar ../config/.env con tus valores

# Construir y ejecutar
docker-compose up --build
```

## Variables de Entorno

Las variables de entorno se configuran en `config/.env`:

- **SECRET_KEY**: Llave secreta para seguridad
- **DATABASE_URL**: URL de conexión a base de datos
- **MAIL_SERVER**: Servidor SMTP para correos
- **MAIL_PORT**: Puerto SMTP
- **MAIL_USERNAME**: Usuario SMTP
- **MAIL_PASSWORD**: Contraseña SMTP
- **ADMIN_EMAIL**: Correo del administrador
- **ADMIN_PASSWORD**: Contraseña del administrador

## Mantenimiento

### Crear Administrador
```bash
python scripts/create_admin.py
```

### Respaldos de Base de Datos
Los respaldos se generan automáticamente el primer día de cada mes. Se almacenan en `app/respaldos_mensuales/`.

### Actualizar Dependencias
```bash
pip freeze > requirements.txt
```

## Convenciones

### Nomenclatura de Archivos
- Python: `snake_case.py`
- HTML: `kebab-case.html`
- CSS: `kebab-case.css`
- JavaScript: `kebab-case.js`

### Estructura de Código
- Blueprints para módulos separados
- Modelos en carpeta `models/`
- Rutas en carpeta `routes/`
- Utilidades en carpeta `utils/`

## Soporte

Para reportar problemas o solicitar ayuda, contacte al equipo de soporte técnico del Centro de Gestión Agroempresarial del Oriente.

---

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Institución:** SENA - Centro de Gestión Agroempresarial del Oriente
