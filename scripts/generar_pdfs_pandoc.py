#!/usr/bin/env python3
"""
Script para generar PDFs de los manuales de usuario del sistema SENA usando pandoc.
Pandoc es la opción recomendada para Windows ya que no requiere dependencias complejas.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Configuración
MANUALES_DIR = Path(__file__).parent.parent / 'docs' / 'manuales'
PDFS_DIR = Path(__file__).parent.parent / 'docs' / 'pdfs'

def check_pandoc():
    """Verifica si pandoc está instalado."""
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def generate_pdf_with_pandoc(md_file, pdf_file):
    """Genera PDF usando pandoc con diseño profesional."""
    print(f"Procesando: {md_file.name}")
    
    # Comando pandoc con opciones para PDF profesional
    cmd = [
        'pandoc',
        str(md_file),
        '-o', str(pdf_file),
        '--pdf-engine=xelatex',
        '--variable=geometry:margin=2cm',
        '--variable=geometry:a4paper',
        '--variable=colorlinks=true',
        '--variable=linkcolor=389e0d',
        '--variable=urlcolor=389e0d',
        '--variable=toccolor=389e0d',
        '--toc',
        '--toc-depth=3',
        '--highlight-style=tango',
        '--number-sections',
        '--metadata=title="Manual de Usuario - SENA"',
        '--metadata=author="SENA - Centro de Gestión Agroempresarial del Oriente"',
        '--metadata=date="' + datetime.now().strftime('%d/%m/%Y') + '"',
        '--variable=fontsize:11pt',
        '--variable=mainfont="Arial"',
        '--variable=sansfont="Arial"',
        '--variable=monofont="Courier New"',
        '-V', 'colorlinks=true',
        '-V', 'linkcolor=389e0d',
        '-V', 'urlcolor=389e0d',
        '-V', 'toccolor=389e0d',
        '-V', 'geometry:margin=2cm',
        '-V', 'geometry:a4paper'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"✓ PDF generado: {pdf_file.name}")
            return True
        else:
            print(f"✗ Error pandoc: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout al generar PDF")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Función principal."""
    print("=" * 70)
    print("Generador de PDFs - Manuales de Usuario SENA (Pandoc)")
    print("=" * 70)
    
    # Crear directorio de PDFs
    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Verificar pandoc
    if not check_pandoc():
        print("\n❌ Pandoc no está instalado en su sistema.")
        print("\nPara instalar Pandoc en Windows:")
        print("1. Descargue el instalador desde: https://pandoc.org/installing.html")
        print("2. Ejecute el instalador y siga las instrucciones")
        print("3. Reinicie su terminal/IDE después de la instalación")
        print("\nAlternativamente, puede usar winget:")
        print("  winget install --id JohnMacFarlane.Pandoc")
        return
    
    print("✓ Pandoc detectado - Generando PDFs de alta calidad\n")
    
    # Obtener archivos Markdown
    md_files = list(MANUALES_DIR.glob('*.md'))
    
    if not md_files:
        print("No se encontraron archivos Markdown en:", MANUALES_DIR)
        return
    
    print(f"Encontrados {len(md_files)} manuales para convertir\n")
    
    # Generar PDFs
    success_count = 0
    failed_files = []
    
    for md_file in sorted(md_files):
        pdf_file = PDFS_DIR / f"{md_file.stem}.pdf"
        if generate_pdf_with_pandoc(md_file, pdf_file):
            success_count += 1
        else:
            failed_files.append(md_file.name)
    
    print("\n" + "=" * 70)
    print(f"Proceso completado: {success_count}/{len(md_files)} PDFs generados")
    print(f"PDFs guardados en: {PDFS_DIR}")
    print("=" * 70)
    
    if failed_files:
        print(f"\n⚠ Archivos que fallaron: {', '.join(failed_files)}")
        print("Asegúrese de que LaTeX esté instalado para usar xelatex")

if __name__ == '__main__':
    main()
