# Docker

Tres archivos, y cada uno tiene un momento:

| Archivo | Para qué |
|---|---|
| `Dockerfile` | La imagen. La usan los dos Compose. |
| `docker-compose.yml` | El despliegue real, detrás de Coolify, con base externa. |
| `docker-compose.pruebas.yml` | Probarlo entero en un servidor: aplicación **y** base. |
| `entrypoint.sh` | Lo que ocurre al arrancar el contenedor. |

---

## Probar en el servidor

El de producción no arranca a solas: da por hecho una base externa y una red de
Coolify ya creada. Para probar se usa el otro.

El repositorio es **privado**, así que por HTTPS el clon pide credenciales. Con
una llave SSH ya cargada en el servidor:

```bash
git clone git@github.com:cristianyesidmquiroga-tech/porteria-2.git
cd porteria-2
cp config/.env.example config/.env
```

Si el servidor todavía no tiene llave, ver «Repositorio privado» al final.

En `config/.env` basta con rellenar lo que la aplicación exige para arrancar:

```
SECRET_KEY=          # python -c "import secrets; print(secrets.token_hex(32))"
ADMIN_EMAIL=
ADMIN_PASSWORD=      # mínimo 12 caracteres
ADMIN_DOCUMENTO=999999999
```

`DATABASE_URL` **no** hay que tocarla: el Compose de pruebas la sobrescribe
para apuntar a su propia base. Es lo que evita tocar la base real por error.

```bash
docker compose -f docker/docker-compose.pruebas.yml --project-directory . \
    up -d --build
```

Y ya: `http://IP_DEL_SERVIDOR:5000`

```bash
docker compose -f docker/docker-compose.pruebas.yml --project-directory . logs -f web
docker compose -f docker/docker-compose.pruebas.yml --project-directory . down
docker compose -f docker/docker-compose.pruebas.yml --project-directory . down -v   # borra también los datos
```

> Esto **no** es producción: publica el puerto sin https delante, la contraseña
> de la base es fija y las cookies van sin `Secure`. Sirve para ver si
> funciona, no para dejarlo abierto.

---

## El `--project-directory .`

No es un adorno. Compose resuelve las rutas de `build` contra el directorio del
proyecto, que por omisión es **la carpeta del archivo**. Como aquí el contexto
es la raíz del repositorio (`context: .` con `dockerfile: docker/Dockerfile`),
sin ese parámetro Compose buscaría el Dockerfile en `docker/docker/` y no lo
encontraría.

Coolify ya usa la raíz del repositorio como directorio de proyecto, así que
allí no hay que añadir nada.

---

## Decisiones que conviene no deshacer

**Un solo worker de gunicorn.** El planificador (APScheduler) vive dentro del
proceso de la aplicación. Con dos workers habría dos planificadores iguales: el
cierre nocturno registraría salidas duplicadas y el respaldo mensual escribiría
el mismo `.xlsx` desde dos procesos **antes** de borrar las filas de la base.
La concurrencia sale de los hilos (`GUNICORN_THREADS`), no de los procesos.

Para escalar a varios procesos hay que sacar antes el planificador a su propio
contenedor y poner `EJECUTAR_TAREAS=false` en los procesos web.

**Los volúmenes no son opcionales.** Las fotos de perfil y los respaldos viven
en volúmenes con nombre. Sin ellos:

- las fotos quedan en el disco efímero del contenedor y el siguiente
  redespliegue las borra todas, sin copia posible —el respaldo mensual exporta
  accesos y asistencias, no imágenes—;
- el respaldo mensual borra las filas de la base **después** de exportarlas, así
  que perder el archivo es perder los datos.

**Las carpetas de datos se crean en el `Dockerfile`, con su dueño.** Al montar
un volumen con nombre sobre una carpeta que ya existe en la imagen, Docker
copia su contenido y sus permisos. Si la carpeta no existiera, el volumen
nacería propiedad de `root` y `appuser` no podría escribir: subir una foto
fallaría, y fallaría en silencio.

**El contenedor no corre como root.** Acota lo que puede hacer una ejecución de
código arbitrario si algún día la hay.

