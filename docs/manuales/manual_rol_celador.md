# Manual por Rol — Celador / Portería

Para el personal de vigilancia: **rol Usuario + cargo Celador**. "Celador" es
un cargo, no un rol del sistema.

## Qué puede hacer

- **Panel General**: KPIs, gráfica de la semana, historial reciente y
  exportación CSV → `manual_control_acceso.md`.
- **Escáner**: leer el código de barras del carnet (o buscar por documento) y
  registrar entradas y salidas con los equipos que trae cada persona.
- **Pases Manuales**: registrar visitantes, vehículos y objetos externos y
  marcarles movimientos. Recuerde: **no tienen vigencia ni vencimiento**; a
  medianoche el sistema los desactiva solo.
- **Incidentes**: dejar constancia de anomalías (equipo no registrado,
  persona sin identificar) desde el escáner.
- **Historial de Ingresos**: consultar entradas/salidas de cualquier persona
  del mes en curso → `manual_historial_ingresos.md`.
- Su propio perfil y su carnet, mensajes y centro de ayuda.

## Qué NO puede hacer

- **Registrar equipos propios** (restricción del sistema para el cargo
  Celador).
- Crear o editar usuarios, aprobar fotos, pasar asistencia, ver la auditoría
  o los respaldos (todo eso es de otros roles — ver `matriz_permisos.md`).

## Particularidades de su cuenta

- **Turno automático:** al iniciar sesión se abre su turno del día; el cierre
  de medianoche lo finaliza. No tiene que abrirlo ni cerrarlo a mano.
- **Sesión extendida:** su sesión dura hasta 12 horas de trabajo continuo (a
  los demás usuarios se les cierra a los 10 minutos de inactividad), pero es
  **sesión única**: si alguien entra con su cuenta en otro equipo, la suya se
  cierra. No comparta credenciales: cada movimiento queda registrado con el
  nombre del operador que lo hizo.

## Reglas de oro en la puerta

1. **Compare la foto con la persona.** El escáner le dice si la foto está
   aprobada; una foto sin aprobar no confirma identidad — pida el documento
   físico.
2. **Solo salen los equipos registrados.** Si alguien lleva un equipo que no
   está en su lista, registre el incidente.
3. **El sistema no deja registrar dos entradas seguidas** ni salidas sin
   entrada: si le pasa, no es un error suyo; quedó una inconsistencia
   registrada en auditoría. Repórtelo si la situación es real.
4. **Visitantes con más de 2 horas adentro** aparecen resaltados al
   verificarlos.
5. Si el sistema se cae, lleve registro manual y repórtelo; los accesos no se
   pueden cargar después con fecha retroactiva.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
