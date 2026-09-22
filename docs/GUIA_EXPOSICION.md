# Guia de exposicion — Sistema de Gestion de Acceso SENA

## 1. Objetivo de la exposicion

Presentar el problema, la solucion desarrollada, el funcionamiento principal,
la estructura de datos y las medidas de seguridad del sistema de control de
acceso para una sede del SENA.

**Duracion total:** 20 minutos exactos.

**Distribucion:** 10 minutos para cada expositor.

**Integrantes:**

- **Brayan:** contexto, problema, objetivos, arquitectura y funcionamiento
  general.
- **Cristian:** base de datos, diagrama entidad-relacion, seguridad, pruebas y
  cierre tecnico.

La demostracion debe hacerse con datos de prueba. No se deben mostrar claves,
correos reales ni el archivo `config/.env`.

---

## 2. Orden general

| Tiempo | Tema | Responsable |
|---|---|---|
| 1 min | Saludo y presentacion del proyecto | Brayan |
| 3 min | Problema y objetivos | Brayan |
| 3 min | Usuarios y modulos principales | Brayan |
| 3 min | Arquitectura y demostracion funcional | Brayan |
| 4 min | Base de datos y diagrama entidad-relacion | Cristian |
| 2 min | Seguridad y reglas de acceso | Cristian |
| 3 min | Automatizaciones, pruebas y despliegue | Cristian |
| 1 min | Conclusiones y preguntas | Cristian |
| **20 min** | **Total** | **Brayan: 10 min / Cristian: 10 min** |

---

## 3. Parte de Brayan — 10 minutos

### 3.1 Saludo y presentacion

**Guion sugerido:**

> Buenos dias/tardes. Somos Brayan y Cristian y vamos a presentar nuestro
> sistema de gestion de acceso para una sede del SENA. La plataforma permite
> administrar usuarios, visitantes, vehiculos, objetos, carnets y movimientos
> de entrada y salida desde un solo sistema.

### 3.2 Problema que se resuelve

Explicar que el control manual o disperso puede producir:

- registros incompletos de entradas y salidas;
- dificultad para saber quien se encuentra dentro de la sede;
- perdida de trazabilidad sobre el funcionario que registro un movimiento;
- dificultad para controlar visitantes, vehiculos y objetos externos;
- informacion desactualizada de carnets, fichas y asistencia;
- riesgos de seguridad al no controlar permisos ni sesiones.

### 3.3 Objetivo general

> Desarrollar una plataforma web que centralice y controle el acceso de
> personas y entidades externas, manteniendo un historial auditable y
> aplicando permisos segun el rol y el cargo de cada usuario.

### 3.4 Objetivos especificos

Mencionar entre cuatro y seis:

1. Registrar entradas y salidas mediante escaner, documento o codigo QR.
2. Administrar usuarios, roles, cargos, fichas y carnets.
3. Controlar visitantes, vehiculos, equipos y objetos externos.
4. Gestionar asistencia a clases y consultar historiales.
5. Proteger fotos, cuentas, sesiones y datos personales.
6. Mantener auditoria, respaldos y pruebas automatizadas.

### 3.5 Usuarios del sistema

Explicar que el sistema no entrega los mismos permisos a todos:

- **Administrador:** gestiona usuarios, roles, fichas, fotos, auditoria y
  configuracion operativa.
- **Celador o personal de porteria:** usa el escaner, registra movimientos y
  administra pases de visitantes, vehiculos y objetos.
- **Instructor:** consulta y registra asistencia de sus fichas.
- **Aprendiz:** consulta su informacion, carnet e historial permitido.
- **Administrativo y coordinacion:** acceden a funciones de asesoramiento,
  ambientes, reportes o gestion segun su cargo.

### 3.6 Modulos principales

Presentar los modulos agrupandolos por funcion:

| Modulo | Funcion principal |
|---|---|
| Autenticacion | Registro, inicio de sesion, verificacion y recuperacion |
| Usuarios | Perfiles, cargos, roles, fotos y carnets |
| Porteria | Escaner, dashboard, pases y movimientos |
| Asistencia | Fichas, instructores, aprendices y asistencia a clase |
| Mensajeria | Comunicacion entre usuarios y administradores |
| Reportes | Historiales, analisis y exportaciones |
| Operacion | Respaldos mensuales, cierre automatico y auditoria |

### 3.7 Arquitectura

**Guion sugerido:**

> El proyecto utiliza Flask como framework web. Las rutas estan separadas en
> blueprints por modulo, los modelos representan las tablas mediante
> SQLAlchemy y las plantillas Jinja2 construyen la interfaz. En produccion se
> ejecuta en Docker con Gunicorn y se conecta a PostgreSQL. Para las pruebas se
> utiliza SQLite en memoria, lo que permite probar el sistema sin tocar la base
> de datos real.

Mostrar, si es posible, esta estructura simplificada:

