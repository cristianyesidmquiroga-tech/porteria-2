# Estado de la auditoría de seguridad — porteria-2

Documento de continuidad. Registra qué se corrigió, qué queda y qué decisiones
se tomaron, para poder retomar el trabajo sin releer todo el historial.

**Fecha:** 30 de agosto de 2026
**Rama:** `main` · **Remoto:** `origin` → `cristianyesidmquiroga-tech/porteria-2`
**Estado:** todo commiteado en local, historial ya reescrito. **Falta empujarlo
al remoto** (`git push --force origin main`, ver sección 5).
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

## 4. Fotos de perfil e historial de git — COMPLETADO

### 4.0 Decisión final: sin fotos en el repositorio ✅

Se eliminaron **todas** las imágenes rasterizadas del proyecto y se sustituyeron
por avatares vectoriales por cargo. El repositorio ya no contiene ni una sola
fotografía, así que el problema no puede repetirse.

- **Las 24 fotos de perfil se borraron.** Revisando los nombres, casi todas eran
  subidas de prueba (`gojo.webp`, `notion.jpg`, capturas de pantalla, fotos
  publicitarias de portátiles Acer), no rostros reales. Copia en
  `_respaldo_fotos_porteria2/originales/`.
- **`app/static/img/default-profile.png` eliminada**: 281 KB para una silueta
  gris que ahora hace `generico.svg` en 328 bytes.
- **9 avatares SVG nuevos** en `app/static/img/perfiles/`, 13 KB en total:
  `aprendiz`, `instructor`, `celador`, `administrador`, `administrativo`,
  `visitante`, `vehiculo`, `objeto`, `generico`. Un color por cargo para que el
  celador distinga el tipo de un vistazo, todos con contraste WCAG AA.
- **Se eliminó `ui-avatars.com`**, que se usaba en 10 sitios como imagen de
  respaldo. Recibía el **nombre real de cada usuario en la URL**, es decir datos
  personales enviados a un tercero en cada carga de página (Ley 1581). También
  se quitó de la CSP.
- **Resolución centralizada**: `Usuario.ruta_foto` devuelve la foto real si el
  archivo existe en disco, y si no el avatar del cargo. `avatar_de_cargo()` y
  `ruta_foto_o_avatar()` en `app/models/usuarios.py` cubren los casos que no
  pasan por el modelo (historial del panel, respuesta JSON del escáner).
- **`scripts/limpiar_fotos_huerfanas.py`**: pone a `NULL` la columna `foto` de
  los usuarios cuyo archivo ya no existe. No es obligatorio (la app degrada al
  avatar por sí sola), solo deja la base coherente con el disco. Se ejecuta sin
  argumentos para simular, con `--aplicar` para hacer los cambios.
- Verificado en navegador: los 9 avatares renderizan bien a 90 px y a 38 px.

### 4.0.1 Validación facial: de cascadas Haar a YuNet ✅

La foto de perfil se le muestra al celador en el escáner para que confirme la
identidad de quien entra, así que tiene que ser un retrato utilizable. Las
cascadas Haar no daban la talla: sobre imágenes reales aceptaban iconos,
infografías, capturas de pantalla y hasta paisajes sin personas, y a la vez
rechazaban retratos legítimos con gafas.

- **Detector nuevo:** YuNet (`cv2.FaceDetectorYN_create`), umbral de confianza
  0.8. Modelo en `app/static/modelos/face_detection_yunet_2023mar.onnx` —
  **232 KB, licencia MIT** (OpenCV Zoo). Va versionado porque el contenedor de
  producción no tiene internet garantizado en tiempo de ejecución.
- **Por qué YuNet:** es robusto con gafas, ángulos y luz irregular, y da un
  *score* de confianza que las cascadas no dan. Ese score es lo que permite
  cortar dibujos e ilustraciones (puntúan bajo) sin cortar fotos reales.
- **Reglas:** exactamente un rostro, y que ocupe al menos el 2 % del área. Los
  mensajes de error dicen qué hacer ("tómala más cerca, tipo foto de documento",
  "sin nadie más detrás"), porque los lee un aprendiz.
- **Fail-open:** si falta OpenCV o el modelo, deja pasar la foto y lo registra en
  el log. La validación es un apoyo, no un guardián: bloquearla dejaría a la
  gente sin poder completar su perfil.
- **Bug corregido de paso:** `cv2.imread` no abre rutas con acentos en Windows.
  Se lee con `numpy.fromfile` + `cv2.imdecode`.

**Verificado con fotos reales** (autorizadas por el usuario, no versionadas):
un retrato frontal se acepta, y **un retrato con gafas y barba se acepta con
confianza 0.946** — ese era el requisito explícito. También se aceptan las
variantes oscura, clara, desenfocada, girada y reducida, que es como llegan las
fotos tomadas con un móvil.

**Pendiente de verificar:** el rechazo de fotos con más de una persona. Esa
prueba se salta porque no hay una foto de dos personas autorizada.

