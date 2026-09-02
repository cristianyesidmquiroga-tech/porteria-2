# Manual de Usuario — Sistema de Asistencia

Para quien pasa asistencia: rol Admin o cualquier usuario con cargo
**Instructor**.

## Lo primero que hay que saber

**La lista de aprendices sale de portería, no de un listado de matrícula.**
Al buscar una ficha, el sistema muestra **únicamente a los aprendices de esa
ficha que registraron ENTRADA en portería ese mismo día**. Quien no pasó por
portería (o cuya entrada no se registró) **no aparece en la lista**, aunque
esté matriculado en la ficha.

Además:

- **Solo funciona para el día en curso.** No hay selector de fecha ni
  registro retroactivo: la asistencia se pasa el mismo día.
- **No hay campo de observaciones** ni justificaciones.
- Puede guardarse **más de un registro el mismo día** (por ejemplo, una
  toma en la mañana y otra en la tarde): cada guardado crea registros nuevos,
  no edita los anteriores.

## Pasar asistencia

1. Menú lateral → **"Mi Ficha"**.
2. Escriba el **número de ficha** y busque.
3. Aparece la lista de aprendices de esa ficha **que entraron hoy**, sin
   duplicados aunque hayan entrado varias veces.
4. Marque con el checkbox a los **presentes** en su clase. Los no marcados
   quedan como ausentes.
5. Pulse **"Guardar Asistencia"**. Queda registrado: aprendiz, ficha,
   presente/ausente, fecha y hora, y usted como instructor.

Si la lista sale vacía: nadie de esa ficha ha registrado entrada hoy, el
número de ficha está mal escrito, o los aprendices tienen la ficha mal
registrada en su perfil.

## Consultar lo guardado

- **Historial Clases** (menú, **solo rol Admin**): busca por número de ficha
  y muestra los últimos 100 registros de asistencia guardados, con
  instructor, aprendiz, presente/ausente y fecha.
- **No existe exportación a Excel ni a PDF de la asistencia.** El único
  archivo con asistencias es el **respaldo mensual** automático
  (`Respaldo_Sistema_AAAA-MM.xlsx`, hoja "Asistencias Clases"), que los
  administradores descargan en "Respaldos del Sistema". Ese proceso además
  **borra de la base** las asistencias del mes exportado, así que los
  registros de meses anteriores solo existen en esos archivos.

## Complemento: Historial de Ingresos

Para el **ausentismo** (días asistidos y faltados de una ficha en un rango de
fechas, con porcentajes y permanencia), use **"Historial de Ingresos"**
(`manual_historial_ingresos.md`): los instructores pueden consultar por ficha
completa. Se basa en los registros de portería, no en la asistencia de clase.

## Preguntas frecuentes

**¿Puedo pasar asistencia de ayer?** No. Solo del día en curso.

**¿Puedo corregir una asistencia guardada?** No hay edición. Puede guardar
una nueva toma el mismo día; ambas quedan registradas.

**Un aprendiz está en clase pero no sale en la lista.** No tiene entrada
registrada hoy en portería (o su perfil tiene otra ficha). Pídale que
regularice su ingreso en portería; sin entrada registrada no aparecerá.

**¿Quién ve lo que guardo?** Los administradores (Historial Clases y el
respaldo mensual). Los aprendices no ven la asistencia de clase en el
sistema.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