```text
Navegador
    |
    v
Flask + Blueprints + Control de permisos
    |
    +-- SQLAlchemy --> PostgreSQL en produccion
    |
    +-- Jinja2 / CSS / JavaScript --> Interfaz web
    |
    +-- Servicios: correo, fotos, tareas y respaldos
```

### 3.8 Demostracion funcional — minuto 7 al 10

Brayan puede realizar esta demostracion en este orden:

1. Iniciar sesion con un usuario de prueba.
2. Mostrar el dashboard de porteria.
3. Escanear o consultar un documento valido.
4. Registrar una entrada y mostrar el cambio en el historial.
5. Crear un visitante o un vehiculo desde el modulo de pases.
6. Mostrar que un usuario sin permiso no puede entrar a una funcion de
   administrador.

**Transicion a Cristian:**

> Ya vimos como utiliza el sistema cada tipo de usuario. Ahora Cristian
> explicara como se organiza la informacion internamente y como se relacionan
> las tablas que soportan estas funciones.

---

## 4. Parte de Cristian — 10 minutos

### 4.1 Espacio para explicar el diagrama entidad-relacion — 4 minutos

**Antes de exponer:** insertar aqui la imagen final del diagrama, por ejemplo:

```markdown
![Diagrama entidad-relacion](ruta/al/diagrama.png)
```

Si no se dispone de una imagen, se puede explicar con este esquema conceptual:

```text
ROL 1 -------- N USUARIO
                 |
                 +-------- N EQUIPO
                 +-------- 1 CARNET
                 +-------- N MENSAJE
                 +-------- N AUDITORIA
                 +-------- N ACCESO como operador
                 +-------- N ASISTENCIA como aprendiz
                 +-------- N ASISTENCIA como instructor
                 |
                 +-------- 0..N FICHA

PUNTO_ACCESO 1 -------- N ACCESO
PUNTO_ACCESO 1 -------- N MOVIMIENTO_VISITANTE
PUNTO_ACCESO 1 -------- N MOVIMIENTO_VEHICULO
PUNTO_ACCESO 1 -------- N MOVIMIENTO_EQUIPO
PUNTO_ACCESO 1 -------- N MOVIMIENTO_OBJETO

VISITANTE 1 -------- N MOVIMIENTO_VISITANTE
VEHICULO  1 -------- N MOVIMIENTO_VEHICULO
EQUIPO    1 -------- N MOVIMIENTO_EQUIPO
OBJETO_EXTERNO 1 ---- N MOVIMIENTO_OBJETO

FICHA 1 -------- N USUARIO aprendiz
USUARIO 1 ------ 0..N ACCESO mediante referencia polimorfica
VISITANTE, VEHICULO y OBJETO_EXTERNO tambien pueden tener ACCESO
```

**Guion para explicar el diagrama:**

> El diagrama entidad-relacion muestra como se guarda la informacion y como se
> conectan las entidades. La tabla `usuarios` es central porque representa a
> las personas del sistema. Cada usuario tiene un rol, puede tener un carnet,
> equipos, mensajes, auditorias y registros de acceso.

> La tabla `roles` permite aplicar control de acceso basado en roles. La tabla
> `fichas` evita repetir el programa y la fecha de finalizacion en cada
> aprendiz. Un aprendiz puede pertenecer a una ficha, y una ficha puede tener
> varios aprendices.

> La tabla `puntos_acceso` identifica por donde se registra un movimiento. La
> tabla `accesos` guarda entradas y salidas. Su campo `tipo_referencia` permite
> distinguir si el movimiento corresponde a un usuario, visitante, vehiculo u
> objeto externo. Por eso `referencia_id` es polimorfico: se interpreta junto
> con `tipo_referencia`, no como una clave foranea directa a una sola tabla.

> Las tablas de movimientos de visitantes, vehiculos, equipos y objetos
> conservan el historial especifico de cada entidad. Finalmente, `auditoria`
> registra acciones importantes para saber que ocurrio, quien lo hizo, cuando
> ocurrio y sobre que registro.

### 4.2 Relaciones que conviene señalar

1. **Rol - Usuario:** un rol puede tener muchos usuarios; cada usuario tiene un
   rol.
2. **Ficha - Usuario:** una ficha puede agrupar varios aprendices; el usuario
   puede quedar sin ficha mientras su perfil esta incompleto.
3. **Usuario - Equipo:** una persona puede registrar varios equipos propios.
4. **Usuario - Carnet:** el carnet pertenece a un usuario y se utiliza para la
   identificacion.
5. **Punto de acceso - Acceso:** un punto puede generar muchos registros de
   entrada y salida.
6. **Usuario - Asistencia:** un usuario puede aparecer como instructor o como
   aprendiz, con relaciones distintas.
7. **Usuario - Mensaje:** cada hilo pertenece a una persona y cada mensaje
   conserva quien lo escribio.
