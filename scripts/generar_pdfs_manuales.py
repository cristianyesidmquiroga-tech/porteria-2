#!/usr/bin/env python3
"""
Script para generar PDFs de los manuales de usuario del sistema SENA.
Convierte archivos Markdown a PDF con diseño profesional.
"""

import os
import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from datetime import datetime

# Configuración
MANUALES_DIR = Path(__file__).parent.parent / 'docs' / 'manuales'
PDFS_DIR = Path(__file__).parent.parent / 'docs' / 'pdfs'
CSS_TEMPLATE = """
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
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
    max-width: 100%;
}

h1 {
    color: #389e0d;
    font-size: 24pt;
    border-bottom: 3px solid #389e0d;
    padding-bottom: 10px;
    margin-top: 0;
    page-break-before: always;
}

h1:first-of-type {
    page-break-before: auto;
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

h4 {
    color: #95de64;
    font-size: 12pt;
    margin-top: 15px;
}

p {
    margin-bottom: 12px;
    text-align: justify;
}

ul, ol {
    margin-bottom: 12px;
    padding-left: 2em;
}

li {
    margin-bottom: 6px;
}

strong {
    color: #389e0d;
    font-weight: bold;
}

code {
    background-color: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 10pt;
}

pre {
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 5px;
    border-left: 4px solid #389e0d;
    overflow-x: auto;
}

pre code {
    background-color: transparent;
    padding: 0;
}

blockquote {
    border-left: 4px solid #389e0d;
    padding-left: 15px;
    margin: 15px 0;
    color: #666;
    font-style: italic;
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
    font-weight: bold;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

hr {
    border: none;
    border-top: 2px solid #389e0d;
    margin: 20px 0;
}

img {
    max-width: 100%;
    height: auto;
    margin: 15px 0;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.note {
    background-color: #fff7e6;
    border-left: 4px solid #faad14;
    padding: 10px 15px;
    margin: 15px 0;
    border-radius: 3px;
}

.tip {
    background-color: #f6ffed;
    border-left: 4px solid #52c41a;
    padding: 10px 15px;
    margin: 15px 0;
    border-radius: 3px;
}

.warning {
    background-color: #fff2f0;
    border-left: 4px solid #ff4d4f;
    padding: 10px 15px;
    margin: 15px 0;
    border-radius: 3px;
}

.step {
    background-color: #e6f7ff;
    border-left: 4px solid #1890ff;
    padding: 10px 15px;
    margin: 15px 0;
    border-radius: 3px;
}

.step-number {
    display: inline-block;
    background-color: #1890ff;
    color: white;
    width: 25px;
    height: 25px;
    line-height: 25px;
    text-align: center;
    border-radius: 50%;
    margin-right: 10px;
    font-weight: bold;
}

a {
    color: #389e0d;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
"""

def markdown_to_html_with_images(md_content):
    """Convierte Markdown a HTML con soporte para imágenes."""
    # Configuración de Markdown
    md = markdown.Markdown(
        extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'nl2br',
            'attr_list'
        ],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight'
            }
        }
    )
    
    html_content = md.convert(md_content)
    
    # Agregar header y footer
    full_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Manual de Usuario - SENA</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    return full_html

def generate_pdf(md_file, pdf_file):
    """Genera un PDF desde un archivo Markdown."""
    print(f"Procesando: {md_file.name}")
    
    # Leer archivo Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convertir a HTML
    html_content = markdown_to_html_with_images(md_content)
    
    # Crear CSS
    css = CSS(string=CSS_TEMPLATE)
    
    # Generar PDF
    try:
        HTML(string=html_content).write_pdf(
            pdf_file,
            stylesheets=[css],
            presentational_hints=True
        )
        print(f"✓ PDF generado: {pdf_file.name}")
        return True
    except Exception as e:
        print(f"✗ Error generando PDF: {e}")
        return False

def main():
    """Función principal."""
    print("=" * 60)
    print("Generador de PDFs - Manuales de Usuario SENA")
    print("=" * 60)
    
    # Crear directorio de PDFs
    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    
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

if __name__ == '__main__':
    main()
