# Manual de Usuario - Gestión de Perfil

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Acceso al Perfil](#acceso-al-perfil)
3. [Completar Perfil](#completar-perfil)
4. [Actualizar Datos Personales](#actualizar-datos-personales)
5. [Gestión de Foto de Perfil](#gestión-de-foto-de-perfil)
6. [Registro de Equipos](#registro-de-equipos)
7. [Carnet Digital y Código QR](#carnet-digital-y-código-qr)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El módulo de gestión de perfil permite a los usuarios del sistema mantener su información personal actualizada, registrar sus equipos, y obtener su carnet digital con código QR para el acceso a las instalaciones del SENA.

### Objetivos del Módulo
- Mantener actualizada la información personal
- Registrar equipos personales (laptops, tablets)
- Obtener carnet digital con código QR
- Gestionar foto de perfil con validación facial

---

## Acceso al Perfil

### Paso 1: Iniciar Sesión
![Pantalla de inicio de sesión](../images/login_screenshot.png)
1. Acceda al sistema mediante la URL proporcionada por el SENA
2. Ingrese su correo institucional y contraseña
3. Haga clic en "Iniciar Sesión"

> **💡 Consejo**: Si olvidó su contraseña, contacte al administrador del sistema.

### Paso 2: Navegar al Perfil
![Menú lateral con opción Mi Perfil](../images/menu_perfil.png)
1. Una vez iniciada la sesión, haga clic en el menú lateral (icono de tres líneas en la esquina superior izquierda)
2. Seleccione la opción "Mi Perfil"
3. Se mostrará la página de gestión de perfil con su carnet digital

---

## Completar Perfil

### Campos Obligatorios
Para activar su código QR de acceso, debe completar los siguientes campos:

#### 1. Documento de Identidad
- Ingrese su número de documento de identidad
- Este campo es obligatorio para la generación del QR

#### 2. Tipo de Sangre
- Seleccione su tipo de sangre de la lista desplegable
- Opciones disponibles: O+, O-, A+, A-, B+, B-, AB+, AB-
- Este campo es obligatorio para emergencias médicas

#### 3. Foto de Perfil
- Suba una foto reciente de su rostro
- La foto debe ser individual (sin otras personas)
- Se realizará validación facial automática

### Campos Adicionales (Según Rol)

#### Para Aprendices:
- **Programa de Formación**: Nombre del programa en el que está matriculado
- **Ficha**: Número de ficha de formación
- **Horario**: Mañana, Tarde o Noche

#### Para Instructores:
- **Especialidad/Área**: Área de especialización

---

## Actualizar Datos Personales

### Paso 1: Acceder al Formulario de Actualización
1. En la página de perfil, haga clic en el botón "Información" (icono de usuario)
2. Se abrirá el formulario de actualización de datos

### Paso 2: Modificar los Datos
1. **Documento**: Edite el campo de documento si es necesario
2. **Tipo de Sangre**: Seleccione o cambie su tipo de sangre
3. **Programa/Área**: Actualice su programa de formación o área de especialización
4. **Ficha**: Modifique el número de ficha si ha cambiado

### Paso 3: Guardar Cambios
1. Haga clic en el botón "Guardar Cambios"
2. El sistema mostrará un mensaje de confirmación
3. Los datos se actualizarán inmediatamente

### Validaciones
- **Programa**: Solo permite letras y espacios (sin números ni símbolos)
- **Tipo de Sangre**: Debe ser uno de los tipos válidos predefinidos
- **Documento**: Se eliminan caracteres HTML por seguridad

---

## Gestión de Foto de Perfil

### Requisitos de la Foto
- Formatos aceptados: PNG, JPG, JPEG, GIF, WebP, BMP, SVG, TIFF
- Tamaño máximo: 10 MB
- Debe mostrar claramente el rostro
- Debe ser una foto individual (sin otras personas)

### Paso 1: Subir Foto
1. En el formulario de actualización, haga clic en el campo "Foto de Perfil"
2. Seleccione la imagen desde su dispositivo
3. El sistema realizará validación facial automática

### Validación Facial Automática
El sistema utiliza detección facial para asegurar que:
- **Se detecte al menos un rostro**: Si no se detecta ningún rostro, la foto será rechazada
- **Solo una persona**: Si se detectan múltiples rostros, la foto será rechazada
- **Formato válido**: Si el formato no puede procesarse, se solicitará otro formato (JPG o PNG)

### Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| "No se detectó ningún rostro" | Foto sin rostro visible | Use una foto donde se vea claramente su cara |
| "Se detectó más de una persona" | Foto con múltiples personas | Use una foto individual |
| "No se pudo procesar la imagen" | Formato incompatible | Use JPG o PNG |

---

## Registro de Equipos

### Paso 1: Acceder a la Sección de Equipos
1. En la página de perfil, haga clic en el botón "Mis Equipos" (icono de laptop)
2. Se mostrará la lista de equipos registrados

### Paso 2: Registrar Nuevo Equipo
1. Haga clic en el botón "Añadir Equipos" (icono de más)
2. Complete el formulario:
   - **Serial/SN**: Número de serie del equipo
   - **Nombre del Equipo**: Nombre descriptivo (ej: "Laptop HP Pavilion")
   - **Tipo de Equipo**: Seleccione el tipo (Computador, Tablet, etc.)
3. Haga clic en "Vincular Equipo"

### Paso 3: Eliminar Equipo
1. En la lista de equipos, haga clic en el icono de papelera
2. Confirme la eliminación en el modal de confirmación
3. El equipo será desvinculado de su cuenta

### Notas Importantes
- Solo los usuarios con permiso pueden registrar equipos
- El número de serie debe ser único
- Puede registrar múltiples equipos

---

## Carnet Digital y Código QR

### Visualización del Carnet
El carnet digital se muestra automáticamente en la página de perfil cuando el perfil está completo.

### Información del Carnet
El carnet incluye:
- **Logo del SENA**
- **Nombre completo**
- **Cargo/Rol**
- **Documento de identidad**
- **Tipo de sangre**
- **Ficha** (para aprendices)
- **Programa de formación** (para aprendices)
- **Horario** (si está configurado)
- **Correo institucional**
- **Código QR de acceso**

### Código QR de Acceso
- **Estado Bloqueado**: Si el perfil está incompleto, el QR no se genera
- **Estado Activo**: Cuando el perfil está completo, el QR se genera automáticamente
- **Uso**: El QR se utiliza para el acceso a las instalaciones mediante escaneo

### Ampliar QR
1. Haga clic en el código QR en el carnet
2. Se abrirá una ventana modal con el QR ampliado
3. Preséntelo al escáner de manera clara

### Descargar Carnet
1. Haga clic en el botón "Descargar Carnet Institucional"
2. El sistema generará una imagen PNG del carnet
3. La imagen se descargará automáticamente a su dispositivo

### Requisitos para QR Activo
El código QR se activa cuando se completan todos los campos obligatorios:
- ✅ Documento de identidad
- ✅ Tipo de sangre
- ✅ Foto de perfil (distinta de la predeterminada)
- ✅ Programa y ficha (para aprendices)

---

## Preguntas Frecuentes

### ¿Por qué mi código QR aparece bloqueado?
El código QR se bloquea cuando el perfil está incompleto. Complete todos los campos obligatorios (documento, tipo de sangre, foto de perfil) para activarlo.

### ¿Puedo cambiar mi foto de perfil?
Sí, puede cambiar su foto de perfil en cualquier momento accediendo al formulario de actualización y seleccionando una nueva imagen.

### ¿Qué pasa si mi foto es rechazada por validación facial?
Si su foto es rechazada, intente con otra foto que cumpla los requisitos: rostro visible, foto individual, formato JPG o PNG.

### ¿Cuántos equipos puedo registrar?
Puede registrar múltiples equipos. No hay límite establecido, pero cada equipo debe tener un número de serie único.

### ¿Puedo eliminar mi cuenta del sistema?
No, la eliminación de cuentas debe ser realizada por un administrador del sistema.

### ¿Qué debo hacer si olvidé mi contraseña?
Utilice la opción "Recuperar Contraseña" en la página de inicio de sesión y siga los pasos indicados.

### ¿Mi información está segura?
Sí, el sistema implementa medidas de seguridad para proteger su información personal, incluyendo encriptación y validaciones de seguridad.

### ¿Puedo actualizar mi información desde cualquier dispositivo?
Sí, puede acceder a su perfil y actualizar su información desde cualquier dispositivo con conexión a internet.

### ¿Qué formato debe tener mi foto?
Formatos aceptados: PNG, JPG, JPEG, GIF, WebP, BMP, SVG, TIFF. Tamaño máximo: 10 MB.

### ¿Por qué mi programa de formación no se guarda?
El campo de programa solo permite letras y espacios. Si incluye números o símbolos, el sistema mostrará un error y no guardará el cambio.

---

## Soporte Técnico

Para reportar problemas o solicitar ayuda adicional con la gestión de perfil, contacte al equipo de soporte técnico del Centro de Gestión Agroempresarial del Oriente.

---

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Institución:** SENA - Centro de Gestión Agroempresarial del Oriente
