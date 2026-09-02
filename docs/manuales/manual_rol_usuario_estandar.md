# Manual por Rol — Usuario estándar y rol Trabajador

Para cuentas sin funciones especiales: **rol Usuario** con un cargo que no
otorga permisos extra, y cuentas con **rol Trabajador**.

## Rol Usuario (estándar)

Puede:

- Completar su perfil y obtener el **carnet digital con código de barras**
  (documento + tipo de sangre + foto aprobada) → `manual_gestion_perfil.md`.
- Registrar hasta **5 equipos** propios → `manual_gestion_equipos.md`
  (excepto si su cargo es Celador).
- Consultar **sus propios ingresos** ("Mis Ingresos") →
  `manual_historial_ingresos.md`.
- Usar **Mensajes**, el **Centro de Ayuda** y el **Tutorial** →
  `manual_mensajes_y_ayuda.md`.

No puede gestionar a otras personas ni ver información ajena. Si su cargo es
Aprendiz, Instructor, Administrativo, Celador o Administrador, use el manual
de ese cargo: el cargo añade (o quita) funciones — ver `matriz_permisos.md`.

## Rol Trabajador

El rol Trabajador es un rol de acceso básico que se puede asignar en la
importación masiva. Sus diferencias con el rol Usuario, según el código:

- **No puede registrar equipos propios** (esa función exige rol Usuario o
  Admin).
- No opera portería ni asesora, aunque su cargo sea Celador, Administrador o
  Administrativo (esos permisos exigen rol Usuario).
- **Sí** puede pasar asistencia si su cargo es Instructor (ese permiso mira
  solo el cargo).
- Todo lo demás (perfil, carnet, foto, mensajes, su historial) funciona
  igual que para el rol Usuario. En el panel de portería, sus ingresos se
  cuentan en la categoría "Trabajadores".

## Reglas comunes de la cuenta

- Sesión **única** (entrar en otro dispositivo cierra la anterior) y cierre a
  los **10 minutos** de inactividad.
- 5 intentos fallidos de contraseña = bloqueo de **10 minutos**.
- Contraseña: mínimo 8 caracteres, letras y números.
- Recuperación de contraseña autoservicio desde la pantalla de ingreso →
  `manual_registro_cuenta.md`.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
