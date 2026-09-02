# Despliegue y operación — Sistema de Gestión de Acceso SENA

Documento para quien despliega, opera o hereda este sistema. Todo lo que
aparece aquí está verificado contra el código del repositorio (los archivos
citados son la fuente de verdad si algo cambia).

> **LO PRIMERO QUE HAY QUE SABER:** el respaldo mensual automático
> **BORRA de la base de datos** los accesos y asistencias del mes anterior
> después de exportarlos a un archivo Excel, y **no existe ninguna función
> para restaurarlos**. Ver la sección [Respaldo mensual](#respaldo-mensual-exporta-y-borra).

---

## 1. Qué es y cómo corre

- Aplicación Flask (`run.py` → `app/create_app()`), servida por **gunicorn**
  dentro de un contenedor Docker (`docker/Dockerfile`, `docker/entrypoint.sh`).
- Base de datos **PostgreSQL externa**, conectada por `DATABASE_URL`. El
  `docker-compose.yml` define **un solo servicio** (`web`); no levanta base de
  datos ni ningún servicio de respaldo.
- Zona horaria fija: `America/Bogota` (variable `TZ` en la imagen y
  `SCHEDULER_TIMEZONE` en `config/config.py`). Todas las fechas se guardan en
  hora de Colombia **sin** información de zona (`app/utils/get_colombia_time`).

### Un solo proceso, a propósito

`docker/entrypoint.sh` arranca gunicorn con `--workers 1` escrito a mano.
**No es un descuido y no debe "corregirse":** el planificador de tareas
(APScheduler) vive dentro del proceso web. Con dos workers habría dos
planificadores idénticos:

- el cierre nocturno registraría **salidas duplicadas**, y
- el respaldo mensual escribiría el mismo `.xlsx` desde dos procesos a la vez
  **antes de borrar las filas de la base**, con riesgo de borrar datos sobre
  un archivo corrupto.

La concurrencia sale de los hilos (`GUNICORN_THREADS`, por defecto 8 en el
entrypoint). Si algún día hacen falta varios procesos, primero hay que separar
el planificador a su propio contenedor con `EJECUTAR_TAREAS=false` en los
procesos web, y mover el limitador de peticiones y el registro de desafíos
anti-bot a Redis (`RATELIMIT_STORAGE_URI`), porque hoy ambos viven en memoria
del proceso.

### Qué pasa en cada arranque del contenedor

1. `scripts/create_admin.py` se ejecuta **en cada despliegue**:
   - crea los roles `Admin` y `Usuario` si faltan,
   - crea el punto de acceso 1 ("Portería Principal") si falta,
   - crea el superadministrador con `ADMIN_EMAIL` / `ADMIN_PASSWORD`
     **solo si no existe** (nunca resetea la contraseña de un admin existente;
     `ADMIN_PASSWORD` exige mínimo 12 caracteres).
   - El sistema **no arranca** si falta `ADMIN_EMAIL`, `SECRET_KEY` o
     `DATABASE_URL`.
2. Arranca gunicorn. `create_app()` ejecuta `db.create_all()` y una migración
   ligera de columnas (`COLUMNAS_PENDIENTES` en `app/__init__.py`) que añade
   las columnas nuevas a bases creadas por versiones anteriores.
3. Se registran las dos tareas programadas (ver abajo).

---

## 2. Variables de entorno

La referencia completa y comentada es **`config/.env.example`** — está al día
y documenta cada variable. El archivo real es `config/.env` y **nunca se
commitea**. Resumen:

| Grupo | Variables | Obligatoria |
|---|---|---|
| Núcleo | `SECRET_KEY`, `DATABASE_URL` | **Sí** (sin ellas no arranca) |
| Superadmin | `ADMIN_EMAIL` (sí), `ADMIN_PASSWORD` (solo la primera vez), `ADMIN_DOCUMENTO` | `ADMIN_EMAIL` sí |
| Correo | `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`, `MAIL_NOMBRE_REMITENTE`, `MAIL_CIFRADO`, `MAIL_MODO`, `MAIL_RESPALDO_RELE`, `MAIL_PAUSA_SEGUNDOS` | Sin correo no llegan códigos de verificación ni recuperación |
| Registro | `DOMINIOS_REGISTRO` (dominios permitidos, recomendado) | No |
| Cookies/HTTPS | `COOKIES_SEGURAS` (`false` solo en desarrollo sin HTTPS) | No |
| Límites | `PROXIES_CONFIABLES`, `RATELIMIT_STORAGE_URI`, `LIMITE_PETICIONES`, `LIMITE_GENERAL` | No |
| Anti-bot | `CAPTCHA_ACTIVO`, `CAPTCHA_DIFICULTAD` | No |
| Tareas | `EJECUTAR_TAREAS`, `ZONA_HORARIA` | No |
| Carnet | `CARNET_ENTIDAD`, `CARNET_ENTIDAD_LARGA`, `CARNET_REGIONAL`, `CARNET_CENTRO`, `CARNET_MUNICIPIO`, `CARNET_ASEGURADORA`, `CARNET_ASEGURADORA_TEL`, `CARNET_POLIZA`, `CARNET_PERFILES` | No (por defecto, los del centro de Vélez) |
| Servidor | `GUNICORN_THREADS` | No |
| Desarrollo | `RECARGAR_PLANTILLAS`, `CARPETA_FOTOS` (config, ver §4) | No |

Notas de seguridad ya incorporadas en el código:

- `PROXIES_CONFIABLES` debe valer **exactamente** el número de proxies propios
  delante de la aplicación (1 detrás de Coolify/Traefik, 0 en local). Un valor
  mayor que el real permite falsear la IP con `X-Forwarded-For`.
- Los secretos de producción viven solo en la plataforma de despliegue, nunca
  en el repositorio. Si un secreto se filtra, se **rota**, no solo se borra.

---

## 3. Tareas programadas (APScheduler)

Ambas se registran en `_registrar_tareas()` (`app/__init__.py`) y corren en
zona `America/Bogota`. Se desactivan por proceso con `EJECUTAR_TAREAS=false`.

### Cierre nocturno (todos los días, 00:00:05)

`auto_exit_all()` en `app/utils/tareas.py`. En una sola transacción:

- Finaliza todos los **turnos de celador** activos.
- Desactiva todos los **visitantes, vehículos** (campo `activo=False`) y pone
  todos los **equipos** en estado `Afuera`.
- Para toda persona o entidad cuyo último movimiento fue `Entrada`, inserta
  una **Salida automática fechada a las 23:59:59 del día anterior**.
- Deja constancia en la tabla de auditoría (usuario "SISTEMA").

Consecuencias operativas:

- La lista de "quién está adentro" empieza vacía cada día.
- En el historial de ingresos, una salida a las 23:59:59 en punto es un cierre
  automático, no una salida real (la vista de historial las marca aparte).
- Los pases de visitantes/vehículos **no tienen fecha de vencimiento propia**:
  su "vigencia" real es hasta la medianoche, cuando el cierre los desactiva.

### Respaldo mensual (día 1 de cada mes, 00:00:10) — EXPORTA Y BORRA

`ejecutar_respaldo_mensual()` en `app/utils/respaldos.py`:

1. Toma **todos los accesos y todas las asistencias del mes anterior**.
2. Los exporta a `app/respaldos_mensuales/Respaldo_Sistema_AAAA-MM.xlsx`
   (3 hojas: accesos de usuarios, accesos de visitantes/vehículos/objetos,
   asistencias de clase).
3. **Verifica** que el archivo quedó bien escrito y se puede reabrir.
4. Solo si la verificación pasa, **BORRA esas filas de la base de datos** y
   confirma la transacción.

**No existe ninguna función de restauración.** Una vez borradas, las filas
solo existen en el `.xlsx`. Por eso:

- El volumen `app/respaldos_mensuales:/app/app/respaldos_mensuales` del
  `docker-compose.yml` **no es opcional**: sin él, el archivo se escribe en el
  disco efímero del contenedor y el siguiente redespliegue lo pierde — junto
  con los datos ya borrados de la base.
- Los archivos se descargan desde el panel (Admin → "Respaldos del Sistema")
  y conviene **copiarlos periódicamente fuera del servidor**.
- Si el respaldo falla (disco lleno, archivo corrupto), **no se borra nada**:
  se anota en auditoría y se avisa por correo a `ADMIN_EMAIL`. Si
  `ADMIN_EMAIL` no está configurado, el aviso solo queda en el log.
- El panel avisa al administrador 15 días y 3 días antes del día 1.

Qué **no** borra el respaldo: usuarios, equipos, fichas, mensajes, auditoría,
turnos de celador. Solo accesos y asistencias del mes anterior.

---

## 4. Directorios y datos en el servidor

| Ruta (dentro del contenedor) | Contenido | Persistencia |
|---|---|---|
| `/app/app/respaldos_mensuales/` | Respaldos mensuales `.xlsx` (los únicos datos ya borrados de la base) | **Volumen obligatorio** (montado en compose) |
| `/app/instance/fotos_perfil/` | Fotos de perfil (fuera de `static/` a propósito: se sirven solo con sesión y permiso) | **ATENCIÓN: no está en un volumen en el compose actual.** Ver nota |
| `/app/app/static/uploads/` | Ubicación antigua de fotos; al arrancar, las que queden ahí se migran a `instance/fotos_perfil` | Volumen montado (legado) |
| Base de datos | Todo lo demás | En el PostgreSQL externo |

**Nota sobre las fotos:** el código guarda las fotos en
`instance/fotos_perfil/` (o en la ruta que indique la clave de configuración
`CARPETA_FOTOS`), pero el `docker-compose.yml` solo monta el volumen del
directorio antiguo `app/static/uploads`. En un redespliegue, las fotos que
estén únicamente en `instance/` dentro del contenedor **se pierden** y cada
persona tendría que volver a subir la suya (y pasar de nuevo por revisión).
Al operar este sistema hay que montar también `instance/` como volumen, o
apuntar `CARPETA_FOTOS` a una ruta persistida.

---

## 5. Comprobación de salud

- `GET /salud` responde `{"estado": "ok"}` **sin autenticación** y está exento
  del límite de peticiones. Es lo que usa el `healthcheck` del compose
  (cada 60 s, con `curl` dentro del contenedor) y lo que debe usar cualquier
  monitor externo.
- Un monitor externo solo confirma que la web responde. Para detectar que el
  **planificador** murió en silencio, la señal es el respaldo mensual: si el
  día 1 no aparece archivo nuevo en "Respaldos del Sistema" (habiendo datos
  del mes anterior) o no llega el correo de fallo, hay que revisar los logs.

---

## 6. Correo

Configuración completa en `config/.env.example`; implementación en
`app/utils/email.py`. Lo esencial:

- El sistema **depende** del correo para: código de verificación de registro,
  recuperación de contraseña, credenciales temporales de cuentas creadas por
  el admin o importadas, resultado de la revisión de foto y aviso de fallo del
  respaldo mensual. Sin SMTP configurado, nadie puede activar una cuenta nueva.
- Modo por defecto `MAIL_MODO=rele`: se entrega a través de un servidor SMTP
  (con Gmail hace falta **contraseña de aplicación**, no la normal). El
  cifrado se deduce del puerto (465 = SSL, 587 = STARTTLS, 25 = ninguno) y se
  puede forzar con `MAIL_CIFRADO`.
- Modo `directo` (la aplicación entrega al servidor del destinatario): casi
  nunca funciona desde un VPS — puerto 25 de salida bloqueado, IP sin
  reputación, sin SPF/DKIM. Antes de activarlo:
  `python scripts/probar_correo.py --puerto-25`.
- Los envíos salen por una **cola con un solo hilo**, con pausa entre correos
  (`MAIL_PAUSA_SEGUNDOS`) y reintentos solo para fallos pasajeros. Probar la
  configuración sin enviar nada: `python scripts/probar_correo.py`.

---

## 7. Desarrollo local y pruebas

```bash
# Entorno virtual del repo: .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt -r requirements-dev.txt

cp config/.env.example config/.env   # y rellenar valores
python scripts/create_admin.py
python run.py
```

- Pruebas: `python -m pytest tests/` (usan SQLite en memoria vía
  `tests/conftest.py`; no tocan la base real).
- En local sin HTTPS: `COOKIES_SEGURAS=false` y `PROXIES_CONFIABLES=0`.
- Scripts útiles en `scripts/`: `probar_correo.py` (SMTP),
  `limpiar_fotos_huerfanas.py` (fotos sin usuario), `generar_pdfs_*.py`
  (convierten estos manuales a PDF).

---

## 8. Qué revisar antes de un despliegue

1. Copia reciente de los `.xlsx` de `app/respaldos_mensuales/` fuera del
   servidor (y respaldo propio de PostgreSQL con `pg_dump`: el respaldo
   mensual del sistema **no** respalda usuarios ni el resto de tablas).
2. Que el commit anterior funcional esté identificado para poder revertir.
3. **Evitar desplegar cerca de la medianoche del día 1 del mes**: un reinicio
   en ese momento puede interrumpir el respaldo (si se interrumpe antes de
   verificar, no borra nada, pero el respaldo queda pendiente hasta que el
   planificador lo reintente dentro de su margen de una hora — `misfire_grace_time=3600`).
4. Que las variables nuevas que exija el código estén cargadas en la
   plataforma de despliegue (el sistema falla explícito si falta una
   obligatoria).
