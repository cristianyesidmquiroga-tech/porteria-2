# Matriz de permisos por rol y cargo

Fuente de verdad: propiedades del modelo `Usuario`
(`app/models/usuarios.py`) y comprobaciones de cada ruta. Esta matriz refleja
el código real; si el código cambia, manda el código.

## Rol y cargo NO son lo mismo

- **Rol** (tabla `roles`): define el nivel de acceso al sistema. Existen tres:
  **Admin**, **Usuario** y **Trabajador**.
- **Cargo** (columna `cargo` del usuario): describe qué es la persona en el
  centro. Valores reconocidos: **Aprendiz, Instructor, Administrativo,
  Celador, Administrador** (lista blanca `CARGOS_VALIDOS`).

La mayoría de los permisos dependen de la **combinación** de ambos. "Celador"
e "Instructor" no son roles: son cargos de personas cuyo rol normalmente es
`Usuario`.

## Permisos calculados (los que usa el código)

| Permiso | Quién lo tiene |
|---|---|
| `es_admin` — acceso total | Rol **Admin** |
| `puede_operar_porteria` — panel, escáner, pases, registrar movimientos | Rol Admin; o rol **Usuario** con cargo **Celador/Portería** o cargo **Administrador** |
| `puede_asesorar` — bandeja de mensajes, responder a usuarios, ver perfiles ajenos en ese contexto | Rol Admin; o rol **Usuario** con cargo **Administrador** o **Administrativo** |
| `puede_gestionar_asistencia` — pasar asistencia ("Mi Ficha") | Rol Admin; o **cualquier** usuario con cargo **Instructor** |
| `puede_registrar_equipos` — registrar equipos propios | Rol Admin; o rol **Usuario** con cargo distinto de Celador |
| Consultar historial de ingresos **de terceros** | Quien opera portería o gestiona asistencia |
| Ver la **foto** de otra persona | Admin, quien opera portería, quien asesora, quien gestiona asistencia |

Consecuencias que suelen sorprender:

- El rol **Trabajador** no opera portería, no asesora y **no puede registrar
  equipos** (esos permisos exigen rol Usuario o Admin).
- Un **celador** (rol Usuario + cargo Celador) no puede registrar equipos
  propios.
- Un rol Usuario con cargo **Administrador** opera portería y asesora, pero
  **no** entra a la gestión de usuarios, fichas, revisión de fotos ni
  respaldos: eso exige rol Admin.

## Matriz por pantalla

Combinaciones: A = rol Admin · U+Cel = Usuario/Celador · U+Adm = Usuario/cargo
Administrador · U+Advo = Usuario/Administrativo · U+Ins = Usuario/Instructor ·
U+Apr = Usuario/Aprendiz · T = rol Trabajador.

| Pantalla (menú) | A | U+Cel | U+Adm | U+Advo | U+Ins | U+Apr | T |
|---|---|---|---|---|---|---|---|
| Panel General, Escáner, Pases Manuales | ✔ | ✔ | ✔ | — | — | — | — |
| Reporte Usuarios (analíticas por cargo) | ✔ | —* | ✔ | — | — | — | — |
| Mi Ficha (pasar asistencia) | ✔ | — | — | — | ✔ | — | —** |
| Mi Perfil / carnet digital | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Registrar equipos propios | ✔ | — | ✔ | ✔ | ✔ | ✔ | — |
| Historial de Ingresos (propio) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Historial de Ingresos (de terceros) | ✔ | ✔ | ✔ | — | ✔ | — | — |
| Centro de Ayuda, Mensajes, Tutorial | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Bandeja de Mensajes (responder) | ✔ | — | ✔*** | ✔*** | — | — | — |
| Gestión Perfiles (usuarios) | ✔ | — | — | — | — | — | — |
| Fichas de Formación | ✔ | — | — | — | — | — | — |
| Revisar Fotos | ✔ | — | — | — | — | — | — |
| Historial Clases | ✔ | — | — | — | — | — | — |
| Historial de Cambios (auditoría) | ✔ | — | — | — | — | — | — |
| Respaldos del Sistema | ✔ | — | — | — | — | — | — |

\* El enlace del menú "Reporte Usuarios" se muestra a Admin y cargo
Administrador; la ruta en sí acepta a cualquiera que opere portería.

\*\* Un Trabajador con cargo Instructor **sí** puede pasar asistencia: el
permiso mira el cargo, no el rol.

\*\*\* El enlace "Bandeja de Mensajes" del menú lateral solo se pinta para rol
Admin, pero la ruta `/admin/mensajes` acepta a todo el que `puede_asesorar`
(cargo Administrador o Administrativo con rol Usuario), que puede entrar por
URL directa.

## Reglas transversales

- **Sesión única:** iniciar sesión en un dispositivo cierra la sesión en
  cualquier otro.
- **Caducidad:** 10 minutos de inactividad para usuarios normales; 12 horas
  para quien opera portería.
- **Rol Admin:** no puede eliminarse a sí mismo ni pueden eliminarse cuentas
  Admin desde el panel (solo editarse). El rol Admin **nunca** se asigna por
  importación de Excel.
- Cambiar el rol o la contraseña de alguien desde el panel **expulsa sus
  sesiones activas**.
