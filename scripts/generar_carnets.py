# -*- coding: utf-8 -*-
"""
Generador de carnets institucionales SENA (piezas listas para imprimir).

Genera los 5 carnets (APRENDIZ, INSTRUCTOR, CONTRATISTA, FUNCIONARIO,
SUBDIRECTOR) como piezas independientes en PNG a 300 DPI, tamano CR80
vertical (54 x 85.6 mm -> 638 x 1011 px), con diseno uniforme.

Uso:
    .\\venv\\Scripts\\python.exe scripts\\generar_carnets.py

Salida:
    docs/carnets/carnet_<rol>.png   (300 DPI, listo para imprimir)
    docs/carnets/carnet_<rol>.html  (fuente editable de cada pieza)
"""

import random
import shutil
import subprocess
import sys
from pathlib import Path

# ================================================================
# GENERALIDADES -- Editar SOLO este bloque para cambiar de Regional
# / Centro de formacion. El cambio se aplica a los 5 carnets sin
# tener que rediseniar ni tocar la estructura de cada uno.
# ================================================================
GENERALIDADES = {
    "regional": "Regional Santander",
    "centro_1": "Centro de Gesti\u00f3n",
    "centro_2": "Agroempresarial del Oriente",
}

ASEGURADORA = {
    "nombre": "Aseguradora Aurora",
    "telefono": "Tel: 601-7443718 Op. 1",
    "poliza": "Poliza: No. 100603",
}

VERDE_SENA = "#39A900"  # Verde institucional SENA

# Jornada marcada por rol: "Manana", "Mixta", "Nocturna" o "" (sin marcar)
JORNADA_MARCADA = {
    "APRENDIZ": "",
    "INSTRUCTOR": "",
    "CONTRATISTA": "",
    "FUNCIONARIO": "",
    "SUBDIRECTOR": "",
}

# Campos editables (placeholders entre llaves, listos para personalizar)
ROLES = {
    "APRENDIZ": {
        "doc_label": "Tip.",
        "documento": "{N\u00famero de documento}",
        "extra": True,  # ficha, programa, aseguradora
    },
    "INSTRUCTOR": {"doc_label": "C.C.", "documento": "{N\u00famero de documento}", "extra": False},
    "CONTRATISTA": {"doc_label": "C.C.", "documento": "{N\u00famero de documento}", "extra": False},
    "FUNCIONARIO": {"doc_label": "C.C.", "documento": "{N\u00famero de documento}", "extra": False},
    "SUBDIRECTOR": {"doc_label": "C.C.", "documento": "{N\u00famero de documento}", "extra": False},
}

# Dimenssiones de salida: CR80 vertical a 300 DPI
CARD_W, CARD_H = 638, 1011

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "carnets"

# ----------------------------------------------------------------
# Piezas SVG
# ----------------------------------------------------------------

def sena_logo_svg(width=128):
    """Logo SENA en verde institucional (#39A900)."""
    return f'''<svg width="{width}" viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
  <g fill="{VERDE_SENA}">
    <circle cx="100" cy="28" r="25"/>
    <rect x="6" y="122" width="188" height="20"/>
    <polygon points="58,142 96,142 66,232 30,232"/>
    <polygon points="104,142 142,142 170,232 134,232"/>
  </g>
  <text x="100" y="106" text-anchor="middle" font-family="Arial, sans-serif"
        font-weight="900" font-size="54" letter-spacing="3" fill="{VERDE_SENA}">SENA</text>
</svg>'''


def foto_placeholder_svg():
    """Espacio para foto tipo carnet (superior derecha)."""
    return '''<svg viewBox="0 0 24 24" width="80" height="80">
  <path fill="#888" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
</svg>'''


def barcode_svg(seed, width=380, height=54):
    """Codigo de barras (patron visual determinista por rol)."""
    rng = random.Random(seed)
    bars, x = [], 0
    while x < width - 4:
        bw = rng.choice([2, 2, 3, 3, 4, 5, 6])
        gap = rng.choice([2, 2, 3, 3, 4])
        if x + bw <= width:
            bars.append(f'<rect x="{x}" y="0" width="{bw}" height="{height}" fill="#000"/>')
        x += bw + gap
    return (f'<svg width="{width}" height="{height}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(bars)}</svg>')


def jornada_html(marcada):
    """Campo Jornada con opciones Manana / Mixta / Nocturna marcables."""
    opciones = []
    for op in ["Ma\u00f1ana", "Mixta", "Nocturna"]:
        clase = "jornada-opcion marcada" if marcada == op else "jornada-opcion"
        opciones.append(f'<span class="{clase}"><span class="jornada-check"></span>{op}</span>')
    return ('<div class="carnet-jornada"><span class="label">Jornada:</span>'
            + "".join(opciones) + "</div>")