8. **Usuario - Auditoria:** las acciones quedan asociadas al operador cuando
   es posible; la auditoria puede sobrevivir si esa cuenta se elimina.

### 4.3 Seguridad — 2 minutos

**Guion sugerido:**

> La seguridad no depende solamente de ocultar botones. Cada ruta valida la
> sesion y el permiso correspondiente. Las contrasenas se almacenan con hash,
> se controlan los intentos de inicio de sesion y las cookies se pueden marcar
> como seguras en produccion.

Mencionar estas medidas:

- autenticacion con Flask-Login;
- control de permisos por rol y cargo;
- proteccion CSRF para formularios;
- contrasenas almacenadas como hash, nunca en texto plano;
- bloqueo o control de intentos fallidos;
- limitador de peticiones para reducir abusos;
- validacion y sanitizacion de datos ingresados;
- fotos fuera de `static/`, servidas solo con sesion y permiso;
- codigos QR y documentos validados antes de registrar movimientos;
- secretos en variables de entorno, no en el repositorio;
- auditoria de acciones administrativas y movimientos.

### 4.4 Automatizaciones y operacion — 1 minuto

Explicar brevemente:

- El cierre automatico de medianoche registra salidas pendientes y deja el
  sistema listo para el siguiente dia.
- El respaldo mensual exporta accesos y asistencias a Excel, verifica que el
  archivo se pueda abrir y solo despues elimina esas filas de la base.
- El correo se utiliza para verificacion de cuentas, recuperacion de
  contrasena, credenciales temporales y avisos operativos.
- El despliegue usa Docker, Gunicorn y PostgreSQL externo.

### 4.5 Pruebas y despliegue — 2 minutos

**Guion sugerido:**

> Para verificar el sistema se construyo una suite de pruebas con pytest. Las
> pruebas utilizan SQLite en memoria, por lo que son independientes de la base
> de datos de produccion. Se cubren autenticacion, permisos, porteria,
> asistencia, carnets, fotos, correo, importacion de Excel, limites y
> seguridad.

Resultado de referencia actual:

```text
460 passed, 17 skipped, 1 xfailed
```

Comando para repetir la verificacion:

```bash
python -m pytest tests/ -v --tb=short
```

### 4.6 Cierre y preguntas — 1 minuto

**Guion sugerido:**

> En conclusion, el sistema centraliza el control de acceso y agrega
> trazabilidad, permisos y seguridad. Su estructura modular permite mantener y
> ampliar el proyecto, mientras que el modelo entidad-relacion organiza los
> datos de usuarios, accesos, entidades externas, asistencia y auditoria. Las
> pruebas automatizadas permiten comprobar que las funciones principales se
> mantengan estables.

**Pregunta final al publico:**

> ¿Desean que ampliemos la demostracion de algun modulo o relacion del modelo?

---

## 5. Preguntas frecuentes

### ¿Por que se usa PostgreSQL en produccion y SQLite en pruebas?

PostgreSQL es la base de datos prevista para el servidor. SQLite en memoria
permite ejecutar pruebas rapidas y aisladas sin modificar datos reales.

### ¿Que pasa si se elimina un usuario?

Depende del dato relacionado. Algunas relaciones se eliminan en cascada, como
equipos o mensajes propios; otras conservan el historial y dejan la referencia
en `NULL`, como ciertos registros de auditoria, accesos operados y asistencias
del instructor.

### ¿Por que `Acceso` no tiene una clave foranea directa a visitante y vehiculo?

Porque una misma tabla registra movimientos de varios tipos de entidad. La
combinacion de `referencia_id` y `tipo_referencia` indica a que modelo pertenece
el registro.

### ¿Como se evita que cualquier usuario entre al panel administrativo?

Cada ruta protegida revisa la sesion y las propiedades de permiso del usuario.
La interfaz puede ocultar opciones, pero la validacion importante ocurre en el
servidor.

### ¿Como se protegen las fotos?

Se almacenan fuera de la carpeta publica y se entregan mediante una ruta que
comprueba autenticacion y autorizacion.

### ¿Que diferencia hay entre rol y cargo?

El rol agrupa permisos generales, por ejemplo `Admin` o `Usuario`. El cargo
representa la funcion institucional, como aprendiz, instructor o celador, y
permite afinar las acciones disponibles.

---

## 6. Lista de preparacion

- Tener levantada la aplicacion o preparar capturas de las pantallas.
- Crear usuarios de prueba con permisos distintos.
- Preparar un visitante, un vehiculo y un objeto de prueba.
- Tener abierto el diagrama entidad-relacion.
- No mostrar `config/.env`, contrasenas, tokens ni datos personales reales.
- Probar el flujo de entrada y salida antes de la exposicion.
- Confirmar que el comando de pruebas funciona en el equipo que se va a usar.
- Acordar quien responde las preguntas de base de datos y quien responde las
  preguntas de interfaz o funcionamiento.
