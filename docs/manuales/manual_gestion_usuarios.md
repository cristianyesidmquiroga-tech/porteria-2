# Manual de Usuario - Gestión de Usuarios (Administrador)

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Acceso al Módulo de Gestión](#acceso-al-módulo-de-gestión)
3. [Ver Lista de Usuarios](#ver-lista-de-usuarios)
4. [Crear Nuevo Usuario](#crear-nuevo-usuario)
5. [Editar Usuario Existente](#editar-usuario-existente)
6. [Eliminar Usuario](#eliminar-usuario)
7. [Importar Usuarios desde Excel](#importar-usuarios-desde-excel)
8. [Gestión de Roles y Permisos](#gestión-de-roles-y-permisos)
9. [Historial de Usuarios](#historial-de-usuarios)
10. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El módulo de gestión de usuarios permite a los administradores del sistema crear, editar, eliminar y gestionar las cuentas de usuario del sistema de acceso del SENA. Este módulo es fundamental para mantener actualizada la base de datos de usuarios y controlar el acceso al sistema.

### Objetivos del Módulo
- Crear nuevas cuentas de usuario
- Editar información de usuarios existentes
- Eliminar usuarios que ya no requieren acceso
- Importar usuarios masivamente desde Excel
- Gestionar roles y permisos de usuario
- Mantener el historial de cambios

### Usuarios Autorizados
- Administradores de Sistema
- Personal autorizado por administración

---

## Acceso al Módulo de Gestión

### Paso 1: Iniciar Sesión
1. Acceda al sistema mediante la URL proporcionada por el SENA
2. Ingrese su correo institucional y contraseña de administrador
3. Haga clic en "Iniciar Sesión"

### Paso 2: Navegar a Gestión de Usuarios
1. Una vez iniciada la sesión, haga clic en el menú lateral
2. Seleccione la opción "Gestión de Perfiles" o "Usuarios"
3. Se mostrará la lista de usuarios del sistema

### Opciones Disponibles
- **Nuevo Perfil**: Crear un nuevo usuario
- **Importar Excel**: Importar usuarios masivamente
- **Editar**: Modificar información de usuario existente
- **Eliminar**: Eliminar usuario del sistema
- **Historial**: Ver historial de cambios

---

## Ver Lista de Usuarios

### Visualización de la Lista
Al acceder al módulo de gestión, verá una tabla con todos los usuarios del sistema.

### Información Mostrada
Para cada usuario se muestra:
- **Nombre**: Nombre completo del usuario
- **Documento**: Número de documento de identidad
- **Correo**: Correo electrónico institucional
- **Cargo**: Cargo o dependencia (Aprendiz, Instructor, etc.)
- **Rol**: Rol en el sistema (Admin, Usuario, etc.)
- **Estado**: Estado de la cuenta (Verificado, Pendiente, Bloqueado)
- **Acciones**: Botones para editar o eliminar

### Estados de Usuario
- **Verificado**: Usuario con correo verificado y acceso completo
- **Pendiente**: Usuario que aún no ha verificado su correo
- **Bloqueado**: Usuario con bloqueo temporal o permanente

### Filtros y Búsqueda
- **Búsqueda**: Puede buscar por nombre, documento o correo
- **Filtro por estado**: Filtrar usuarios por estado (verificado, pendiente, bloqueado)
- **Filtro por rol**: Filtrar usuarios por rol
- **Filtro por cargo**: Filtrar usuarios por cargo

---

## Crear Nuevo Usuario

### Paso 1: Abrir el Formulario de Creación
1. En la página de gestión de usuarios, haga clic en "Nuevo Perfil"
2. Se abrirá el formulario de creación de usuario

### Paso 2: Completar Información Básica

#### Campo 1: Nombre Completo
- **Descripción**: Nombre completo del usuario
- **Formato**: Nombre y apellidos completos
- **Ejemplo**: "Juan Pérez García"

#### Campo 2: Documento
- **Descripción**: Número de documento de identidad
- **Formato**: Según tipo de documento (CC, TI, CE, etc.)
- **Ejemplo**: "123456789"

#### Campo 3: Correo Electrónico
- **Descripción**: Correo institucional del usuario
- **Formato**: usuario@sena.edu.co
- **Importancia**: Se usará para inicio de sesión y verificación

#### Campo 4: Contraseña Temporal
- **Descripción**: Contraseña inicial para el usuario
- **Requisitos**: Mínimo 8 caracteres
- **Nota**: El usuario deberá cambiarla en el primer inicio

### Paso 3: Configurar Rol y Cargo

#### Campo 5: Rol de Sistema
Seleccione el rol apropiado:
- **Admin**: Administrador del sistema (acceso completo)
- **Usuario**: Usuario estándar (acceso limitado)
- **Celador**: Personal de portería
- Otros roles configurados en el sistema

#### Campo 6: Cargo / Dependencia
Seleccione el cargo del usuario:
- **Aprendiz**: Estudiante del SENA
- **Instructor**: Docente del SENA
- **Administrativo**: Personal administrativo
- **Celador**: Personal de seguridad
- **Administrador de Sistema**: Administrador técnico

### Paso 4: Información Adicional (Según Cargo)

#### Para Aprendices:
- **Ficha**: Número de ficha de formación
- **Programa**: Programa de formación
- **Horario**: Mañana, Tarde o Noche

#### Para Instructores:
- **Especialidad/Área**: Área de especialización

### Paso 5: Guardar Usuario
1. Verifique que toda la información sea correcta
2. Haga clic en "Guardar Usuario"
3. El sistema creará la cuenta de usuario
4. Se mostrará un mensaje de confirmación

### Validaciones
- **Correo único**: El correo no debe existir en el sistema
- **Documento único**: El documento no debe existir en el sistema
- **Campos obligatorios**: Todos los campos marcados son requeridos
- **Formato de correo**: Debe ser un correo válido

---

## Editar Usuario Existente

### Paso 1: Seleccionar el Usuario
1. En la lista de usuarios, encuentre el usuario que desea editar
2. Haga clic en el botón "Editar" (icono de lápiz)
3. Se abrirá el formulario de edición

### Paso 2: Modificar Información

#### Información Editable
- **Nombre completo**: Puede modificar el nombre
- **Documento**: Puede actualizar el documento
- **Correo**: Puede cambiar el correo (con precaución)
- **Rol**: Puede cambiar el rol del usuario
- **Cargo**: Puede cambiar el cargo
- **Ficha/Programa**: Puede actualizar información académica
- **Horario**: Puede modificar el horario

#### Información de Verificación
- **Estado de verificación**: Puede marcar correo como verificado
- **Estado de bloqueo**: Puede bloquear o desbloquear usuario

### Paso 3: Cambiar Contraseña (Opcional)
1. Puede establecer una nueva contraseña temporal
2. Deje el campo vacío para no cambiar la contraseña actual
3. El usuario deberá cambiarla en el próximo inicio

### Paso 4: Auditoría de Cambios
El sistema requiere registrar:
- **Quién autoriza el cambio**: Nombre del administrador que autoriza
- **Motivo**: Razón del cambio

### Paso 5: Guardar Cambios
1. Complete los campos de auditoría
2. Haga clic en "Guardar Cambios"
3. El sistema actualizará la información del usuario
4. Se mostrará un mensaje de confirmación

### Precauciones
- **Cambiar correo**: Puede afectar el acceso del usuario
- **Cambiar rol**: Modifica los permisos del usuario
- **Cambiar documento**: Puede afectar el código QR
- **Bloquear usuario**: Revoca el acceso inmediatamente

---

## Eliminar Usuario

### Paso 1: Seleccionar el Usuario
1. En la lista de usuarios, encuentre el usuario que desea eliminar
2. Haga clic en el botón "Eliminar" (icono de papelera)
3. Se abrirá un modal de confirmación

### Paso 2: Confirmar Eliminación
1. El sistema mostrará el nombre del usuario a eliminar
2. Lea el mensaje de advertencia
3. Esta acción es irreversible

### Paso 3: Auditoría de Eliminación
El sistema requiere registrar:
- **Quién autoriza la eliminación**: Nombre del administrador
- **Motivo**: Razón de la eliminación

### Paso 4: Confirmar
1. Complete los campos de auditoría
2. Haga clic en "Si, Eliminar"
3. El usuario será eliminado del sistema permanentemente
4. Si hace clic en "No, Cancelar", la eliminación se cancelará

### Restricciones
- **No puede eliminarse a sí mismo**: Un administrador no puede eliminar su propia cuenta
- **Usuarios con accesos activos**: Se recomienda verificar que no tenga accesos activos
- **Historial**: El historial de accesos se mantiene en el sistema

---

## Importar Usuarios desde Excel

### Paso 1: Acceder a Importación
1. En la página de gestión de usuarios, haga clic en "Importar Excel"
2. Se abrirá el modal de importación

### Paso 2: Preparar el Archivo Excel

#### Columnas Obligatorias
- **Nombre**: Nombre completo del usuario
- **Correo**: Correo institucional

#### Columnas Opcionales
- **Documento**: Número de documento
- **Cargo**: Cargo o dependencia
- **Rol**: Rol en el sistema
- **Ficha**: Número de ficha (para aprendices)
- **Programa**: Programa de formación (para aprendices)
- **Horario**: Horario (Mañana, Tarde, Noche)
- **Contraseña**: Contraseña temporal (si no se especifica, se genera una)

#### Formato del Archivo
- **Tipo**: .xlsx o .xls
- **Encoding**: UTF-8
- **Primera fila**: Debe contener los nombres de las columnas

### Paso 3: Cargar el Archivo
1. Haga clic en "Seleccionar archivo"
2. Seleccione el archivo Excel preparado
3. El sistema mostrará el nombre del archivo seleccionado

### Paso 4: Importar
1. Haga clic en "Subir e Importar"
2. El sistema procesará el archivo
3. Se mostrará un indicador de progreso

### Paso 5: Revisar Resultados
El sistema mostrará:
- **Total de usuarios procesados**
- **Usuarios creados exitosamente**
- **Errores encontrados** (si los hay)

### Errores Comunes en Importación

| Error | Causa | Solución |
|-------|-------|----------|
| "Correo duplicado" | El correo ya existe en el sistema | Verifique que el correo no esté duplicado |
| "Formato inválido" | El archivo no tiene el formato correcto | Use el formato .xlsx con columnas correctas |
| "Campo obligatorio faltante" | Falta nombre o correo | Asegúrese de incluir columnas obligatorias |
| "Rol inválido" | El rol especificado no existe | Use roles válidos del sistema |

### Plantilla de Excel
Se recomienda usar la plantilla proporcionada por el sistema para asegurar el formato correcto.

---

## Gestión de Roles y Permisos

### Roles del Sistema

#### Administrador
- **Permisos**: Acceso completo a todos los módulos
- **Funciones**: Gestión de usuarios, configuración del sistema, reportes
- **Restricciones**: No puede eliminarse a sí mismo

#### Usuario Estándar
- **Permisos**: Gestión de perfil, registro de equipos
- **Funciones**: Actualizar datos personales, registrar equipos
- **Restricciones**: No puede gestionar otros usuarios

#### Celador
- **Permisos**: Control de acceso, escaneo de QR
- **Funciones**: Registrar entradas/salidas, verificar usuarios
- **Restricciones**: No puede gestionar usuarios

#### Otros Roles
El sistema puede tener roles adicionales configurados según las necesidades de la institución.

### Cambiar Rol de Usuario
1. Edite el usuario
2. Seleccione el nuevo rol
3. Complete la auditoría de cambios
4. Guarde los cambios

### Impacto del Cambio de Rol
- **Permisos**: Los permisos se actualizan inmediatamente
- **Acceso**: El usuario puede perder o ganar acceso a módulos
- **Sesión**: El usuario debe cerrar y volver a iniciar sesión

---

## Historial de Usuarios

### Paso 1: Acceder al Historial
1. En el menú, seleccione "Historial"
2. Se mostrará el historial de cambios de usuarios

### Información del Historial
Para cada cambio se registra:
- **Fecha y hora** del cambio
- **Usuario modificado**
- **Tipo de cambio** (creación, edición, eliminación)
- **Administrador** que realizó el cambio
- **Motivo** del cambio
- **Campos modificados**

### Filtros del Historial
- **Por usuario**: Filtrar cambios por usuario específico
- **Por administrador**: Filtrar por quien realizó el cambio
- **Por tipo de cambio**: Filtrar por tipo de acción
- **Por rango de fechas**: Filtrar por periodo específico

### Exportación del Historial
1. Aplique los filtros deseados
2. Haga clic en "Exportar"
3. El sistema generará un archivo con el historial

---

## Buenas Prácticas

### Al Crear Usuarios
1. **Verifique la información**: Asegúrese de que todos los datos sean correctos
2. **Use correos institucionales**: Solo use correos oficiales del SENA
3. **Asigne el rol correcto**: El rol debe corresponder a las funciones del usuario
4. **Genere contraseñas seguras**: Use contraseuras temporales seguras

### Al Editar Usuarios
1. **Documente los cambios**: Complete siempre el motivo del cambio
2. **Comuníquese con el usuario**: Informe al usuario sobre cambios importantes
3. **Verifique el impacto**: Considere cómo el cambio afecta al usuario
4. **Mantenga el historial**: Los cambios quedan registrados automáticamente

### Al Eliminar Usuarios
1. **Verifique la necesidad**: Asegúrese de que la eliminación sea necesaria
2. **Confirme la identidad**: Verifique que es el usuario correcto
3. **Considere alternativas**: Considere bloquear en lugar de eliminar
4. **Documente el motivo**: Registre la razón de la eliminación

### Seguridad
1. **No comparta credenciales**: Mantenga su cuenta de administrador segura
2. **Use contraseñas fuertes**: Cambie su contraseña regularmente
3. **Revise accesos**: Monitoree usuarios con roles elevados
4. **Reporte irregularidades**: Notifique cualquier actividad sospechosa

---

## Preguntas Frecuentes

### ¿Puedo crear usuarios sin correo institucional?
No, el correo institucional es obligatorio y se usa para inicio de sesión y verificación.

### ¿Qué hago si un usuario olvida su contraseña?
Como administrador, puede editar el usuario y establecer una nueva contraseña temporal.

### ¿Puedo recuperar un usuario eliminado?
No, la eliminación es permanente. Si necesita recrear el usuario, debe crearlo nuevamente.

### ¿Cómo sé qué rol asignar a un usuario?
Asigne el rol según las funciones que realizará:
- **Admin**: Para personal técnico que gestiona el sistema
- **Celador**: Para personal de portería
- **Usuario**: Para aprendices, instructores y administrativos

### ¿Puedo importar usuarios con contraseñas ya establecidas?
Sí, puede incluir la columna "Contraseña" en el archivo Excel. Si no se incluye, el sistema generará una automáticamente.

### ¿Qué pasa si el archivo Excel tiene errores?
El sistema mostrará los errores encontrados y no importará los usuarios con errores. Puede corregir el archivo y volver a importar.

### ¿Puedo editar mi propio perfil?
Sí, puede editar su propio perfil, pero no puede cambiar su propio rol ni eliminarse a sí mismo.

### ¿Cómo manejo usuarios que ya no necesitan acceso?
Recomendamos bloquear el usuario en lugar de eliminarlo. Esto mantiene el historial pero revoca el acceso.

### ¿Puedo ver quién hizo cambios en un usuario específico?
Sí, el historial muestra todos los cambios con el administrador que los realizó y el motivo.

### ¿Hay límite en el número de usuarios que puedo importar?
No hay límite establecido, pero archivos muy grandes pueden tardar más en procesarse.

### ¿Puedo asignar múltiples roles a un usuario?
No, cada usuario tiene un solo rol. Si necesita permisos adicionales, contacte al equipo técnico para configurar roles personalizados.

---

## Soporte Técnico

Para reportar problemas o solicitar ayuda adicional con la gestión de usuarios, contacte al equipo de soporte técnico del Centro de Gestión Agroempresarial del Oriente.

### Información de Contacto
- **Soporte Técnico**: [Correo de soporte]
- **Horario**: [Horario de atención]
- **Ubicación**: [Ubicación física del soporte]

### Emergencias del Sistema
Para emergencias del sistema fuera del horario de soporte:
- Contacte al administrador de sistema on-call
- Use los canales de emergencia establecidos

---

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Institución:** SENA - Centro de Gestión Agroempresarial del Oriente
