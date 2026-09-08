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

```bash
git clone https://github.com/cristianyesidmquiroga-tech/porteria-2.git
cd porteria-2
cp config/.env.example config/.env
```

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
