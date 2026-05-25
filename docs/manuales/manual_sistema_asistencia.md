# Manual de Usuario - Sistema de Asistencia

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Acceso al Módulo de Asistencia](#acceso-al-módulo-de-asistencia)
3. [Buscar Ficha](#buscar-ficha)
4. [Registrar Asistencia](#registrar-asistencia)
5. [Ver Lista de Aprendices](#ver-lista-de-aprendices)
6. [Exportar Asistencia](#exportar-asistencia)
7. [Historial de Asistencia](#historial-de-asistencia)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El módulo de sistema de asistencia permite a instructores y personal autorizado registrar y controlar la asistencia de aprendices por ficha de formación. Este sistema facilita el seguimiento de la asistencia y la generación de reportes.

### Objetivos del Módulo
- Registrar asistencia de aprendices por ficha
- Controlar la presencia en clases o actividades
- Generar reportes de asistencia
- Mantener historial de registros
- Facilitar el seguimiento académico

### Usuarios Autorizados
- Instructores
- Coordinadores de formación
- Personal administrativo autorizado

---

## Acceso al Módulo de Asistencia

### Paso 1: Iniciar Sesión
1. Acceda al sistema mediante la URL proporcionada por el SENA
2. Ingrese su correo institucional y contraseña
3. Haga clic en "Iniciar Sesión"

### Paso 2: Navegar al Módulo de Asistencia
1. Una vez iniciada la sesión, haga clic en el menú lateral
2. Seleccione la opción "Asistencia"
3. Se mostrará la página de búsqueda de ficha

### Requisitos
- Debe tener permiso de instructor o coordinador
- La ficha debe estar activa en el sistema
- Los aprendices deben tener perfiles completos

---

## Buscar Ficha

### Paso 1: Ingresar Número de Ficha
1. En el campo "Código de Ficha", ingrese el número de ficha
2. Ejemplo: "1234567" o "2024001"

### Paso 2: Buscar
1. Haga clic en el botón de búsqueda (icono de lupa)
2. El sistema buscará la ficha en la base de datos

### Resultados de Búsqueda

#### Ficha Encontrada
Si la ficha existe:
- Se mostrará el número de ficha
- Se mostrará la lista de aprendices de esa ficha
- Podrá proceder a registrar asistencia

#### Ficha No Encontrada
Si la ficha no existe:
- El sistema mostrará un mensaje de error
- Verifique el número de ficha ingresado
- Contacte a administración si la ficha debería existir

### Validaciones
- **Formato**: El número de ficha debe ser válido
- **Existencia**: La ficha debe estar registrada en el sistema
- **Permisos**: Debe tener permiso para acceder a esa ficha

---

## Registrar Asistencia

### Paso 1: Seleccionar Ficha
1. Busque la ficha deseada (ver sección "Buscar Ficha")
2. El sistema mostrará la lista de aprendices

### Paso 2: Ver Lista de Aprendices
Para cada aprendiz se muestra:
- **Nombre completo**
- **Documento** de identidad
- **Estado actual** (presente/ausente)
- **Checkbox** para marcar asistencia

### Paso 3: Marcar Asistencia
1. Marque los aprendices presentes con el checkbox
2. Los aprendices no marcados se considerarán ausentes
3. Puede marcar o desmarcar según sea necesario

### Paso 4: Guardar Asistencia
1. Haga clic en el botón "Guardar Asistencia"
2. El sistema registrará:
   - Fecha y hora del registro
   - Ficha
   - Instructor que realizó el registro
   - Lista de presentes y ausentes
3. Se mostrará un mensaje de confirmación

### Opciones Adicionales

#### Fecha de Asistencia
- Por defecto, registra la fecha actual
- Puede seleccionar una fecha diferente si es necesario
- Útil para registrar asistencia retroactiva

#### Observaciones
- Puede agregar observaciones sobre la asistencia
- Útil para justificaciones o notas especiales

---

## Ver Lista de Aprendices

### Información Mostrada
Al buscar una ficha, el sistema muestra:

#### Datos de la Ficha
- **Número de ficha**
- **Programa de formación**
- **Horario** (Mañana, Tarde, Noche)
- **Instructor asignado**

#### Lista de Aprendices
Para cada aprendiz:
- **Nombre completo**
- **Documento de identidad**
- **Foto de perfil** (si está disponible)
- **Estado de asistencia** (presente/ausente)
- **Checkbox** para marcar

#### Estadísticas
- **Total de aprendices** en la ficha
- **Número de presentes** (marcados)
- **Número de ausentes** (no marcados)

### Ordenamiento
- La lista se ordena alfabéticamente por nombre
- Puede facilitar la identificación de aprendices

### Búsqueda en Lista
- Puede usar la función de búsqueda del navegador (Ctrl+F)
- Busque por nombre o documento para encontrar aprendices específicos

---

## Exportar Asistencia

### Paso 1: Registrar Asistencia
Primero debe registrar la asistencia (ver sección "Registrar Asistencia")

### Paso 2: Exportar
1. Después de guardar, haga clic en "Exportar"
2. El sistema generará un archivo con los datos de asistencia

### Formatos de Exportación
- **Excel (.xlsx)**: Formato de hoja de cálculo
- **PDF**: Formato de documento
- **CSV**: Formato de valores separados por comas

### Información Exportada
El archivo exportado incluye:
- Fecha de registro
- Número de ficha
- Nombre del instructor
- Lista de aprendices presentes
- Lista de aprendices ausentes
- Estadísticas de asistencia

### Uso de la Exportación
- **Reportes académicos**: Para seguimiento de aprendices
- **Archivos**: Para mantener registros históricos
- **Análisis**: Para estadísticas de asistencia
- **Comunicación**: Para compartir con coordinación

---

## Historial de Asistencia

### Paso 1: Acceder al Historial
1. En el menú, seleccione "Historial"
2. Se mostrará el historial de registros de asistencia

### Información del Historial
Para cada registro se muestra:
- **Fecha y hora** del registro
- **Ficha**
- **Instructor** que realizó el registro
- **Número de presentes**
- **Número de ausentes**
- **Acciones**: Ver detalles, exportar

### Filtros del Historial
- **Por ficha**: Filtrar por número de ficha específico
- **Por instructor**: Filtrar por instructor que realizó el registro
- **Por rango de fechas**: Filtrar por periodo específico
- **Por programa**: Filtrar por programa de formación

### Ver Detalles de un Registro
1. Haga clic en "Ver detalles" en el registro deseado
2. Se mostrará:
   - Lista completa de aprendices
   - Estado de cada aprendiz (presente/ausente)
   - Observaciones (si las hay)
   - Fecha y hora exacta del registro

### Editar Registro (Si está Permitido)
1. Algunos sistemas permiten editar registros recientes
2. Haga clic en "Editar" si está disponible
3. Modifique la asistencia según sea necesario
4. Guarde los cambios

### Restricciones de Edición
- **Tiempo**: Puede haber un límite de tiempo para editar
- **Permisos**: Solo ciertos usuarios pueden editar
- **Auditoría**: Los cambios quedan registrados

---

## Buenas Prácticas

### Al Registrar Asistencia
1. **Sea consistente**: Registre asistencia a la misma hora siempre que sea posible
2. **Verifique la ficha**: Asegúrese de que es la ficha correcta
3. **Revise la lista**: Verifique que todos los aprendices estén en la lista
4. **Marque cuidadosamente**: Revise los marcados antes de guardar

### Al Manejar Ausencias
1. **Documente justificaciones**: Si hay justificaciones, agrégalas como observaciones
2. **Comuníquese**: Informe a coordinación sobre ausencias recurrentes
3. **Siga protocolos**: Siga los protocolos establecidos por el SENA
4. **Mantenga registros**: Guarde los registros para seguimiento

### Al Exportar Datos
1. **Organice archivos**: Use nombres descriptivos para los archivos exportados
2. **Guarde copias**: Mantenga copias de seguridad de los registros
3. **Comparta apropiadamente**: Comparta solo con personal autorizado
4. **Revise antes de enviar**: Verifique la información antes de compartirla

### Seguridad y Privacidad
1. **Proteja datos**: La información de asistencia es confidencial
2. **Acceso limitado**: Solo comparta con personal autorizado
3. **Cumpla normativas**: Siga las normativas de protección de datos
4. **Reporte incidentes**: Notifique cualquier brecha de seguridad

---

## Preguntas Frecuentes

### ¿Qué hago si un aprendiz no aparece en la lista?
1. Verifique que el aprendiz tenga perfil completo en el sistema
2. Contacte a administración para verificar el registro del aprendiz
3. Si es un aprendiz nuevo, solicite que sea registrado en el sistema

### ¿Puedo registrar asistencia para fechas futuras?
No, el sistema solo permite registrar asistencia para la fecha actual o fechas pasadas.

### ¿Puedo corregir un registro de asistencia incorrecto?
Depende de la configuración del sistema. Algunos registros pueden editarse dentro de un periodo de tiempo. Contacte a administración si necesita correcciones.

### ¿Qué hago si un aprendiz llega tarde?
Marque la asistencia según el momento del registro. Puede agregar una observación sobre el retraso si es necesario.

### ¿Puedo registrar asistencia para múltiples fichas a la vez?
No, debe registrar asistencia por ficha individualmente. Esto asegura mayor precisión en los registros.

### ¿Cómo sé si un aprendiz tiene justificación por ausencia?
El sistema no gestiona justificaciones automáticamente. Debe agregarlas como observaciones o usar el sistema de justificaciones establecido por su institución.

### ¿Puedo ver el historial de asistencia de un aprendiz específico?
Sí, puede filtrar el historial por aprendiz o ver el perfil del aprendiz para ver su historial de asistencia.

### ¿Qué hago si el sistema no me permite guardar la asistencia?
1. Verifique que haya marcado al menos un aprendiz
2. Asegúrese de tener conexión a internet
3. Contacte a soporte técnico si el problema persiste

### ¿Puedo registrar asistencia desde mi teléfono?
Sí, el sistema es responsive y puede accederse desde dispositivos móviles, aunque se recomienda usar una computadora para mejor experiencia.

### ¿Cuánto tiempo se mantienen los registros de asistencia?
Los registros se mantienen indefinidamente en el sistema según la política de retención de datos del SENA.

### ¿Puedo exportar asistencia de múltiples fichas a la vez?
No, debe exportar por ficha individualmente. Puede luego consolidar los datos en una hoja de cálculo si es necesario.

---

## Integración con Otros Módulos

### Sistema de Acceso (Portería)
- Los registros de acceso en portería pueden complementar la asistencia
- Puede verificar si un aprendiz ingresó a las instalaciones
- Útil para validar justificaciones de ausencia

### Gestión de Perfiles
- Los aprendices deben tener perfiles completos para aparecer en las listas
- La información del perfil se usa en los reportes de asistencia

### Historial de Usuarios
- Los cambios en perfiles pueden afectar las listas de asistencia
- Mantenga los perfiles actualizados para mayor precisión

---

## Soporte Técnico

Para reportar problemas o solicitar ayuda adicional con el sistema de asistencia, contacte al equipo de soporte técnico del Centro de Gestión Agroempresarial del Oriente.

### Información de Contacto
- **Soporte Técnico**: [Correo de soporte]
- **Horario**: [Horario de atención]
- **Ubicación**: [Ubicación física del soporte]

### Capacitación
Para solicitar capacitación adicional sobre el uso del sistema:
- Contacte al coordinador de formación
- Solicite sesiones de entrenamiento para instructores
- Consulte los materiales de capacitación disponibles

---

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Institución:** SENA - Centro de Gestión Agroempresarial del Oriente
