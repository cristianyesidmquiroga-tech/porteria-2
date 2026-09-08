# Imagen de la aplicación de portería.
#
# Dos etapas. La primera instala las dependencias en un entorno propio, la
# segunda solo se lleva ese entorno: lo que hace falta para instalar no viaja a
# producción. Menos peso y menos superficie.

# ---------------------------------------------------------------- construcción
FROM python:3.12-slim AS construccion

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Solo el archivo de dependencias. Mientras no cambie, esta capa se reutiliza y
# la instalación no se repite en cada despliegue; copiar el código antes la
# invalidaría con cualquier cambio de una plantilla.
COPY requirements.txt /tmp/requirements.txt

RUN python -m venv /opt/entorno \
    && /opt/entorno/bin/pip install --no-cache-dir -r /tmp/requirements.txt


# ------------------------------------------------------------------ ejecución
FROM python:3.12-slim AS ejecucion

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/entorno/bin:$PATH" \
    TZ=America/Bogota

# `libglib` la necesita opencv-python-headless, que es lo que detecta el rostro
# en la foto de perfil. `tzdata` para que TZ signifique algo: sin ella el
# contenedor va en UTC y el cierre nocturno correría cinco horas antes de la
# medianoche de Colombia.
#
# `curl` ya no se instala: la sonda de salud la hace Python, que aquí ya está.
# Un binario menos dentro de la imagen es una superficie menos.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY --from=construccion /opt/entorno /opt/entorno

# El usuario se crea ANTES de copiar el código, para copiarlo ya con su dueño
# puesto. Con `COPY` y después `chown -R` el árbol entero se duplicaba en una
# segunda capa y la imagen pesaba casi el doble.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

COPY --chown=appuser:appuser . .

# Las carpetas de datos se crean AQUÍ, con su dueño, y no es un detalle
# cosmético: al montar un volumen con nombre sobre una carpeta que ya existe en
# la imagen, Docker copia su contenido y sus permisos al volumen. Si la carpeta
# no existiera, el volumen nacería propiedad de root y `appuser` no podría
# escribir: subir una foto de perfil fallaría, y fallaría en silencio.
RUN mkdir -p /app/datos/fotos_perfil \
             /app/app/static/uploads/profiles \
             /app/app/respaldos_mensuales \
             /app/instance \
    && chown -R appuser:appuser /app/datos \
                                /app/app/static/uploads \
                                /app/app/respaldos_mensuales \
                                /app/instance \
    && chmod +x docker/entrypoint.sh

# No se corre como root: acota lo que puede hacer una ejecución de código
# arbitrario si algún día la hay.
USER appuser

EXPOSE 5000

# La sonda va también en la imagen y no solo en el Compose, para que quien
# ejecute el contenedor a mano la tenga igual. `start-period` es generoso
# porque el primer arranque espera a la base y crea las tablas.
HEALTHCHECK --interval=60s --timeout=10s --start-period=90s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/salud', timeout=5).status == 200 else 1)"]

ENTRYPOINT ["./docker/entrypoint.sh"]
