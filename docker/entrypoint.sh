#!/bin/bash
set -e

echo "========================================="
echo "  Inicializando base de datos..."
echo "========================================="
python scripts/create_admin.py

echo "========================================="
echo "  Iniciando servidor (gunicorn)..."
echo "========================================="
# UN SOLO worker a proposito: el planificador (APScheduler) vive dentro del
# proceso. Con dos workers el cierre nocturno correria dos veces (salidas
# duplicadas) y el respaldo mensual escribiria el mismo .xlsx desde dos
# procesos ANTES de borrar los datos de la base. La concurrencia sale de los
# hilos, no de los procesos.
# NO cambiar el 1 por "${GUNICORN_WORKERS:-...}": esa variable no existe a
# proposito (ver config/.env.example). Para escalar a mas procesos hay que
# sacar antes el planificador a su propio contenedor y poner
# EJECUTAR_TAREAS=false en los procesos web.
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 1 \
    --threads "${GUNICORN_THREADS:-8}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --forwarded-allow-ips '*' \
    "run:app"
