# Manual por Rol — Administrador (rol Admin)

El rol **Admin** tiene acceso a todo el sistema. Este manual es el mapa de
sus funciones; el detalle de cada una está en el manual de módulo indicado.

> Nota de vocabulario: "Admin" es un **rol**. Existe también el **cargo**
> "Administrador" (rol Usuario), que opera portería y asesora pero **no**
> accede a la gestión del sistema. Ver `matriz_permisos.md`.

## Sus pantallas y responsabilidades

| Pantalla (menú) | Qué hace ahí | Manual |
|---|---|---|
| Gestión Perfiles | Crear, editar, eliminar e importar usuarios; asignar rol y cargo | `manual_gestion_usuarios.md` |
| Fichas de Formación | Registrar programa y fecha de finalización por ficha (heredan los aprendices) | `manual_gestion_fichas.md` |
| Revisar Fotos | Aprobar/rechazar fotos; sin su aprobación nadie tiene carnet activo | `manual_revision_fotos.md` |
| Bandeja de Mensajes | Responder a las personas bloqueadas o con dudas | `manual_mensajes_y_ayuda.md` |
| Panel General, Escáner, Pases | Todo lo de portería (también puede operarla) | `manual_control_acceso.md` |
| Reporte Usuarios | Analíticas de ingresos por cargo/programa/ficha | `manual_control_acceso.md` |
| Mi Ficha | Pasar asistencia (igual que un instructor) | `manual_sistema_asistencia.md` |
| Historial Clases | Consultar asistencias guardadas por ficha | `manual_sistema_asistencia.md` |
| Historial de Ingresos | Entradas/salidas y ausentismo por persona, ficha o cargo | `manual_historial_ingresos.md` |
| Historial de Cambios | Auditoría de todo lo que se hace en el sistema | `manual_gestion_usuarios.md` |
| Respaldos del Sistema | Descargar los respaldos mensuales | abajo |

## Lo que solo el Admin debe tener presente

1. **El día 1 de cada mes, el sistema exporta a Excel los accesos y
   asistencias del mes anterior y LOS BORRA de la base de datos. No hay
   restauración.** Los archivos quedan en "Respaldos del Sistema":
   descárguelos y guarde copia fuera del servidor. El panel se lo recuerda 15
   y 3 días antes. Detalle: `docs/DESPLIEGUE_Y_OPERACION.md`.
2. **La cola de "Revisar Fotos" bloquea personas.** Mientras una foto espera
   revisión, esa persona no tiene carnet. Revísela a diario.
3. **El cargo gobierna permisos.** Cambiar el cargo de alguien puede darle
   acceso a portería o a la asistencia. La referencia es
   `matriz_permisos.md`.
4. **El rol Admin no se concede por importación de Excel** ni puede
   eliminarse desde el panel. Concédalo solo cuenta a cuenta y con motivo.
5. **Los registros de acceso y la auditoría no se editan.** Las correcciones
   se documentan (incidentes, mensajes), no se reescriben.
6. La configuración del sistema (correo, dominios de registro, textos del
   carnet, límites) **no tiene pantalla**: vive en variables de entorno del
   despliegue (`docs/DESPLIEGUE_Y_OPERACION.md`). No existe pantalla de
   "puntos de acceso" ni de "configuración" dentro de la aplicación.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
