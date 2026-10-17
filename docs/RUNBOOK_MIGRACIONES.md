# Runbook de migraciones (PostgreSQL + Flask-Migrate)

RPO: 0 (dump justo antes del upgrade).
RTO medido en laboratorio local: menos de 1 segundo.

## Orden a seguir

1. Preflight: `flask db current`, `flask db heads`, `flask db check`, `flask db upgrade --sql > preflight.sql`.
2. Revisar `preflight.sql`: sin `DROP COLUMN` inesperado, `CONCURRENTLY` fuera de transacción.
3. Dump: `docker exec <contenedor> pg_dump -U postgres -Fc -d porteria -f /tmp/porteria.dump` + `docker cp`.
4. Probar la restauración en una base aparte (`createdb` + `pg_restore`), medir el tiempo.
5. Activar `MODO_MANTENIMIENTO` si el cambio no es transparente.
6. `flask db upgrade`.
7. Verificar: `flask db current`, consultas de humo sobre las tablas tocadas.
8. Anotar el punto de parada (revisión anterior al upgrade). Si algo falla: `flask db downgrade <id>` o restaurar el dump.

## Primera vez en producción

Las tablas ya existen, así que el baseline **no** se aplica con `upgrade`: se hace
`flask db stamp <id_baseline>` y luego `upgrade` del resto.

Producción tiene los nombres de constraint por defecto de PostgreSQL (`usuarios_pkey`),
no los de la convención (`pk_usuarios`). Antes del `stamp`:

1. Restaurar un dump de producción en un contenedor local.
2. `flask db stamp <id_baseline>` + `flask db check`.
3. Si hay diferencias, crear una revisión que renombre los constraints.
4. Borrar ese dump al terminar (Ley 1581 de 2012).