# ----------------------------------------------------------------
# Plantilla HTML de cada carnet
# ----------------------------------------------------------------

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: #fff; }
.carnet {
    width: %(W)dpx; height: %(H)dpx;
    border: 4px solid #ccc; border-radius: 26px;
    background: #fff; font-family: Arial, sans-serif;
    display: flex; flex-direction: column; overflow: hidden;
}
.carnet-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 24px 34px 18px 34px; border-bottom: 4px solid #ccc;
}
.carnet-photo {
    width: 132px; height: 176px; background: #ddd; border-radius: 12px;
    display: flex; justify-content: center; align-items: center; overflow: hidden;
}
.carnet-photo img { width: 100%%; height: 100%%; object-fit: cover; }
.carnet-body { padding: 18px 34px; flex-grow: 1; font-size: 26px; line-height: 1.35; color: #333; }
.carnet-role {
    font-weight: bold; font-size: 34px; text-transform: uppercase;
    margin-bottom: 14px; padding-bottom: 10px; border-bottom: 2px solid #eee; color: %(VERDE)s;
}
.carnet-name { font-weight: bold; font-size: 30px; margin-bottom: 4px; }
.carnet-surname { font-size: 30px; margin-bottom: 14px; }
.info-line { margin-bottom: 8px; }
.label { font-weight: bold; }
.carnet-jornada { margin-bottom: 8px; display: flex; align-items: center; gap: 14px; }
.jornada-opcion { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
.jornada-check {
    display: inline-block; width: 20px; height: 20px;
    border: 3px solid #333; border-radius: 4px; background: #fff;
}
.jornada-opcion.marcada { font-weight: bold; }
.jornada-opcion.marcada .jornada-check { background: %(VERDE)s; border-color: %(VERDE)s; }
.carnet-small-text { font-size: 21px; line-height: 1.25; margin-top: 12px; color: #444; }
.carnet-barcode { margin-top: 16px; }
.carnet-footer {
    background: #e6e6e6; padding: 16px 34px; font-size: 25px;
    border-top: 2px solid #ccc; font-weight: bold; color: #333; line-height: 1.3;
}
""" % {"W": CARD_W, "H": CARD_H, "VERDE": VERDE_SENA}


def carnet_html(rol, cfg):
    extra = ""
    if cfg["extra"]:
        extra = f'''
        <div class="carnet-small-text">
            Ficha de Formaci&oacute;n No. {{C&oacute;digo}}<br>
            Fecha de Finalizaci&oacute;n: {{Fecha Final}}<br>
            <strong>{{Nombre del Programa}}</strong>
        </div>
        <div class="carnet-small-text" style="margin-top:12px;">
            {ASEGURADORA["nombre"]}<br>
            {ASEGURADORA["telefono"]}<br>
            {ASEGURADORA["poliza"]}
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>Carnet {rol}</title><style>{CSS}</style></head>
<body>
<div class="carnet">
    <div class="carnet-header">
        {sena_logo_svg()}
        <div class="carnet-photo">{foto_placeholder_svg()}</div>
    </div>
    <div class="carnet-body">
        <div class="carnet-role">{rol}</div>
        <div class="carnet-name">{{Nombres}}</div>
        <div class="carnet-surname">{{Apellidos}}</div>
        <div class="info-line"><span class="label">{cfg["doc_label"]}</span> {cfg["documento"]}</div>
        <div class="info-line"><span class="label">RH</span> {{Tipo de Sangre}}</div>
        {jornada_html(JORNADA_MARCADA.get(rol, ""))}
        {extra}
        <div class="carnet-barcode">{barcode_svg(seed=rol)}</div>
    </div>
    <div class="carnet-footer">
        <div>{GENERALIDADES["regional"]}</div>
        <div>{GENERALIDADES["centro_1"]}</div>
        <div>{GENERALIDADES["centro_2"]}</div>
    </div>
</div>
</body>
</html>'''


# ----------------------------------------------------------------
# Render a PNG con navegador headless (300 DPI)
# ----------------------------------------------------------------

def find_browser():
    candidatos = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for ruta in candidatos:
        if Path(ruta).exists():
            return ruta
    return shutil.which("chrome") or shutil.which("msedge")


def render_png(browser, html_path, png_path):
    cmd = [
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--window-size={CARD_W},{CARD_H}",
        f"--screenshot={png_path}",
        html_path.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not png_path.exists():
        # Fallback al headless clasico
        cmd[1] = "--headless"
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return png_path.exists()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    if not browser:
        sys.exit("No se encontro Chrome ni Edge para renderizar los PNG.")

    print(f"Navegador: {browser}")
    print(f"Salida:    {OUT_DIR}\n")

    ok = True
    for rol, cfg in ROLES.items():
        nombre = f"carnet_{rol.lower()}"
        html_path = OUT_DIR / f"{nombre}.html"
        png_path = OUT_DIR / f"{nombre}.png"
        html_path.write_text(carnet_html(rol, cfg), encoding="utf-8")
        if render_png(browser, html_path, png_path):
            print(f"  OK  {png_path.name}  ({CARD_W}x{CARD_H} px @ 300 DPI)")
        else:
            ok = False
            print(f"  ERROR generando {png_path.name}")

    print("\nListo." if ok else "\nHubo errores.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
