# Manual de Usuario — Historial de Ingresos

Consulta de entradas y salidas por persona o por grupo, con resumen de
asistencia. Menú lateral → **"Historial de Ingresos"** (para usuarios sin
permisos ampliados aparece como **"Mis Ingresos"**).

## Quién ve qué

- **Todo el mundo** puede consultar **su propio** historial.
- Quien **opera portería** (Admin, Usuario+Celador, Usuario+Administrador) o
  **gestiona asistencia** (Admin, cargo Instructor) puede además consultar a
  **otras personas**: por persona concreta, por **ficha completa**, por
  **cargo** o por búsqueda de nombre/documento.
- Si alguien sin permiso intenta pedir el historial de otro, el sistema lo
  rechaza (no filtra en silencio).

## Filtros

- **Rango de fechas** (esta sí es la pantalla con filtro por fechas; por
  defecto, los últimos 30 días).
- Persona(s), ficha, cargo o texto de búsqueda (nombre o documento).
- **"Solo días hábiles"**: por defecto las faltas se cuentan solo de lunes a
  viernes; se puede desactivar.
- Topes para proteger el servidor: máximo 300 personas por consulta y 500
  movimientos listados por persona (los resúmenes sí se calculan sobre todo
  el periodo).

## Qué muestra

Por cada persona:

- **Movimientos emparejados** Entrada → Salida con fecha, horas, permanencia
  en minutos y **equipos** que llevaba. Una salida a las **23:59:59** está
  marcada como **cierre automático** (la registró el sistema a medianoche, no
  el celador: la hora real de salida de esa persona no se conoce).
- **Resumen del periodo:** días asistidos, días faltados (sobre los días
  esperados del rango), porcentaje de asistencia, día de la semana con más
  faltas, promedio de permanencia y cuántas entradas quedaron sin salida.

Casos que el sistema soporta y muestra tal cual: entrada sin salida (la
persona sigue adentro o no registró salida), y salida cuya entrada quedó
fuera del rango consultado.

## API JSON

La misma consulta existe en `/api/historial-persona` (mismos filtros por
querystring, mismos permisos, sesión requerida). Devuelve resumen y
movimientos por persona. Es la que puede usarse para llevar los datos a una
hoja de cálculo; **no hay botón de exportar** en la pantalla.

## Límite temporal de los datos

El historial de accesos del mes anterior **se exporta y se borra de la base
el día 1 de cada mes** (respaldo mensual). En esta pantalla solo se puede
consultar lo que aún está en la base: el mes en curso. Lo anterior está en
los archivos `Respaldo_Sistema_AAAA-MM.xlsx` que administra el rol Admin.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
