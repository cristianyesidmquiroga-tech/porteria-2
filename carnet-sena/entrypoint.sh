#!/bin/bash
echo "========================================="
echo "  Inicializando base de datos..."
echo "========================================="
python create_admin.py

echo "========================================="
echo "  Iniciando servidor Flask..."
echo "========================================="
exec python run.py
