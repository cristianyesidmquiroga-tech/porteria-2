# Manuales de Usuario — Sistema de Gestión de Acceso SENA

Sistema de control de acceso del Centro de Gestión Agroempresarial del
Oriente (SENA). Permite el control de entradas y salidas mediante **carnet
digital con código de barras**, el registro de visitantes, vehículos y
objetos, el registro de equipos personales y el control de asistencia.

Todos los manuales de esta carpeta están verificados contra el código del
repositorio (última revisión: septiembre de 2026). Si un manual y el sistema
se contradicen, repórtelo: el manual se corrige contra el código, nunca al
revés.

## Empezar por aquí

- **`matriz_permisos.md`** — qué puede hacer cada combinación de rol y cargo.
  Los **roles** del sistema son **Admin, Usuario y Trabajador**; "Celador",
  "Instructor", "Aprendiz", "Administrativo" y "Administrador" son
  **cargos**. Casi todas las dudas de "por qué no veo tal menú" se responden
  ahí.
- Para operación y despliegue (respaldos, tareas automáticas, correo,
  variables): **`../DESPLIEGUE_Y_OPERACION.md`**.

## Manuales por módulo

| Manual | Contenido | Para quién |
|---|---|---|
| `manual_registro_cuenta.md` | Registro público, verificación de correo, inicio de sesión, recuperación de contraseña | Todos |
| `manual_gestion_perfil.md` | Perfil, foto (validación + aprobación), carnet digital y código de barras | Todos |
| `manual_gestion_equipos.md` | Registro de equipos propios (máx. 5) | Usuarios (salvo celadores y rol Trabajador) |
| `manual_mensajes_y_ayuda.md` | Mensajería con asesores, centro de ayuda, tutorial | Todos / asesores |
| `manual_historial_ingresos.md` | Historial de entradas/salidas y ausentismo, con rango de fechas | Todos (propio); portería e instructores (terceros) |
| `manual_control_acceso.md` | Escáner, movimientos, pases manuales, incidentes, panel | Quien opera portería |
| `manual_sistema_asistencia.md` | Asistencia por ficha (solo quienes entraron ese día) | Instructores y Admin |
| `manual_gestion_usuarios.md` | Usuarios: crear, editar, eliminar, importar Excel; auditoría y respaldos | Solo rol Admin |
| `manual_gestion_fichas.md` | Fichas de formación (programa y fecha heredados) | Solo rol Admin |
| `manual_revision_fotos.md` | Cola de aprobación de fotos | Solo rol Admin |

## Manuales por rol/cargo

| Manual | Cubre |
|---|---|
| `manual_rol_administrador.md` | Rol **Admin** (todo el sistema) |
| `manual_rol_celador.md` | Cargo **Celador** (portería) |
| `manual_rol_instructor.md` | Cargo **Instructor** (asistencia) |
| `manual_rol_aprendiz.md` | Cargo **Aprendiz** |
| `manual_rol_administrativo.md` | Cargo **Administrativo** (asesor) |
| `manual_rol_usuario_estandar.md` | Rol Usuario sin cargo especial y rol **Trabajador** |

## Hechos del sistema que todos los manuales respetan

- El carnet usa **código de barras (Code128)** derivado del documento. No
  existen códigos QR, ni botones de "Imprimir QR"/"Descargar QR", ni
  regeneración de códigos. El único botón del carnet es **"Descargar carnet"**.
- **No existen "pases temporales"** con vigencia, revocación ni extensión:
  se registran visitantes, vehículos y objetos, y el cierre automático de
  medianoche los desactiva.
- El carnet se activa solo con la **foto aprobada por un administrador**,
  además del documento, el tipo de sangre y (aprendices) la ficha.
- La lista de asistencia contiene **solo a quienes registraron entrada en
  portería ese mismo día**; no hay fechas retroactivas ni observaciones.
- **No hay** exportación de asistencia a Excel/PDF, edición de equipos,
  pantalla de puntos de acceso, restauración de respaldos ni filtros de fecha
  en el panel de portería (las consultas por fechas viven en "Historial de
  Ingresos").
- El día 1 de cada mes los accesos y asistencias del mes anterior **se
  exportan a Excel y se borran de la base**; no hay forma de restaurarlos.

## Requisitos

- Navegador actualizado (Chrome, Firefox, Edge o Safari) con conexión a
  internet.
- Para el escáner de portería: dispositivo con cámara (el lector funciona
  desde el navegador) o, en su defecto, la búsqueda manual por documento.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
