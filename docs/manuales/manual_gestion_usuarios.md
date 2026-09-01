# Manual de Usuario — Gestión de Usuarios (solo rol Admin)

Para administradores del sistema (rol **Admin**). Cubre la pantalla "Gestión
Perfiles": crear, editar, eliminar e importar usuarios, y las pantallas de
auditoría y respaldos.

## Índice
1. [Roles y cargos](#roles-y-cargos)
2. [Crear un usuario](#crear-un-usuario)
3. [Editar un usuario](#editar-un-usuario)
4. [Eliminar un usuario](#eliminar-un-usuario)
5. [Importar usuarios desde Excel](#importar-usuarios-desde-excel)
6. [Historial de Cambios (auditoría)](#historial-de-cambios-auditoría)
7. [Respaldos del Sistema](#respaldos-del-sistema)
8. [Preguntas frecuentes](#preguntas-frecuentes)

---

## Roles y cargos

Al crear o editar un usuario se asignan **dos cosas distintas**:

- **Rol** (nivel de acceso): **Admin**, **Usuario** o **Trabajador**.
  "Celador" e "Instructor" **no son roles**.
- **Cargo** (qué es la persona): Aprendiz, Instructor, Administrativo,
  Celador o Administrador.

Los permisos reales salen de la combinación — la referencia completa está en
`matriz_permisos.md`. Ejemplos: portería la opera rol Usuario con cargo
Celador o Administrador; la asistencia la pasa quien tenga cargo Instructor.

**El cargo gobierna permisos**: cambiárselo a alguien puede darle o quitarle
acceso a portería, asistencia o asesoría.

---

## Crear un usuario

Gestión Perfiles → **"Nuevo Perfil"**.

- Obligatorios: **nombre, correo, contraseña temporal y rol**.
- El **documento** se valida y normaliza igual que en el perfil (tipo +
  número); si es inválido o está repetido, la creación se rechaza con el
  motivo.
- Si la **ficha** escrita ya está registrada en "Fichas de Formación", el
  aprendiz hereda automáticamente su programa y fecha de finalización.
- A las cuentas con rol **Usuario** se les envía un **correo de bienvenida
  con las credenciales temporales**, se les obliga a cambiar la contraseña en
  el primer ingreso y a completar su perfil. Las cuentas de gestión (Admin,
  Trabajador) se crean con el perfil marcado completo y sin ese correo.
- Crear una cuenta con cargo **Celador** abre además su turno.
- Todo queda en la auditoría (con "autorizado por" y "motivo" si se
  diligencian).

## Editar un usuario

- Editables: nombre, correo, tipo y número de documento (validados y con
  chequeo de duplicados), cargo, rol, ficha (con herencia de programa/fecha),
  programa, horario, verificación de correo, desbloqueo de cuenta y
  contraseña.
- **Cambiar rol o contraseña expulsa las sesiones activas** de esa persona.
- Cambiar el cargo recalcula si el perfil sigue estando completo (a un
  aprendiz se le exige ficha).
- Desbloquear: pone a cero los intentos fallidos y levanta el bloqueo de
  login.
- La edición exige registrar **quién autoriza** y **motivo**; queda en la
  auditoría.

## Eliminar un usuario

- **Permanente y sin recuperación.** Borra también sus turnos, sus equipos
  con sus movimientos, su carnet y sus registros de acceso.
- Restricciones: no puede eliminarse a sí mismo, y las cuentas con rol
  **Admin no se pueden eliminar** (solo editar).
- La eliminación queda registrada en la auditoría con autorizador y motivo.
- Si solo quiere impedir el acceso, considere cambiar la contraseña o
  mantener la cuenta bloqueada en lugar de eliminarla.

---

## Importar usuarios desde Excel

Gestión Perfiles → **"Importar Excel"**. El archivo debe ser `.xlsx` con la
primera fila de encabezados. **Los nombres de columna van con mayúscula
inicial, exactamente así:**

| Columna | ¿Obligatoria? | Notas |
|---|---|---|
| `Nombre` | **Sí** | Fila sin nombre o sin correo → se omite |
| `Correo` | **Sí** | Correo ya registrado → la fila se omite |
| `Documento` | No | Se valida; si es inválido o repetido, la persona se importa **sin documento** y queda el aviso |
| `Tipo Documento` | No | CC, TI, CE, PPT o PA; si falta se deduce del número |
| `Cargo` | No | Solo Aprendiz, Instructor, Administrativo, Celador o Administrador; otro valor → se asigna **Aprendiz** con aviso |
| `Rol` | No | Solo `usuario` o `trabajador`. **`Admin` nunca se asigna por importación**; otro valor → Usuario con aviso |
| `Ficha` | No | Si la ficha existe en el sistema, hereda programa y fecha |
| `Programa`, `Horario` | No | Texto |
| `Contraseña` | No | Si falta, se genera una **aleatoria distinta por fila** |

**Solo `Nombre` y `Correo` son obligatorias.** Cualquier manual o plantilla
que exija documento, contraseña, cargo o rol como obligatorios está
desactualizado.

Comportamiento:

- Cada persona importada recibe el **correo de bienvenida** con sus
  credenciales temporales y debe cambiar la contraseña al entrar.
- Una fila con error **no tumba el lote**: se anota el aviso y se sigue.
- Al final se muestra el resumen (creados, omitidos y avisos fila por fila) y
  la importación completa queda en la auditoría.
- Los documentos se leen como **texto**: no importa si Excel los muestra con
  formato numérico.

---

## Historial de Cambios (auditoría)

Menú → **"Historial de Cambios"**. Lista todos los eventos de auditoría, del
más reciente al más antiguo: creación/edición/eliminación de usuarios,
importaciones, revisiones de foto, inconsistencias de acceso, incidentes de
portería, cierres nocturnos y resultado de los respaldos mensuales. Cada
evento registra quién lo hizo, cuándo, el autorizador y el motivo si se
diligenciaron. Es de **solo lectura**: no hay filtros por fecha ni
exportación en esta pantalla.

## Respaldos del Sistema

Menú → **"Respaldos del Sistema"**. Lista los archivos
`Respaldo_Sistema_AAAA-MM.xlsx` generados el día 1 de cada mes y permite
**descargarlos**.

> **Importante:** ese archivo es la **única copia** de los accesos y
> asistencias del mes que exporta, porque el proceso **los borra de la base
> de datos** después de verificar el archivo. No existe función de
> restauración. Descargue y guarde copias fuera del servidor. Detalle
> completo en `docs/DESPLIEGUE_Y_OPERACION.md`.

El panel muestra avisos al administrador 15 y 3 días antes de cada limpieza
mensual.

---

## Preguntas frecuentes

**¿Cómo restablezco la contraseña de alguien?** Edite el usuario y escriba
una contraseña temporal (o pídale que use "¿Olvidaste tu contraseña?"). El
cambio expulsa sus sesiones.

**¿Puedo recuperar un usuario eliminado?** No. Habría que crearlo de nuevo;
su historial borrado no vuelve.

**¿Por qué una fila del Excel quedó sin documento?** El número no pasó la
validación del tipo o ya estaba registrado. Corríjalo editando el usuario.

**¿Puedo dar rol Admin por Excel?** No, nunca. El rol Admin solo se asigna
editando la cuenta una a una desde el panel.

**¿Dónde configuro puntos de acceso?** No existe pantalla para eso: el
sistema usa un único punto ("Portería Principal") creado automáticamente.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
