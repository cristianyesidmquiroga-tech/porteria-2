# Manual de Usuario — Control de Acceso (Portería)

Para quien opera la portería: rol Admin, o rol Usuario con cargo **Celador**
o **Administrador**. Cubre el escáner, el registro de movimientos, los pases
manuales y el panel general.

## Índice
1. [Ideas clave](#ideas-clave)
2. [Escáner](#escáner)
3. [Registrar entradas y salidas](#registrar-entradas-y-salidas)
4. [Pases manuales: visitantes, vehículos y objetos](#pases-manuales-visitantes-vehículos-y-objetos)
5. [Incidentes](#incidentes)
6. [Panel General (dashboard)](#panel-general-dashboard)
7. [Turnos de celador y cierre de medianoche](#turnos-de-celador-y-cierre-de-medianoche)
8. [Preguntas frecuentes](#preguntas-frecuentes)

---

## Ideas clave

- El carnet digital lleva un **código de barras** generado a partir del
  documento. No hay códigos QR ni pases con fecha de vencimiento.
- El "estado" de una persona o entidad (Adentro/Afuera) es simplemente su
  **último movimiento registrado**. El sistema impide registrar dos entradas
  seguidas o una salida sin entrada.
- **La foto es la verificación de identidad.** El escáner indica si la foto
  fue aprobada por un administrador; una foto sin aprobar no sirve para
  confirmar quién está en la puerta.

---

## Escáner

Menú lateral → **"Escáner"**.

1. Pulse el botón de encender cámara (puede alternar entre cámaras).
2. Apunte al **código de barras** del carnet digital (en pantalla o
   descargado). El lector también acepta los códigos de los pases manuales.
3. Si la cámara falla, use **"¿Cámara con problemas? Usar búsqueda manual"**
   y teclee el **número de documento** (o la placa/serial para pases).

Al identificar a una persona, el sistema muestra: nombre, documento, cargo,
rol, foto (con la marca de si está **aprobada**), estado actual
(Adentro/Afuera) y sus equipos registrados con el estado de cada uno.

Para un visitante que está adentro, muestra además el **tiempo transcurrido**
desde su entrada y lo resalta si supera **2 horas**.

---

## Registrar entradas y salidas

1. Identifique a la persona (escáner o búsqueda manual).
2. Si trae equipos, **marque cuáles**: solo aparecen los equipos registrados
   a nombre de esa persona; no se pueden agregar equipos ajenos desde aquí.
3. Pulse **Entrada** o **Salida**.

El sistema guarda fecha y hora, los equipos marcados y **qué operador
registró el movimiento**, y actualiza el estado de los equipos
(Adentro/Afuera).

### Validaciones de flujo

- **Entrada de alguien que ya figura adentro** o **salida de alguien sin
  entrada previa**: el sistema **rechaza** el movimiento y deja constancia en
  la auditoría ("Inconsistencia de Acceso Detectada"). Si la situación es
  real (por ejemplo, ayer no se registró la salida), tenga en cuenta que el
  cierre de medianoche ya debió registrar la salida automática; si aun así
  hay inconsistencia, repórtela como incidente.
- Los registros de acceso **no se pueden editar ni borrar** desde ninguna
  pantalla.

---

## Pases manuales: visitantes, vehículos y objetos

Menú lateral → **"Pases Manuales"**. Tres pestañas: Personas (Visitantes),
Vehículos (Logística) y Objetos Externos.

**No son pases temporales:** no tienen fecha ni hora de validez, no expiran
por sí solos, y no existen "revocar" ni "extender". Son registros de
entidades externas para poder marcarles entradas y salidas. El cierre de
medianoche los desactiva y les registra la salida automática.

### Visitantes
- Datos: **nombre y documento (obligatorios)** y motivo.
- Si el documento ya existe, el registro se **reactiva y actualiza** en vez
  de duplicarse.
- El sistema genera un código interno (`SENA-VISIT:<documento>`) cuyo código
  de barras se puede mostrar/imprimir desde la lista, aunque el celador
  también puede buscarlo tecleando el documento.

### Vehículos
- Datos: **placa (obligatoria)**, tipo (**SENA** o **Externo**), propietario
  y motivo. Placa repetida = se reactiva y actualiza.

### Objetos externos
- Para equipos de terceros (ej. un taladro de un contratista, un portátil de
  un visitante). Datos: **descripción (obligatoria)**, serial (si no se
  escribe, el sistema genera uno), propietario y motivo.
- Los objetos sí se pueden **editar** después y **desactivar** (los
  visitantes y vehículos no tienen edición posterior: se sobrescriben al
  volver a registrarlos).

### Registrar movimientos de pases
Escanee el código del pase o búsquelo manualmente, y registre Entrada o
Salida igual que con una persona. Aplican las mismas validaciones de flujo.

---

## Incidentes

Desde el escáner puede registrar un **incidente** (equipo no registrado,
anomalía, persona sin identificar): escriba el detalle y quedará en el
historial de auditoría con su nombre como quien reporta. Es el mecanismo para
dejar rastro de lo que el flujo normal no cubre.

---

## Panel General (dashboard)

Menú lateral → **"Panel General"**:

- **KPIs:** total de aprendices, instructores y trabajadores registrados, y
  cuántos visitantes, vehículos y objetos están **adentro ahora**.
- **Gráfica** de ingresos de los últimos 7 días por cargo, con un resumen en
  texto.
- **Historial reciente:** los últimos **100 movimientos**, con filtros por
  **cargo** y por **ficha**. **No hay filtro por fechas** en esta pantalla;
  para consultar por rango de fechas use **"Historial de Ingresos"**
  (ver `manual_historial_ingresos.md`).
- **Exportar:** botón de exportación que descarga un **CSV** (se abre en
  Excel) con el historial de accesos de usuarios, aplicando los filtros de
  cargo/ficha activos.

Los administradores y el cargo Administrador ven además **"Reporte
Usuarios"**: analíticas de ingresos de hoy y de los últimos 7 días por
programa/ficha (aprendices), por área (instructores) o por cargo (personal),
con la lista de quiénes están adentro en ese momento.

---

## Turnos de celador y cierre de medianoche

- Al iniciar sesión, a quien tiene cargo **Celador** se le abre un **turno**
  automáticamente (uno por día). El turno se cierra con el cierre automático
  de medianoche.
- **Todos los días a las 00:00** el sistema cierra lo que quedó abierto:
  registra salida (23:59:59) a toda persona/entidad que seguía adentro,
  desactiva visitantes y vehículos, y pone los equipos en "Afuera". Por eso
  cada mañana el conteo de "adentro" empieza en cero.

---

## Preguntas frecuentes

**¿El código no se deja leer?** Suba el brillo de la pantalla, acerque y
aleje el teléfono, o use la búsqueda manual por documento. Funciona igual.

**¿Alguien sin cuenta quiere entrar?** Regístrelo como visitante en "Pases
Manuales" y márquele la entrada.

**¿La persona aparece "Adentro" pero está en la puerta?** Su salida de ayer
no se registró; el cierre de medianoche la habrá corregido hoy a las 00:00.
Si pasa el mismo día, registre el incidente y avise a administración.

**¿Puedo corregir un registro equivocado?** No. Los accesos no se editan.
Registre el movimiento contrario cuando el flujo lo permita y deje incidente
si hace falta explicación.

**¿Dónde veo el historial de una persona concreta o de una ficha?** En
**"Historial de Ingresos"** (`manual_historial_ingresos.md`), que sí permite
rango de fechas, resumen de asistencia y detalle de equipos.

**¿Cuánto historial hay?** El historial de accesos del mes anterior se
exporta a Excel y **se borra de la base el día 1 de cada mes**. Lo anterior
al mes en curso está en los archivos de respaldo (los administra el rol
Admin).

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
