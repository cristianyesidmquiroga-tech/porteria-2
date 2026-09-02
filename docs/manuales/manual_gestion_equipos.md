# Manual de Usuario — Gestión de Equipos

Para registrar los dispositivos (portátil, tablet, celular…) con los que se
ingresa al centro. En portería, el celador marca cuáles equipos entran y
salen con usted.

## Quién puede registrar equipos

- Rol Admin, o rol **Usuario** con cualquier cargo **excepto Celador**.
- El rol **Trabajador** y los celadores **no** pueden registrar equipos
  propios (así está definido en el sistema; ver `matriz_permisos.md`).

## Límites y validaciones reales

- Máximo **5 equipos** por persona.
- **Nombre del equipo: obligatorio** (hasta 100 caracteres).
- **Serial: opcional.** Si se escribe, debe ser único en todo el sistema
  (hasta 100 caracteres).
- **Tipo:** Portátil/Computador, Tablet, Celular u Otro. Si no se elige, se
  guarda "Otro".

## Registrar un equipo

1. Menú lateral → **"Mi Perfil"** → botón **"Añadir Equipos"**.
2. Complete nombre (ej.: "Portátil HP negro"), serial si lo tiene (etiqueta
   en la parte inferior del portátil) y tipo.
3. Pulse **"Vincular Equipo"**.

## Ver y eliminar equipos

- El botón **"Mis Equipos"** muestra la lista con nombre, serial y estado
  (Adentro/Afuera según el último movimiento registrado en portería).
- Para eliminar: icono de papelera → confirmar. Solo puede eliminar **sus
  propios** equipos. La eliminación es inmediata; si vuelve a necesitarlo,
  regístrelo de nuevo.
- No existe una función de **editar** un equipo: para corregir nombre o
  serial, elimínelo y regístrelo otra vez.

## Cómo se usan en portería

- Al registrar su entrada o salida, el celador ve sus equipos registrados y
  marca los que trae. Solo se aceptan equipos que estén vinculados a su
  cuenta.
- El estado del equipo (Adentro/Afuera) se actualiza con cada movimiento.
- A medianoche, el cierre automático pone todos los equipos en "Afuera".
- Si llega con un equipo sin registrar, el celador puede dejar constancia
  como **incidente**; registre el equipo desde su perfil antes de volver.

## Preguntas frecuentes

**¿Cuántos equipos puedo tener?** Hasta 5.

**¿El serial es obligatorio?** No. Pero si lo escribe debe ser único; si el
sistema dice que ya existe, verifique que no lo haya registrado antes o que
otra persona no lo tenga vinculado.

**¿Queda historial de los movimientos de mis equipos?** Los movimientos de
entrada/salida quedan en el historial de accesos junto a los suyos (visibles
en "Historial de Ingresos"). Tenga en cuenta que el historial de accesos se
exporta y **se depura de la base cada mes** (ver manual de respaldos en
`DESPLIEGUE_Y_OPERACION.md`).

**¿Puedo registrar un equipo de otra persona?** No. Cada equipo se vincula a
una sola cuenta y usted responde por los suyos.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
