# Manual de Usuario - Control de Acceso (Portería)

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Acceso al Módulo de Portería](#acceso-al-módulo-de-portería)
3. [Escaneo de Código QR](#escaneo-de-código-qr)
4. [Verificación de Usuarios](#verificación-de-usuarios)
5. [Registro de Entradas y Salidas](#registro-de-entradas-y-salidas)
6. [Gestión de Equipos en Acceso](#gestión-de-equipos-en-acceso)
7. [Pases Temporales](#pases-temporales)
8. [Dashboard de Accesos](#dashboard-de-accesos)
9. [Historial de Clases](#historial-de-clases)
10. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El módulo de control de acceso (portería) permite a los celadores y personal de seguridad gestionar el ingreso y egreso de personas y equipos a las instalaciones del SENA mediante el uso de códigos QR y verificación de identidad.

### Objetivos del Módulo
- Controlar el acceso de usuarios a las instalaciones
- Registrar entradas y salidas con timestamp
- Verificar la identidad de usuarios mediante QR
- Gestionar el ingreso de equipos personales
- Emitir pases temporales para visitantes
- Mantener un historial de accesos

### Usuarios Autorizados
- Celadores
- Administradores de Sistema
- Personal de seguridad autorizado

---

## Acceso al Módulo de Portería

### Paso 1: Iniciar Sesión
1. Acceda al sistema mediante la URL proporcionada por el SENA
2. Ingrese su correo institucional y contraseña
3. Haga clic en "Iniciar Sesión"

### Paso 2: Navegar al Módulo de Portería
1. Una vez iniciada la sesión, haga clic en el menú lateral
2. Seleccione la opción "Portería" o "Control de Acceso"
3. Se mostrará el dashboard de control de acceso

### Opciones Disponibles
- **Escáner**: Para escanear códigos QR
- **Verificar**: Para verificar usuarios manualmente
- **Dashboard**: Ver historial y estadísticas
- **Pases**: Gestionar pases temporales
- **Historial de Clases**: Control de asistencia por ficha

---

## Escaneo de Código QR

### Paso 1: Acceder al Escáner
1. En el menú de portería, seleccione "Escáner"
2. Se abrirá la interfaz de escaneo de QR

### Paso 2: Escanear el Código QR
1. Solicite al usuario que presente su carnet digital con código QR
2. Apunte la cámara del dispositivo hacia el código QR
3. El sistema detectará automáticamente el código
4. Se mostrará la información del usuario

### Información Mostrada al Escanear
- **Nombre completo** del usuario
- **Documento** de identidad
- **Cargo/Rol** en el sistema
- **Foto de perfil**
- **Estado** del perfil (verificado/bloqueado)
- **Equipos** registrados (si tiene)

### Paso 3: Registrar Acceso
1. Verifique que la información sea correcta
2. Seleccione el tipo de acceso:
   - **Entrada**: Para registrar ingreso a las instalaciones
   - **Salida**: Para registrar egreso de las instalaciones
3. Si el usuario tiene equipos registrados, seleccione los equipos que ingresan/egresan
4. Haga clic en el botón correspondiente ("Registrar Entrada" o "Registrar Salida")
5. El sistema mostrará un mensaje de confirmación

### Validaciones Automáticas
- **Perfil Completo**: El sistema verifica que el perfil esté completo
- **Estado del Usuario**: Verifica que el usuario no esté bloqueado
- **Horarios**: (Opcional) Verifica si el usuario tiene acceso en el horario actual

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| "QR no válido" | Código QR dañado o incorrecto | Solicite al usuario que muestre su carnet nuevamente |
| "Usuario no encontrado" | Usuario no registrado en el sistema | Verifique manualmente la identidad del usuario |
| "Perfil incompleto" | El usuario no ha completado su perfil | Indique al usuario que complete su perfil |
| "Usuario bloqueado" | El usuario tiene bloqueo activo | Contacte a administración |

---

## Verificación de Usuarios

### Paso 1: Acceder a Verificación
1. En el menú de portería, seleccione "Verificar"
2. Se abrirá el formulario de verificación manual

### Paso 2: Buscar Usuario
Puede buscar usuario por:
- **Documento de identidad**: Ingrese el número de documento
- **Nombre**: Ingrese el nombre completo (puede ser parcial)

### Paso 3: Verificar Información
1. El sistema mostrará los resultados de búsqueda
2. Seleccione el usuario correcto de la lista
3. Se mostrará la información completa del usuario

### Información Disponible
- Datos personales (nombre, documento, correo)
- Información del perfil (cargo, rol, programa, ficha)
- Estado de verificación de correo
- Estado de bloqueo (si aplica)
- Foto de perfil
- Equipos registrados

### Paso 4: Registrar Acceso
Una vez verificado el usuario, puede registrar su acceso siguiendo el mismo proceso que en el escáner de QR.

---

## Registro de Entradas y Salidas

### Registro de Entrada

#### Paso 1: Identificar al Usuario
- Escanee el código QR del usuario, o
- Busque el usuario manualmente

#### Paso 2: Verificar Equipos
Si el usuario tiene equipos registrados:
1. Se mostrará una lista de sus equipos
2. Seleccione los equipos que ingresan con el usuario
3. Puede seleccionar múltiples equipos
4. Si no ingresa equipos, deje la selección vacía

#### Paso 3: Confirmar Entrada
1. Haga clic en "Registrar Entrada"
2. El sistema registrará:
   - Fecha y hora de entrada
   - Usuario que ingresa
   - Equipos que ingresan (si aplica)
   - Celador que realizó el registro

### Registro de Salida

#### Paso 1: Identificar al Usuario
- Escanee el código QR del usuario, o
- Busque el usuario manualmente

#### Paso 2: Verificar Equipos
Si el usuario tiene equipos registrados:
1. Se mostrará una lista de sus equipos
2. Seleccione los equipos que egresan con el usuario
3. Puede seleccionar múltiples equipos
4. Si no egresan equipos, deje la selección vacía

#### Paso 3: Confirmar Salida
1. Haga clic en "Registrar Salida"
2. El sistema registrará:
   - Fecha y hora de salida
   - Usuario que egresa
   - Equipos que egresan (si aplica)
   - Celador que realizó el registro

### Validaciones de Salida
- **Equipos sin entrada**: Si un equipo egresa sin haber entrado, el sistema mostrará una advertencia
- **Salida sin entrada**: Si un usuario egresa sin haber entrado, el sistema mostrará una advertencia

---

## Gestión de Equipos en Acceso

### Visualización de Equipos del Usuario
Al escanear o verificar un usuario, el sistema muestra:
- Lista de equipos registrados por el usuario
- Estado de cada equipo (dentro/fuera de instalaciones)
- Número de serie de cada equipo

### Selección de Equipos
- **Entrada**: Seleccione los equipos que ingresan con el usuario
- **Salida**: Seleccione los equipos que egresan con el usuario
- **Selección múltiple**: Puede seleccionar varios equipos a la vez

### Advertencias
- **Equipo ya dentro**: Si intenta registrar entrada de un equipo que ya está dentro, el sistema mostrará una advertencia
- **Equipo fuera**: Si intenta registrar salida de un equipo que ya está fuera, el sistema mostrará una advertencia

---

## Pases Temporales

### ¿Qué son los Pases Temporales?
Los pases temporales permiten el acceso a visitantes o personas que no tienen perfil permanente en el sistema.

### Paso 1: Acceder a Pases
1. En el menú de portería, seleccione "Pases"
2. Se mostrará la lista de pases activos y el formulario para crear nuevos

### Paso 2: Crear un Pase Temporal
1. Haga clic en "Crear Nuevo Pase"
2. Complete el formulario:
   - **Nombre completo** del visitante
   - **Documento** de identidad
   - **Motivo** de la visita
   - **Fecha** de validez
   - **Hora** de validez (inicio y fin)
   - **Área** a la que tiene acceso
3. Haga clic en "Generar Pase"

### Paso 3: Entregar el Pase
1. El sistema generará un código QR temporal
2. Imprima o muestre el código QR al visitante
3. El visitante puede usar este QR para acceso durante el periodo de validez

### Gestión de Pases
- **Ver pases activos**: Lista de pases actualmente vigentes
- **Ver pases expirados**: Historial de pases que ya expiraron
- **Cancelar pase**: Puede cancelar un pase antes de que expire
- **Extender validez**: Puede extender la validez de un pase existente

---

## Dashboard de Accesos

### Paso 1: Acceder al Dashboard
1. En el menú de portería, seleccione "Dashboard"
2. Se mostrará el panel de control de accesos

### Información Disponible

#### Estadísticas Generales
- Total de accesos hoy
- Total de entradas hoy
- Total de salidas hoy
- Usuarios actualmente dentro
- Equipos actualmente dentro

#### Filtros
- **Por fecha**: Filtrar accesos por rango de fechas
- **Por cargo**: Filtrar por tipo de usuario (aprendiz, instructor, etc.)
- **Por tipo de acceso**: Entradas o salidas

#### Historial Reciente
- Lista de los últimos accesos registrados
- Muestra usuario, tipo de acceso, fecha y hora
- Puede ver detalles de cada acceso

### Exportación de Datos
1. Seleccione el rango de fechas deseado
2. Aplique los filtros necesarios
3. Haga clic en "Exportar"
4. El sistema generará un archivo con los datos

---

## Historial de Clases

### ¿Qué es el Historial de Clases?
El historial de clases permite ver los accesos de aprendices de una ficha específica, útil para controlar asistencia.

### Paso 1: Acceder al Historial de Clases
1. En el menú de portería, seleccione "Historial de Clases"
2. Se mostrará el formulario de búsqueda por ficha

### Paso 2: Buscar por Ficha
1. Ingrese el número de ficha
2. Haga clic en "Buscar"
3. Se mostrarán los aprendices de esa ficha

### Paso 3: Ver Historial
Para cada aprendiz se muestra:
- Nombre completo
- Documento
- Historial de accesos recientes
- Estado actual (dentro/fuera)

### Registro de Asistencia
1. Puede registrar asistencia masiva para la ficha
2. Seleccione la fecha
3. Marque los aprendices presentes
4. Haga clic en "Guardar Asistencia"

---

## Buenas Prácticas

### Durante el Escaneo de QR
1. **Verifique la identidad**: Asegúrese de que la persona corresponde al perfil escaneado
2. **Revise el estado**: Verifique que el usuario no esté bloqueado
3. **Confirme equipos**: Si el usuario lleva equipos, verifique que coincidan con los registrados
4. **Registre correctamente**: Seleccione el tipo de acceso apropiado (entrada/salida)

### Al Manejar Visitantes
1. **Solicite identificación**: Pida documento de identidad al visitante
2. **Registre el motivo**: Anote el motivo de la visita
3. **Defina el tiempo**: Establezca un periodo de validez apropiado
4. **Monitoree el pase**: Revise regularmente los pases activos

### Seguridad
1. **No comparta credenciales**: Mantenga su cuenta de celador segura
2. **Reporte irregularidades**: Notifique cualquier situación sospechosa
3. **Mantenga el orden**: Siga los protocolos establecidos
4. **Documente incidentes**: Registre cualquier incidente o anomalía

---

## Preguntas Frecuentes

### ¿Qué hago si el código QR no se escanea?
1. Solicite al usuario que muestre el QR nuevamente
2. Asegúrese de que haya buena iluminación
3. Si persiste, use la verificación manual por documento

### ¿Puedo registrar acceso sin escanear QR?
Sí, puede usar la función de verificación manual buscando al usuario por documento o nombre.

### ¿Qué hago si el usuario no tiene perfil en el sistema?
1. Verifique si es un visitante y emita un pase temporal
2. Si es un usuario del SENA sin perfil, contacte a administración
3. No permita el acceso sin verificación adecuada

### ¿Puedo corregir un registro de acceso incorrecto?
No, los registros de acceso no se pueden modificar directamente. Contacte a administración para correcciones.

### ¿Cómo sé si un usuario tiene equipos registrados?
Al escanear o verificar el usuario, el sistema muestra automáticamente la lista de equipos registrados.

### ¿Qué hago si un usuario intenta salir con equipos que no registró?
1. No permita la salida de equipos no registrados
2. Indique al usuario que registre sus equipos en su perfil
3. Si es necesario, contacte a administración

### ¿Puedo ver el historial de accesos de un usuario específico?
Sí, puede usar el dashboard y filtrar por usuario, o verificar al usuario específico para ver su historial.

### ¿Qué pasa si el sistema se cae durante mi turno?
1. Mantenga un registro manual de accesos
2. Notifique al soporte técnico inmediatamente
3. Cuando el sistema se restablezca, reporte los accesos manuales

### ¿Puedo acceder al sistema desde mi teléfono?
Sí, el sistema es responsive y puede accederse desde dispositivos móviles, aunque se recomienda usar una tablet o computadora para mejor experiencia.

### ¿Cómo manejo situaciones de emergencia?
En caso de emergencia, siga los protocolos de seguridad establecidos por el SENA. El sistema de acceso es secundario a la seguridad física.

### ¿Puedo delegar mis funciones a otro celador?
No, cada celador debe usar sus propias credenciales. No comparta su cuenta con otros usuarios.

---

## Soporte Técnico

Para reportar problemas o solicitar ayuda adicional con el módulo de control de acceso, contacte al equipo de soporte técnico del Centro de Gestión Agroempresarial del Oriente.

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
