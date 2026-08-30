# Estado de la auditoría de seguridad — porteria-2

Documento de continuidad. Registra qué se corrigió, qué queda y qué decisiones
se tomaron, para poder retomar el trabajo sin releer todo el historial.

**Fecha:** 29 de agosto de 2026
**Rama:** `main` · **Remoto:** `origin` → `cristianyesidmquiroga-tech/porteria-2`
**Estado del árbol:** cambios aplicados y **sin commitear**
**Pruebas:** `.venv/Scripts/python.exe -m pytest tests/ -q` → 51 pasando

---

## 1. Cómo verificar que todo sigue bien

```bash
.venv/Scripts/python.exe -m pytest tests/ -q
```

Prueba de humo manual (arranca la app contra SQLite en memoria y pide cada vista):
está descrita en la sección 6.

---

## 2. Corregido y verificado

### Críticos
| # | Problema | Dónde se arregló |
|---|---|---|
| 1 | `debug=True` en producción (consola de Werkzeug, RCE) | `run.py`, `docker/entrypoint.sh` → gunicorn |
| 2 | `SECRET_KEY` con valor por defecto público en el repo | `config/config.py` — ahora obligatoria, sin fallback |
| 3 | Contraseña de admin por defecto y reseteada en cada deploy | `scripts/create_admin.py` |
| 4 | `DATABASE_URL` caía en silencio a SQLite efímero | `config/config.py` — obligatoria |
| 5 | Fotos de rostros versionadas en git | `.gitignore` (purga de historial: ver sección 4) |
| 6 | Sin aviso de privacidad ni consentimiento (Ley 1581) | `templates/main/politica_privacidad.html`, casilla en `register.html`, validación en `registro.py` |

**Hallazgo extra:** `load_dotenv()` nunca encontraba `config/.env` (buscaba `.env` en
la raíz). Por eso en local **siempre** se usaba el `SECRET_KEY` publicado en el repo.

### Altos
- **Cierre nocturno roto desde siempre**: `timedelta` no importado en `app/utils/tareas.py` → `NameError` cada noche. Reescrito y ahora transaccional.
- **Desfase de 5 horas en todos los reportes**: las fechas se guardan en hora de Colombia y se reinterpretaban como UTC. Corregido en `dashboard.py`, `reportes.py`, `asistencia.py`, `perfil.py`, `login.py`. Helper nuevo: `app/utils/parsear_fecha_bd()`.
- **XSS almacenado en el escáner**: función `esc()` en `templates/porteria/scanner.html`.
- **Recuperación de contraseña sin límite de intentos**: contador propio `intentos_codigo`, `hmac.compare_digest`, códigos con `secrets`.
- **OTPs en `CODIGOS_DESARROLLO.txt` y en los logs**: eliminados.
- **Política de contraseña triple (0/4/6)**: unificada a 8 caracteres con letras y números (`app/utils/security.validar_contrasena`).
- **Cookies sin `Secure`/`SameSite`**: configuradas, caducidad 12 h.
- **La validación facial nunca corría**: faltaba opencv en `requirements.txt`.
- **`/equipos/delete` por GET**: ahora POST con CSRF.
- Cabeceras CSP, HSTS, `X-Frame-Options: DENY`, `Permissions-Policy`.
- Enumeración de usuarios cerrada en login, recuperación y registro.

### Encontrado por los subagentes (incluye fallos que introdujeron las propias correcciones)
- **La CSP inicial dejaba el escáner muerto** (48 manejadores inline, `unpkg.com` sin permitir). Corregida.
- **El endpoint de recuperación reseteaba `intentos_fallidos`**, anulando el bloqueo del login → fuerza bruta ilimitada. Contadores separados.
- **2 workers de gunicorn = 2 planificadores**: el respaldo mensual habría escrito el mismo `.xlsx` desde dos procesos *antes* de borrar los datos. Ahora `--workers 1`.
- **`session_token = None` desactivaba la comprobación** en vez de cerrar sesión: el logout no invalidaba nada. `app/utils/security.py`.
- **El respaldo mensual mezclaba entidades** (faltaba `tipo_referencia == 'Usuario'`): archivaba el acceso de un visitante con la cédula de un aprendiz y lo borraba. `app/utils/respaldos.py`.
- **Movimientos de personas sin validación ni trazabilidad**: ahora detectan incoherencias como ya hacían las entidades, y registran `operador_id`.
- Inyección de fórmulas en el CSV exportado, `showToast` con `innerHTML`, restos de la migración rol→cargo en `verify.html` y `dashboard.py`, validación de documento único al editar, auditoría en el alta de usuarios.

### Encontrado por las pruebas nuevas
- **El registro reventaba con 500** si faltaba el campo `ficha` (`sanitize_html(None).strip()`).
- **`templates/auth/email_recuperacion.html` nunca existió**: toda recuperación de contraseña terminaba en `TemplateNotFound` → 500. Esa función llevaba rota desde siempre. Plantilla creada.

---

## 3. Decisiones tomadas con el usuario

