# Manual por Rol — Administrativo

Para el personal de planta con **rol Usuario + cargo Administrativo**.
"Administrativo" es un cargo, no un rol del sistema.

## Qué puede hacer

- **Todo lo de un usuario estándar:** perfil y carnet digital con código de
  barras (`manual_gestion_perfil.md`), hasta 5 equipos propios
  (`manual_gestion_equipos.md`), su propio historial de ingresos, mensajes,
  centro de ayuda y tutorial. Su carnet imprime el perfil FUNCIONARIO.
- **Asesorar:** el cargo Administrativo forma parte de los **asesores** del
  sistema — puede atender la bandeja de mensajes y responder a los usuarios
  (foto rechazada, datos mal registrados, cuentas bloqueadas), y ver las
  fotos de perfil en ese contexto. El enlace "Bandeja de Mensajes" no aparece
  en su menú (solo se pinta para rol Admin), pero puede entrar directamente
  por la URL `/admin/mensajes`. Detalle: `manual_mensajes_y_ayuda.md`.

## Qué NO puede hacer

- Operar portería (escáner, pases, panel): eso corresponde al cargo Celador,
  al cargo Administrador o al rol Admin.
- Aprobar o rechazar fotos (solo rol Admin, en "Revisar Fotos"): como asesor
  puede orientar por mensajes, pero la decisión la toma un Admin.
- Gestionar usuarios o fichas, pasar asistencia, ver auditoría o respaldos.

La referencia completa está en `matriz_permisos.md`.

## Nota sobre el cargo "Administrador"

No confunda **Administrativo** con el cargo **Administrador** (también rol
Usuario): este último además opera portería y ve los reportes de usuarios,
pero tampoco accede a la gestión del sistema (eso es del rol Admin).

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