**El arranque espera a la base.** Sin esa espera el contenedor entra en ciclo de
reinicio siempre que la base tarde un poco más en levantar, y el síntoma —un
contenedor reiniciándose— no dice en ninguna parte que la causa es una carrera.

---

## Qué se cambió, y por qué

- **Los volúmenes decían `datos/fotos_perfil:/app/...`**, una ruta relativa sin
  `./`. Compose no la admite como volumen con nombre —esos no pueden llevar
  barras— ni queda claro que sea una ruta del disco del servidor. Pasan a ser
  volúmenes con nombre.
- **`/app/datos/fotos_perfil` no se creaba en la imagen**, aunque `CARPETA_FOTOS`
  apuntara ahí. Ahora se crea con su dueño.
- **La imagen pasa a dos etapas** y el código se copia con `--chown`: antes un
  `chown -R` posterior duplicaba el árbol entero en otra capa.
- **Se quita `curl`**, que estaba solo para la sonda de salud. La hace Python,
  que ya está en la imagen.
- **`--forwarded-allow-ips` deja de ser `*`.** Con `*`, cualquiera que alcance
  el puerto sin pasar por el proxy falsea su IP de origen y se salta los
  límites por IP. Es el mismo agujero que `config/.env.example` advierte para
  `PROXIES_CONFIABLES`. Por omisión se confía en la red privada de Docker.
- **Registro con tope de tamaño.** Sin él crece hasta llenar el disco del
  servidor y se lleva por delante todo lo demás que corra ahí.
- **`.dockerignore` más estricto**: fuera las pruebas, la documentación y
  cualquier `.env`. Un secreto copiado a una imagen se queda en su capa para
  siempre, aunque una capa posterior lo borre.

---

## Repositorio privado

El repositorio es privado, así que ni Coolify ni el servidor pueden clonarlo
sin credenciales. Hay dos formas, y conviene saber cuál se está usando.

### La llave que Coolify trae de fábrica NO sirve para esto

En *Keys & Tokens → Private keys* aparece `localhost's key`, descrita como «la
llave privada de la máquina anfitriona de Coolify». Esa es la que Coolify usa
para hablar con **su propio servidor**, no con GitHub. Añadirla como llave de
despliegue del repositorio no es lo previsto y mezcla dos cosas que conviene
tener separadas: si algún día se revoca el acceso al repositorio, no debería
quedarse Coolify sin poder administrar su propia máquina.

### Opción A — Aplicación de GitHub (la que recomienda Coolify)

*Sources → + Add → GitHub App*. Coolify guía la instalación y queda con acceso
a los repositorios que se le indiquen.

Ventajas sobre una llave de despliegue: los permisos se pueden acotar y
revocar por repositorio desde GitHub, se renueva sola, y habilita el
despliegue automático al empujar sin configurar nada más.

### Opción B — Llave de despliegue

1. En Coolify: *Keys & Tokens → Private keys → + New private key*. Se genera
   una nueva; **no** se reutiliza `localhost's key`.
2. Copiar la parte **pública** que muestra Coolify.
3. En GitHub: *Settings → Deploy keys → Add deploy key* del repositorio,
   pegar ahí la pública. **Sin** marcar «Allow write access»: el despliegue
   solo necesita leer, y una llave de solo lectura que se filtre no permite
   reescribir el repositorio.
4. En el recurso de Coolify, elegir esa llave y usar la dirección **SSH**
   (`git@github.com:usuario/repo.git`). Con la de HTTPS la llave no se usa y
   el clon falla igual.

Una llave de despliegue vale para **un** repositorio. Si mañana hay un segundo
proyecto, hace falta otra: reutilizar la misma en varios repositorios convierte
una filtración en un problema múltiple.

### Para clonar a mano en el servidor

Con la llave ya en `~/.ssh` del servidor:

```bash
ssh -T git@github.com          # debe saludar por el nombre de usuario
git clone git@github.com:cristianyesidmquiroga-tech/porteria-2.git
```

Si responde `Permission denied (publickey)`, la llave no está cargada o la
pública no está registrada en el repositorio.

> Ser privado **no** cambia nada del despliegue en sí: los volúmenes, la
> imagen y los dos Compose funcionan igual. Solo cambia cómo se obtiene el
> código.