### 4.1 Optimización de fotos (sigue vigente para las que suban los usuarios) ✅
- `app/utils/imagenes.py`: toda foto que se sube se reescala a 512 px máx., se
  aplana, se le quitan los metadatos EXIF (llevan coordenadas GPS) y se guarda
  como JPEG progresivo de calidad 82. El nombre es fijo (`user_<id>.jpg`), así
  que una foto nueva reemplaza a la anterior en vez de dejarla huérfana en disco.
- `perfil.py` reescrito: escritura atómica a un temporal, de modo que si la
  imagen no es válida o no pasa la validación facial, la foto anterior queda
  intacta. SVG queda excluido a propósito (admite `<script>`).
- **Las 24 fotos existentes se comprimieron: 20,2 MB → 0,63 MB (−97 %).**
  Verificadas una a una: las 24 abren correctamente.
- `loading="lazy"` + `width`/`height` en el listado del panel;
  `fetchpriority="high"` en la tarjeta de verificación, que el celador mira al
  instante mientras alguien espera en la puerta.

### 4.2 Purga del historial de git ✅ (falta solo el push)
- Respaldos en `repositorio/_respaldo_fotos_porteria2/`:
  - `originales/` — las 24 fotos sin comprimir
  - `porteria-2-ANTES-DE-PURGAR.bundle` — el repositorio completo antes de tocarlo
- `git filter-repo` en **dos pasadas**: `app/static/uploads` y también
  `carnet-sena/app/static/uploads`. En los commits antiguos el proyecto vivía
  bajo ese subdirectorio, así que la primera pasada dejó las fotos ahí.
- Resultado: 0 fotos en `refs/heads/main` ni en el stash, `.git` de 9,5 MB →
  738 KB, los 59 commits intactos, las 24 fotos siguen en disco (ya sin versionar).
- **Falta el `git push --force`**: ver sección 5.

#### Cómo verificar la purga (importante: por rama, no con `--all`)

```bash
git rev-list --objects refs/heads/main | grep uploads/profiles
```

**No usar `--all`.** Recorre también `refs/remotes/origin/main`, que es la copia
local de lo que hay *hoy* en GitHub — y mientras no se haya hecho el push, ese
historial todavía contiene las fotos. Da un falso positivo alarmante. Tras el
push, esa referencia se actualiza sola y los objetos viejos quedan inalcanzables.

#### Cuidado con GitHub Desktop

El repositorio se sincroniza con GitHub Desktop (el stash se llama
`!!GitHub_Desktop<main>` y el reflog muestra `fetch --no-write-fetch-head`).
**Ciérralo antes del `push --force`**: si está abierto cuando cambie el remoto,
detecta la divergencia y puede ofrecer un *pull* que devuelva el historial viejo
al repositorio local, deshaciendo la purga sin aviso.

Después del push, para eliminar también las copias locales de los objetos viejos:

```bash
git gc --prune=now
```

---

## 5. PENDIENTE del lado del usuario (sin esto el deploy falla)

1. **Publicar el historial reescrito.** Reescribe `origin/main`; el punto de
   retorno es `_respaldo_fotos_porteria2/porteria-2-ANTES-DE-PURGAR.bundle`.
   **Cierra GitHub Desktop antes** (ver la advertencia de la sección 4.2):
   ```bash
   git push --force origin main
   git gc --prune=now
   ```
   Si alguien más tiene el repositorio clonado, debe volver a clonarlo: su copia
   conserva el historial viejo, con las fotos dentro.

2. **Limpiar las referencias a fotos borradas en la base de producción.** Las
   fotos ya no existen, así que la columna `foto` de esos usuarios apunta a
   archivos inexistentes. La aplicación lo tolera (muestra el avatar del cargo),
   pero conviene dejarlo coherente:
   ```bash
   python scripts/limpiar_fotos_huerfanas.py            # simula
   python scripts/limpiar_fotos_huerfanas.py --aplicar  # ejecuta
   ```
   Esos usuarios verán el avatar de su cargo y el sistema volverá a pedirles que
   suban una foto. Si en producción hubiera fotos reales que se quieran
   conservar, hay que copiarlas al volumen del host **antes** de correr esto.

3. **Variables en Coolify.** La app se niega a arrancar sin ellas, a propósito:
   - `SECRET_KEY=143a80b738486159c74e6692dcba13f9e974d719c339add6930f54040362910e`
     (la anterior está comprometida por haber estado en el repo)
   - Confirmar que `DATABASE_URL` está configurada.
4. **Directorios del host antes del primer arranque** (el contenedor ya no corre como root):
   ```bash
   mkdir -p app/static/uploads/profiles app/respaldos_mensuales
   chown -R 10001:10001 app/static/uploads app/respaldos_mensuales
   ```
5. **`DOMINIOS_REGISTRO`**: quedó en `sena.edu.co,soy.sena.edu.co`. Si hay
   usuarios con correo personal, vaciarlo o añadir sus dominios.
6. **Confirmar el esquema de `objetos_externos`** contra la base real (`\d objetos_externos`).
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
