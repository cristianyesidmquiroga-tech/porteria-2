FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Bogota

WORKDIR /app

# libglib es requerida por opencv-python-headless (deteccion facial de la foto).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 tzdata curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker/entrypoint.sh \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/app/static/uploads/profiles /app/app/respaldos_mensuales \
    && chown -R appuser:appuser /app

# No correr como root: limita el impacto de una ejecucion de codigo arbitrario.
USER appuser

EXPOSE 5000

ENTRYPOINT ["./docker/entrypoint.sh"]
