# Manual de Usuario - Rol Administrador

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Permisos y Responsabilidades](#permisos-y-responsabilidades)
3. [Gestión de Usuarios](#gestión-de-usuarios)
4. [Gestión de Equipos](#gestión-de-equipos)
5. [Control de Acceso](#control-de-acceso)
6. [Sistema de Asistencia](#sistema-de-asistencia)
7. [Configuración del Sistema](#configuración-del-sistema)
8. [Reportes y Estadísticas](#reportes-y-estadísticas)
9. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El rol de **Administrador** tiene acceso completo a todas las funcionalidades del sistema de gestión de acceso del SENA. Como administrador, usted es responsable de gestionar usuarios, configurar el sistema, generar reportes y mantener la seguridad de la plataforma.

### Objetivos del Rol
- Gestionar usuarios del sistema (crear, editar, eliminar)
- Configurar roles y permisos
- Importar usuarios desde Excel
- Generar reportes y estadísticas
- Supervisar el control de acceso
- Mantener la seguridad del sistema

### Características Principales
- ✅ Acceso completo a todos los módulos
- ✅ Gestión de usuarios (CRUD completo)
- ✅ Importación masiva de usuarios
- ✅ Configuración del sistema
- ✅ Reportes avanzados
- ✅ Supervisión de accesos

---

## Permisos y Responsabilidades

### Permisos del Administrador

| Módulo | Permisos |
|--------|----------|
| Gestión de Usuarios | Crear, editar, eliminar, importar, asignar roles |
| Gestión de Equipos | Ver, editar, eliminar equipos de cualquier usuario |
| Control de Acceso | Ver historial, generar reportes, configurar puntos de acceso |
| Sistema de Asistencia | Ver todas las fichas, generar reportes, exportar datos |
| Configuración | Modificar configuración del sistema, gestionar respaldos |

### Responsabilidades
- Mantener actualizada la información de usuarios
- Asignar roles y permisos apropiados
- Supervisar el control de acceso
- Generar reportes periódicos
- Mantener la seguridad del sistema
- Gestionar respaldos de datos

---

## Gestión de Usuarios

### Paso 1: Acceder a Gestión de Usuarios
1. Inicie sesión con su cuenta de administrador
2. Navegue al menú lateral
3. Seleccione "Gestión de Usuarios"

### Paso 2: Ver Lista de Usuarios
La tabla muestra todos los usuarios del sistema con:
- Nombre completo
- Documento de identidad
- Correo electrónico
- Cargo/Dependencia
- Rol de sistema
- Estado (Activo/Inactivo)
- Acciones (Editar/Eliminar)

### Paso 3: Crear Nuevo Usuario
1. Haga clic en el botón "Agregar Usuario"
2. Complete el formulario:
   - **Nombre**: Nombre completo del usuario
   - **Correo**: Correo institucional
   - **Documento**: Número de documento
   - **Contraseña**: Contraseña temporal (mínimo 8 caracteres)
   - **Cargo**: Cargo del usuario
   - **Rol**: Seleccione el rol apropiado
3. Haga clic en "Guardar"

> **⚠️ Importante**: La contraseña temporal debe ser cambiada por el usuario en el primer inicio de sesión.

### Paso 4: Editar Usuario
1. Haga clic en el botón "Editar" del usuario deseado
2. Modifique la información necesaria
3. Haga clic en "Guardar Cambios"

### Paso 5: Eliminar Usuario
1. Haga clic en el botón "Eliminar" del usuario deseado
2. Confirme la eliminación en el modal

> **⚠️ Advertencia**: La eliminación de usuarios es permanente. No se puede deshacer.

### Paso 6: Importar Usuarios desde Excel
1. Haga clic en el botón "Importar Excel"
2. Descargue la plantilla de Excel
3. Complete la plantilla con los datos de usuarios
4. Cargue el archivo Excel
5. Revise los datos importados
6. Haga clic en "Importar"

#### Estructura del Archivo Excel
| Columna | Descripción | Obligatorio |
|---------|-------------|-------------|
| nombre | Nombre completo | Sí |
| correo | Correo electrónico | Sí |
| documento | Documento de identidad | Sí |
| contraseña | Contraseña temporal | Sí |
| cargo | Cargo del usuario | Sí |
| rol | Rol de sistema | Sí |

---

## Gestión de Equipos

### Ver Equipos de Usuarios
Como administrador, puede ver y gestionar los equipos de cualquier usuario:

1. Acceda al perfil del usuario
2. Navegue a la sección "Mis Equipos"
3. Verá todos los equipos registrados por el usuario

### Editar/Eliminar Equipos
1. Haga clic en "Editar" para modificar datos del equipo
2. Haga clic en "Eliminar" para quitar el equipo del sistema

---

## Control de Acceso

### Supervisar Accesos en Tiempo Real
1. Navegue a "Control de Acceso"
2. Seleccione "Dashboard de Portería"
3. Verá estadísticas en tiempo real:
   - Usuarios dentro de las instalaciones
   - Entradas recientes
   - Salidas recientes
   - Pases temporales activos

### Ver Historial de Accesos
1. Navegue a "Control de Acceso"
2. Seleccione "Historial"
3. Filtre por fecha, usuario, o tipo de acceso
4. Exporte el historial si es necesario

### Configurar Puntos de Acceso
1. Navegue a "Control de Acceso"
2. Seleccione "Configuración"
3. Agregue o modifique puntos de acceso
4. Asigne permisos por punto de acceso

---

## Sistema de Asistencia

### Ver Asistencia de Fichas
1. Navegue a "Sistema de Asistencia"
2. Ingrese el número de ficha
3. Verá la lista de aprendices y su asistencia

### Generar Reportes de Asistencia
1. Seleccione el rango de fechas
2. Elija la ficha o instructor
3. Haga clic en "Generar Reporte"
4. Exporte a Excel si es necesario

### Ver Estadísticas de Asistencia
1. Navegue a "Sistema de Asistencia"
2. Seleccione "Estadísticas"
3. Verá gráficos y métricas de asistencia

---

## Configuración del Sistema

### Configurar Variables de Entorno
1. Acceda al archivo `config/.env`
2. Modifique las variables necesarias:
   - `SECRET_KEY`: Llave de seguridad
   - `DATABASE_URL`: URL de base de datos
   - `MAIL_SERVER`: Servidor de correo
   - `ADMIN_EMAIL`: Correo del administrador
3. Reinicie el servidor para aplicar cambios

### Gestionar Respaldos
El sistema genera respaldos automáticos mensuales. Puede:
1. Ver respaldos en `app/respaldos_mensuales/`
2. Descargar respaldos específicos
3. Restaurar respaldos si es necesario

> **💡 Consejo**: Mantenga copias de seguridad de los respaldos en ubicaciones externas.

---

## Reportes y Estadísticas

### Reportes de Usuarios
1. Navegue a "Reportes"
2. Seleccione "Reporte de Usuarios"
3. Filtre por rol, estado, o fecha
4. Exporte a PDF o Excel

### Reportes de Acceso
1. Navegue a "Reportes"
2. Seleccione "Reporte de Accesos"
3. Configure filtros de fecha y tipo
4. Exporte el reporte

### Reportes de Asistencia
1. Navegue a "Reportes"
2. Seleccione "Reporte de Asistencia"
3. Seleccione ficha y rango de fechas
4. Exporte el reporte

---

## Buenas Prácticas

### Seguridad
1. **Contraseñas**: Use contraseuras seguras para usuarios nuevos
2. **Roles**: Asigne roles mínimos necesarios
3. **Auditoría**: Revise regularmente el historial de accesos
4. **Respaldos**: Verifique que los respaldos se generen correctamente

### Gestión de Usuarios
1. **Verificación**: Verifique la información antes de crear usuarios
2. **Actualización**: Mantenga actualizada la información de usuarios
3. **Eliminación**: Elimine solo usuarios que ya no necesitan acceso
4. **Importación**: Revise los datos antes de importar desde Excel

### Reportes
1. **Frecuencia**: Genere reportes periódicos (semanales/mensuales)
2. **Análisis**: Analice las tendencias en los reportes
3. **Acción**: Tome acciones basadas en los datos de los reportes
4. **Archivo**: Archive reportes importantes para referencia futura

---

## Preguntas Frecuentes

### ¿Puedo eliminar mi propia cuenta de administrador?
No, por seguridad el sistema no permite que un administrador se elimine a sí mismo.

### ¿Qué pasa si elimino un usuario por error?
La eliminación es permanente. Mantenga respaldos de datos regularmente para recuperación.

### ¿Puedo cambiar el rol de un usuario existente?
Sí, puede editar el usuario y cambiar su rol en cualquier momento.

### ¿Cómo importo muchos usuarios a la vez?
Use la función "Importar Excel" para cargar múltiples usuarios desde un archivo Excel.

### ¿Puedo ver el historial de cambios de un usuario?
Sí, el sistema mantiene un registro de todas las modificaciones realizadas a los usuarios.

### ¿Qué debo hacer si un usuario olvidó su contraseña?
Como administrador, puede restablecer la contraseña editando el usuario y asignando una nueva temporal.

### ¿Puedo crear roles personalizados?
Actualmente el sistema tiene roles predefinidos. Para roles personalizados, contacte al equipo de desarrollo.

### ¿Cómo genero un reporte de asistencia mensual?
Navegue a "Sistema de Asistencia" → "Reportes", seleccione el mes y ficha, luego exporte.

### ¿Puedo limitar el acceso de un usuario a ciertos horarios?
Sí, puede configurar restricciones de horario en la configuración del usuario.

### ¿Qué debo hacer si detecto un acceso no autorizado?
1. Revise el historial de accesos
2. Bloquee al usuario si es necesario
3. Reporte el incidente a seguridad
4. Revise las medidas de seguridad

---

## Soporte Técnico

Para asistencia técnica adicional:
- Correo: soporte@sena.edu.co
- Teléfono: [Número de soporte]
- Horario: Lunes a Viernes, 8:00 AM - 5:00 PM

---

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Institución:** SENA - Centro de Gestión Agroempresarial del Oriente