- **Asistencia por ficha (instructor↔ficha):** se deja **como está a propósito**. Los instructores dan clase a grupos distintos en mañana, tarde y noche a lo largo de la semana, así que el instructor escribe la ficha directamente. No es un fallo, es el flujo de trabajo real. Lo que sí queda es la traza: `AsistenciaClase.instructor_id` registra quién pasó cada lista.
- **Fotos de perfil:** deben seguir mostrándose, priorizando velocidad de carga. Por eso se comprimen en vez de eliminarse.
- **Purga del historial de git:** autorizada por el usuario (incluye force-push sobre `origin`).

---

## 4. EN CURSO — retomar aquí

### 4.1 Optimización de fotos de perfil ✅ código hecho, falta comprimir las existentes
- **Hecho:** `app/utils/imagenes.py` nuevo. Toda foto que se sube se reescala a
  512 px máx., se aplana, se le quitan los EXIF (llevan GPS) y se guarda como
  JPEG progresivo de calidad 82. El nombre es fijo (`user_<id>.jpg`), así que
  una foto nueva reemplaza a la anterior en vez de dejarla huérfana.
  `perfil.py` reescrito para usarlo, con escritura atómica a un temporal.
- **Falta:**
  1. Comprimir las 24 fotos que ya existen (21 MB, una de 2 MB) con
     `comprimir_en_sitio()` de ese mismo módulo, conservando nombre y formato
     para no tener que tocar la columna `foto` de la base.
  2. Añadir `loading="lazy"` y `width`/`height` a los `<img>` de perfil en
     `templates/porteria/scanner.html`, `verify.html`, `usuarios/profile.html`
     y `usuarios/gestion.html` (evita el salto de layout y acelera la carga).

### 4.2 Purga del historial de git ⏳ NO EMPEZADA — es lo destructivo, va al final
Orden obligatorio, no saltarse pasos:
1. **Copia de seguridad de las fotos fuera del repo.** Crítico: en producción
   Coolify clona el repo, así que borrarlas del historial las borra del servidor
   si no se restauran antes en el volumen.
2. `git bundle create ../porteria-2-respaldo.bundle --all` — punto de retorno.
3. `pip install git-filter-repo` (no está instalado).
4. `git rm -r --cached app/static/uploads/` y commitear.
5. `git filter-repo --path app/static/uploads --invert-paths --force`.
6. `git remote add origin ...` (filter-repo borra el remoto) y `git push --force`.
7. **Restaurar las fotos en el volumen del servidor** antes del siguiente deploy.

---

## 5. PENDIENTE del lado del usuario (sin esto el deploy falla)

1. **Variables en Coolify.** La app se niega a arrancar sin ellas, a propósito:
   - `SECRET_KEY=143a80b738486159c74e6692dcba13f9e974d719c339add6930f54040362910e`
     (la anterior está comprometida por haber estado en el repo)
   - Confirmar que `DATABASE_URL` está configurada.
2. **Directorios del host antes del primer arranque** (el contenedor ya no corre como root):
   ```bash
   mkdir -p app/static/uploads/profiles app/respaldos_mensuales
   chown -R 10001:10001 app/static/uploads app/respaldos_mensuales
   ```
3. **`DOMINIOS_REGISTRO`**: quedó en `sena.edu.co,soy.sena.edu.co`. Si hay
   usuarios con correo personal, vaciarlo o añadir sus dominios.
4. **Confirmar el esquema de `objetos_externos`** contra la base real (`\d objetos_externos`).
   La migración automática es idempotente, pero conviene verificarlo.

---

## 6. Pendiente técnico, no bloqueante

- **Quitar `'unsafe-inline'` de `script-src`**: requiere migrar los 48
  manejadores inline (`onclick`, `onerror`…) a `addEventListener` en archivos
  externos. Refactorización de frontend aparte. Está comentado en `app/__init__.py`.
- **Auto-hospedar las librerías de CDN** (`unpkg`, `jsdelivr`, `cdnjs`) y el logo
  del SENA, hoy enlazado desde Wikipedia. jsDelivr sirve cualquier paquete npm,
  así que permitirlo en la CSP la hace evadible.
- **Fotos servidas sin autenticación** desde `static/`: para datos biométricos
  correspondería una ruta autenticada fuera de `static/`.
- **Verificación de correo sin límite de reenvíos** (`reenviar_codigo`): permite
  bombardear un buzón y agotar la cuota SMTP.
- **Sin rate limiting por IP** en `/auth/login` y `/auth/recuperar`.
- **N+1 queries** en `porteria/dashboard.py`: una consulta por cada visitante,
  vehículo y objeto, más una por cada uno de los 100 accesos del historial.
- **Sin Alembic**: las migraciones son `ALTER TABLE` idempotentes en
  `app/__init__.py` (`COLUMNAS_PENDIENTES`).
- **Respaldo mensual dentro del contenedor**: ya hay volumen en el compose, pero
  conviene copiarlo fuera del VPS.

---

## 7. Otro tema abierto

**Strix** (`usestrix/strix`) — herramienta open-source de pentesting con agentes
de IA, Apache 2.0, activa. El usuario quiere analizarla y probarla **después** de
cerrar esta auditoría. Recomendación registrada: usarla contra el **código local**
(`strix --target ./porteria-2 --scan-mode quick`), nunca contra la URL de
producción sin autorización escrita del SENA (Ley 1273 de 2009).
