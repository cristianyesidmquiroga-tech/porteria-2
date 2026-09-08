#!/bin/bash
#
# Arranque del contenedor: esperar la base, preparar los datos mínimos y ceder
# el proceso a gunicorn.
set -euo pipefail

echo "========================================="
echo "  Esperando a la base de datos..."
echo "========================================="

# Sin esta espera, el contenedor entra en ciclo de reinicio siempre que la base
# tarde un poco más que la aplicación: `create_admin.py` se conecta nada más
# arrancar y muere si no hay nadie al otro lado. Pasa en cada despliegue donde
# la base y la aplicación suben a la vez, y el síntoma —un contenedor que se
# reinicia sin parar— no dice en ninguna parte que la causa es una carrera.
INTENTOS="${ESPERA_BASE_INTENTOS:-30}"
PAUSA="${ESPERA_BASE_PAUSA:-2}"

for intento in $(seq 1 "$INTENTOS"); do
    if python - <<'PY'
import os
import sys
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL")
if not url:
    print("ERROR: falta DATABASE_URL.", file=sys.stderr)
    sys.exit(2)

partes = urlparse(url)
if not partes.scheme.startswith("postgres"):
    # Otra base (por ejemplo SQLite en una prueba local): no hay nada que
    # esperar, se sigue de largo.
    sys.exit(0)

import psycopg2

try:
    psycopg2.connect(
        dbname=(partes.path or "/").lstrip("/"),
        user=partes.username,
        password=partes.password,
        host=partes.hostname,
        port=partes.port or 5432,
        connect_timeout=3,
    ).close()
except Exception as error:  # noqa: BLE001 - se informa y se reintenta
    print(f"  todavía no responde: {error}".rstrip(), file=sys.stderr)
    sys.exit(1)
PY
    then
        echo "  la base responde."
        break
    fi

    if [ "$intento" -eq "$INTENTOS" ]; then
        echo "ERROR: la base no respondió tras $INTENTOS intentos." >&2
        exit 1
    fi
    sleep "$PAUSA"
done

echo "========================================="
echo "  Preparando roles, punto de acceso y administrador..."
echo "========================================="
python scripts/create_admin.py

echo "========================================="
echo "  Iniciando servidor (gunicorn)..."
echo "========================================="

# Cuántos proxies propios hay delante. `*` significa "confía en el
# X-Forwarded-* de quien sea", y eso solo es seguro si NADIE puede alcanzar
# este puerto sin pasar por el proxy. Si alguna vez el contenedor queda
# expuesto directo, con `*` cualquiera falsea su IP de origen y se salta los
# límites por IP —el mismo agujero que config/.env.example advierte para
# PROXIES_CONFIABLES—.
#
# Por omisión se confía en el rango privado de la red de Docker, que es por
# donde entra el proxy. Se puede ampliar con la variable si hiciera falta.
PROXIES="${GUNICORN_PROXIES_CONFIABLES:-10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,127.0.0.1}"

# UN SOLO worker a propósito: el planificador (APScheduler) vive dentro del
# proceso. Con dos workers el cierre nocturno correría dos veces —salidas
# duplicadas— y el respaldo mensual escribiría el mismo .xlsx desde dos
# procesos ANTES de borrar los datos de la base. La concurrencia sale de los
# hilos, no de los procesos.
#
# NO cambiar el 1 por "${GUNICORN_WORKERS:-...}": esa variable no existe a
# propósito (ver config/.env.example). Para escalar a más procesos hay que
# sacar antes el planificador a su propio contenedor y poner
# EJECUTAR_TAREAS=false en los procesos web.
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 1 \
    --threads "${GUNICORN_THREADS:-8}" \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    --forwarded-allow-ips "$PROXIES" \
    "run:app"
