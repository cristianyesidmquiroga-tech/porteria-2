#!/usr/bin/env python3
"""
Script simplificado para generar PDFs de los manuales de usuario del sistema SENA.
Usa pandoc si está disponible, o markdown2pdf como alternativa.
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
    """Genera PDF usando pandoc."""
    print(f"Procesando con pandoc: {md_file.name}")
    
    # Comando pandoc con opciones para PDF profesional
    cmd = [
        'pandoc',
        str(md_file),
        '-o', str(pdf_file),
        '--pdf-engine=xelatex',
        '--variable=geometry:margin=2cm',
        '--variable=colorlinks=true',
        '--variable=linkcolor=green',
        '--variable=urlcolor=green',
        '--variable=toccolor=green',
        '--toc',
        '--toc-depth=3',
        '--highlight-style=tango',
        '--metadata=title="Manual de Usuario - SENA"',
        '--metadata=author="SENA - Centro de Gestión Agroempresarial del Oriente"'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
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

def generate_pdf_with_markdown2pdf(md_file, pdf_file):
    """Genera PDF usando markdown2pdf."""
    print(f"Procesando con markdown2pdf: {md_file.name}")
    
    try:
        import markdown2pdf
        markdown2pdf.convert(str(md_file), str(pdf_file))
        print(f"✓ PDF generado: {pdf_file.name}")
        return True
    except ImportError:
        print("✗ markdown2pdf no está instalado")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def generate_pdf_with_weasyprint(md_file, pdf_file):
    """Genera PDF usando weasyprint."""
    print(f"Procesando con weasyprint: {md_file.name}")
    
    try:
        import markdown
        from weasyprint import HTML, CSS
        
        # Leer Markdown
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convertir a HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'codehilite', 'toc', 'nl2br']
        )
        
        # CSS básico
        css = CSS(string="""
            @page {
                size: A4;
                margin: 2cm;
                @top-center {
                    content: "SENA - Centro de Gestión Agroempresarial del Oriente";
                    font-size: 10pt;
                    color: #666;
                }
                @bottom-center {
                    content: counter(page) " / " counter(pages);
                    font-size: 10pt;
                    color: #666;
                }
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #389e0d;
                font-size: 24pt;
                border-bottom: 3px solid #389e0d;
                padding-bottom: 10px;
                margin-top: 0;
            }
            h2 {
                color: #52c41a;
                font-size: 18pt;
                border-bottom: 2px solid #52c41a;
                padding-bottom: 8px;
                margin-top: 30px;
            }
            h3 {
                color: #73d13d;
                font-size: 14pt;
                margin-top: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #389e0d;
                color: white;
            }
            code {
                background-color: #f5f5f5;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }
            pre {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #389e0d;
            }
            blockquote {
                border-left: 4px solid #389e0d;
                padding-left: 15px;
                margin: 15px 0;
                color: #666;
                font-style: italic;
            }
        """)
        
        # Generar PDF
        full_html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Manual de Usuario - SENA</title>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        HTML(string=full_html).write_pdf(pdf_file, stylesheets=[css])
        print(f"✓ PDF generado: {pdf_file.name}")
        return True
        
    except ImportError:
        print("✗ weasyprint no está instalado")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def generate_pdf(md_file, pdf_file):
    """Genera PDF usando el método disponible."""
    # Intentar pandoc primero (mejor calidad)
    if check_pandoc():
        if generate_pdf_with_pandoc(md_file, pdf_file):
            return True
    
    # Intentar weasyprint
    if generate_pdf_with_weasyprint(md_file, pdf_file):
        return True
    
    # Intentar markdown2pdf
    if generate_pdf_with_markdown2pdf(md_file, pdf_file):
        return True
    
    print("✗ No se pudo generar el PDF. Instale pandoc, weasyprint o markdown2pdf")
    return False

def main():
    """Función principal."""
    print("=" * 60)
    print("Generador de PDFs - Manuales de Usuario SENA")
    print("=" * 60)
    
    # Crear directorio de PDFs
    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Verificar pandoc
    if check_pandoc():
        print("✓ Pandoc detectado - Se usará para generar PDFs de alta calidad")
    else:
        print("⚠ Pandoc no detectado - Se intentará con weasyprint")
        print("  Para instalar pandoc: https://pandoc.org/installing.html")
    
    # Obtener archivos Markdown
    md_files = list(MANUALES_DIR.glob('*.md'))
    
    if not md_files:
        print("No se encontraron archivos Markdown en:", MANUALES_DIR)
        return
    
    print(f"\nEncontrados {len(md_files)} manuales para convertir\n")
    
    # Generar PDFs
    success_count = 0
    for md_file in sorted(md_files):
        pdf_file = PDFS_DIR / f"{md_file.stem}.pdf"
        if generate_pdf(md_file, pdf_file):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"Proceso completado: {success_count}/{len(md_files)} PDFs generados")
    print(f"PDFs guardados en: {PDFS_DIR}")
    print("=" * 60)
    
    if success_count == 0:
        print("\nPara generar PDFs, instale una de las siguientes herramientas:")
        print("1. Pandoc (recomendado): https://pandoc.org/installing.html")
        print("2. WeasyPrint: pip install weasyprint")
        print("3. Markdown2PDF: pip install markdown2pdf")

if __name__ == '__main__':
    main()
