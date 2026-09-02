# Manual por Rol — Instructor

Para usuarios con **cargo Instructor** (normalmente rol Usuario). "Instructor"
es un cargo, no un rol del sistema.

## Lo primero: cómo funciona la asistencia

La lista de **"Mi Ficha"** muestra **solo a los aprendices de la ficha que
registraron entrada en portería ese mismo día**. No es la lista de matrícula:
quien no pasó por portería no aparece. No hay fecha retroactiva, ni
observaciones, ni exportación a Excel/PDF. Detalle completo:
`manual_sistema_asistencia.md`.

## Qué puede hacer

- **Mi Ficha:** pasar asistencia del día (presentes/ausentes) por número de
  ficha.
- **Historial de Ingresos:** consultar el ausentismo real de su ficha por
  rango de fechas — días asistidos/faltados, porcentaje, permanencia — de una
  persona o de la ficha completa → `manual_historial_ingresos.md`. Esta es la
  herramienta para seguimiento de asistencia a lo largo del tiempo (dentro
  del mes en curso; los meses anteriores quedan en los respaldos que
  administra el rol Admin).
- **Mi Perfil / carnet digital:** igual que cualquier usuario; su carnet
  imprime el perfil INSTRUCTOR con su área (`manual_gestion_perfil.md`).
  Su campo "Programa/Área" es texto libre (no elige ficha).
- **Mis equipos:** registrar hasta 5 equipos propios
  (`manual_gestion_equipos.md`).
- **Mensajes, Centro de Ayuda, Tutorial** (`manual_mensajes_y_ayuda.md`).
- Ver la **foto** de los aprendices en el historial y la asistencia (parte de
  sus funciones).

## Qué NO puede hacer

- Operar portería (escáner, pases, panel), gestionar usuarios o fichas,
  aprobar fotos, ver auditoría o respaldos. Ver `matriz_permisos.md`.
- Ver el "Historial Clases" (las asistencias guardadas las consulta el rol
  Admin); usted ve el resultado de lo que guarda en el momento de guardarlo.

## Preguntas frecuentes

**Un aprendiz presente no sale en la lista.** No registró entrada hoy en
portería, o su perfil tiene mal la ficha. Sin entrada registrada no hay forma
de marcarlo.

**¿Cómo saco el consolidado del mes para un reporte?** Use "Historial de
Ingresos" con el rango del mes (o su API JSON). La asistencia de clase
guardada se consolida en el respaldo mensual, que puede pedirle al
administrador.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
